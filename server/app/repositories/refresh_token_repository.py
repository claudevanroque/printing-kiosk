from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.core import security

def create(
    db: Session,
    user_id: UUID,
    device_id: str,
    token_hash: str,
    expires_at: datetime,
    created_at: datetime,
    is_revoked: bool | None = None,
) -> RefreshToken:
    refresh_session = RefreshToken(
        user_id=user_id,
        device_id=device_id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=created_at,
        is_revoked=is_revoked,
    )

    db.add(refresh_session)
    db.flush()

    return refresh_session

def update(
    db: Session,
    refresh_token: RefreshToken,
    token_hash: str,
    expires_at: datetime,
    is_revoked: bool = False,
) -> RefreshToken:
    refresh_token.token_hash = token_hash
    refresh_token.expires_at = expires_at
    refresh_token.is_revoked = is_revoked

    db.flush()

    return refresh_token

def rotate(
    db: Session,
    refresh_token: RefreshToken,
    new_token_hash: str,
) -> RefreshToken:
    refresh_token.token_hash = new_token_hash
    db.flush()

    return refresh_token

def get_by_token(db: Session, refresh_token: str,) -> RefreshToken | None:

    token_hash = security.hash_refresh_token(
        refresh_token
    )

    statement = select(
        RefreshToken
    ).where(
        RefreshToken.token_hash == token_hash
    )

    return db.scalar(statement)

def get_by_user_and_device(db: Session, user_id: UUID, device_id: str) -> RefreshToken | None:
    statement = select(
        RefreshToken
    ).where(
        RefreshToken.user_id == user_id,
        RefreshToken.device_id == device_id
    )

    return db.scalar(statement)

def revoke(db: Session, refresh_token: RefreshToken) -> RefreshToken:
    refresh_token.is_revoked = True
    db.flush()

    return refresh_token


# def create(db: Session, *, user_id: UUID, token_jti: str, expires_at: datetime) -> RefreshToken:
#     refresh_token = RefreshToken(user_id=user_id, token_jti=token_jti, expires_at=expires_at)
#     db.add(refresh_token)
#     return refresh_token

# def get_by_jti(db: Session, token_jti: str) -> RefreshToken | None:
#     stmt = select(RefreshToken).where(RefreshToken.token_jti == token_jti)
#     return db.scalar(stmt)

# def revoke(db: Session, token: RefreshToken) -> None:
#     token.revoked = True