
import asyncio
import secrets
import sys

from winrt.windows.networking.connectivity import (
    NetworkInformation,
)
from winrt.windows.networking.networkoperators import (
    NetworkOperatorTetheringManager,
    TetheringOperationalState,
    TetheringOperationStatus,
)

from app.core import network


# No 0/O, 1/l/I so the password is easy to read and type.
PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"


class HotspotError(Exception):
    pass


# Credentials of the hotspot this process started, so a repeated start can
# return them instead of reconfiguring a running hotspot.
_active_credentials: dict | None = None


def generate_password(length: int = 12) -> str:
    if not 8 <= length <= 63:
        raise ValueError("WPA2 passwords must be 8-63 characters.")

    return "".join(
        secrets.choice(PASSWORD_ALPHABET) for _ in range(length)
    )


def get_hotspot_manager():
    if sys.platform != "win32":
        raise HotspotError("Windows is required.")

    # Get the Ethernet connection used by the kiosk.
    profiles = NetworkInformation.get_connection_profiles()

    for profile in profiles:
        adapter = profile.network_adapter

        if adapter is None:
            continue

        # IANA interface type 6 = Ethernet.
        if adapter.iana_interface_type != 6:
            continue

        try:
            return (
                NetworkOperatorTetheringManager
                .create_from_connection_profile(profile)
            )
        except Exception:
            continue

    raise HotspotError(
        "Cannot access Windows Mobile Hotspot. "
        "Check Ethernet connection and Windows permissions."
    )


def hotspot_status(manager=None):
    manager = manager or get_hotspot_manager()

    state = manager.tethering_operational_state

    return {
        "state": TetheringOperationalState(state).name,
        "running": state == TetheringOperationalState.ON,
    }


async def _wait_for_hotspot_ip(timeout: float = 10.0) -> None:
    # Windows reports the hotspot as ON before the adapter gets its IP.
    deadline = asyncio.get_running_loop().time() + timeout

    while network.get_hotspot_ip() is None:
        if asyncio.get_running_loop().time() >= deadline:
            raise HotspotError(
                "Hotspot started but its network address is not ready."
            )

        await asyncio.sleep(0.2)


async def start_hotspot():
    global _active_credentials

    manager = get_hotspot_manager()

    status = hotspot_status(manager)

    if status["running"]:
        if _active_credentials is not None:
            await _wait_for_hotspot_ip()

            return {**status, **_active_credentials}

        # Running with a password we don't know: restart to set a known one.
        await stop_hotspot()

    password = generate_password()
    config = manager.get_current_access_point_configuration()
    config.passphrase = password

    try:
        await manager.configure_access_point_async(config)
    except Exception as exc:
        raise HotspotError(
            f"Failed to set hotspot password: {exc}"
        ) from exc

    try:
        result = await manager.start_tethering_async()
    except Exception as exc:
        raise HotspotError(
            f"Failed to start hotspot: {exc}"
        ) from exc

    if result.status != TetheringOperationStatus.SUCCESS:
        raise HotspotError(
            f"Windows rejected hotspot start: {TetheringOperationStatus(result.status).name}"
        )

    _active_credentials = {"ssid": config.ssid, "password": password}

    await _wait_for_hotspot_ip()

    return {**hotspot_status(manager), **_active_credentials}


async def stop_hotspot():
    global _active_credentials

    manager = get_hotspot_manager()

    status = hotspot_status(manager)

    if not status["running"]:
        _active_credentials = None
        return status

    try:
        result = await manager.stop_tethering_async()
    except Exception as exc:
        raise HotspotError(
            f"Failed to stop hotspot: {exc}"
        ) from exc

    if result.status != TetheringOperationStatus.SUCCESS:
        raise HotspotError(
            f"Windows rejected hotspot stop: {TetheringOperationStatus(result.status).name}"
        )

    _active_credentials = None

    return hotspot_status(manager)


async def main():
    if len(sys.argv) != 2:
        print("Usage: python -m app.core.windows_hotspot start|stop|status")
        return

    command = sys.argv[1].lower()

    try:
        if command == "start":
            result = await start_hotspot()
        elif command == "stop":
            result = await stop_hotspot()
        elif command == "status":
            result = hotspot_status()
        else:
            raise HotspotError("Invalid command.")

        print(result)

    except HotspotError as exc:
        print(f"Hotspot error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())