import random
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.room import Room, RoomMember, RoomScore
from app.schemas.room_schema import RoomCreate, RoomJoin, ScoreUpdate
from app.services.leaderboard_service import calculate_workout_score


def generate_room_code(db: Session) -> str:
    for _ in range(20):
        code = f"GYM-{random.randint(100, 999)}"
        existing_room = db.scalar(select(Room).where(Room.room_code == code))

        if not existing_room:
            return code

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate room code.")


def get_room_by_code(db: Session, room_code: str) -> Room:
    room = db.scalar(select(Room).where(Room.room_code == room_code.upper().strip()))

    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")

    return room


def create_room(db: Session, payload: RoomCreate) -> Room:
    room = Room(
        room_code=generate_room_code(db),
        room_name=payload.room_name,
        host_user_id=payload.host_user_id,
        exercise_name=payload.exercise_name,
        target_reps=payload.target_reps,
        target_sets=payload.target_sets,
        target_hold_seconds=payload.target_hold_seconds,
    )
    db.add(room)
    db.flush()
    _add_member(db, room, payload.host_user_id, payload.host_username, is_host=True)
    db.commit()
    db.refresh(room)
    return room


def join_room(db: Session, room_code: str, payload: RoomJoin) -> Room:
    room = get_room_by_code(db, room_code)

    if room.status == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is already completed.")

    _add_member(db, room, payload.user_id, payload.username, is_host=False)
    db.commit()
    db.refresh(room)
    return room


def start_room(db: Session, room_code: str) -> Room:
    room = get_room_by_code(db, room_code)
    room.status = "active"
    room.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(room)
    return room


def end_room(db: Session, room_code: str) -> Room:
    room = get_room_by_code(db, room_code)
    room.status = "completed"
    room.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(room)
    return room


def upsert_score(db: Session, room: Room, payload: ScoreUpdate) -> RoomScore:
    workout_score = calculate_workout_score(
        room,
        payload.reps,
        payload.sets_completed,
        payload.hold_seconds,
        payload.form_score,
    )
    score = db.scalar(
        select(RoomScore).where(
            RoomScore.room_id == room.id,
            RoomScore.user_id == payload.user_id,
        )
    )

    if not score:
        score = RoomScore(room_id=room.id, user_id=payload.user_id, username=payload.username)
        db.add(score)

    score.username = payload.username
    score.reps = payload.reps
    score.sets_completed = payload.sets_completed
    score.hold_seconds = payload.hold_seconds
    score.form_score = payload.form_score
    score.workout_score = workout_score
    score.status = payload.status
    score.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(score)
    return score


def _add_member(db: Session, room: Room, user_id: int, username: str, is_host: bool) -> None:
    existing_member = db.scalar(
        select(RoomMember).where(
            RoomMember.room_id == room.id,
            RoomMember.user_id == user_id,
        )
    )

    if not existing_member:
        db.add(
            RoomMember(
                room_id=room.id,
                user_id=user_id,
                username=username,
                is_host=1 if is_host else 0,
            )
        )

    existing_score = db.scalar(
        select(RoomScore).where(
            RoomScore.room_id == room.id,
            RoomScore.user_id == user_id,
        )
    )

    if not existing_score:
        db.add(RoomScore(room_id=room.id, user_id=user_id, username=username))
