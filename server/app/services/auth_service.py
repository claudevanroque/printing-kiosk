from datetime import datetime, timezone

import jwt

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    decode_token,
    verify_password,
    hash_refresh_token,
    get_refresh_token_expiration,
)


from app.repositories import (
    user_repository,
    refresh_token_repository,
)

def login(db: Session, *, email: str, password: str, device_id: str):
    email = email.strip().lower()

    user = user_repository.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password",
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="User account is inactive",
        )

    access_token = create_access_token(user_id=user.id)

    refresh_token = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    expires_at = get_refresh_token_expiration()
    now = datetime.now(timezone.utc)

    existing_refresh_token = refresh_token_repository.get_by_user_and_device(
        db,
        user_id=user.id,
        device_id=device_id,
    )

    if existing_refresh_token is None:
        refresh_token_repository.create(
            db,
            user_id=user.id,
            device_id=device_id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            created_at=now,
            is_revoked=False,
        )
    else:
        refresh_token_repository.update(
            db,
            refresh_token=existing_refresh_token,
            token_hash=refresh_hash,
            expires_at=expires_at,
            is_revoked=False,
        )

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh(db: Session, *, refresh_token: str):
    stored_token = refresh_token_repository.get_by_token(db, refresh_token)

    if not stored_token or stored_token.is_revoked:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    if stored_token.expires_at <= datetime.now(timezone.utc):
        refresh_token_repository.revoke(db, stored_token)
        raise HTTPException(
            status_code=401,
            detail="Refresh token has expired",
        )

    user = user_repository.get_by_id(db, user_id=stored_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User is unavailable",
        )

    refresh_token_repository.revoke(db, stored_token)

    access_token = create_access_token(user_id=user.id)
    new_refresh_token = generate_refresh_token()
    new_token_hash = hash_refresh_token(new_refresh_token)
    new_expires_at = get_refresh_token_expiration()

    refresh_token_repository.create(
        db,
        user_id=user.id,
        device_id=stored_token.device_id,
        token_hash=new_token_hash,
        expires_at=new_expires_at,
        created_at=datetime.now(timezone.utc),
        is_revoked=False,
    )
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


def logout(db: Session, *, refresh_token: str):
    stored_token = refresh_token_repository.get_by_token(db, refresh_token)

    if stored_token and not stored_token.is_revoked:
        refresh_token_repository.revoke(db, stored_token)
        db.commit()

    return {
        "detail": "Successfully logged out",
    }