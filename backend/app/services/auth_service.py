from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


def register_user(db: Session, username: str, password: str) -> User:
    existing_user = db.scalar(select(User).where(User.username == username))

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists.")

    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, username: str, password: str) -> str:
    user = db.scalar(select(User).where(User.username == username))

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

    return create_access_token(str(user.id))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
