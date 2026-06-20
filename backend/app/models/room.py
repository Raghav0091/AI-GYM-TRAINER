from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    room_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    host_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    exercise_name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_sets: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    target_hold_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="waiting", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RoomMember(Base):
    __tablename__ = "room_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    is_host: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="joined", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RoomScore(Base):
    __tablename__ = "room_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sets_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hold_seconds: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    form_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    workout_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
