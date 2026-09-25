import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User

def create_platform_admin():
    db = SessionLocal()
    try:
        print("\n=== Create Platform Administrator ===\n")

        existing_admin = db.scalar(
            select(User).where(
                User.is_platform_admin == True
            )
        )

        if existing_admin:
            print("\nA platform administrator already exists.")
            print(f"Email: {existing_admin.email}")
            return

        email = input("Email: ").strip().lower()

        existing_user = db.scalar(
            select(User).where(
                User.email == email
            )
        )

        if existing_user:
            print("\nA user with this email already exists.")
            return

        password = getpass.getpass(
            "Password: "
        )

        confirm_password = getpass.getpass(
            "Confirm password: "
        )

        if password != confirm_password:
            print("\nPasswords do not match.")
            return

        if len(password) < 8:
            print(
                "\nPassword must contain at least 8 characters."
            )
            return

        admin = User(
            email=email,
            hashed_password=hash_password(
                password
            ),
            is_platform_admin=True,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\nPlatform administrator created successfully.")
        print(f"ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(
            f"Platform Admin: {admin.is_platform_admin}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_platform_admin()