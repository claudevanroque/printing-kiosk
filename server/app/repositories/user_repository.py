from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

def get_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)

def get_by_id(db: Session, user_id: UUID) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.scalar(stmt)

def create(db: Session, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    return user
