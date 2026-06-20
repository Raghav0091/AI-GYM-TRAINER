from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.room import Room, RoomScore
from app.schemas.room_schema import LeaderboardPlayer


def calculate_workout_score(room: Room, reps: int, sets_completed: int, hold_seconds: float, form_score: int) -> int:
    if room.exercise_name.lower() == "plank":
        return int(max(0, hold_seconds) * 5 + max(0, sets_completed) * 100 + max(0, form_score))

    return int(max(0, reps) * 10 + max(0, sets_completed) * 50 + max(0, form_score))


def get_leaderboard(db: Session, room: Room) -> list[LeaderboardPlayer]:
    if room.exercise_name.lower() == "plank":
        order_by = (RoomScore.hold_seconds.desc(), RoomScore.form_score.desc())
    else:
        order_by = (RoomScore.reps.desc(), RoomScore.form_score.desc(), RoomScore.sets_completed.desc())

    scores = db.scalars(
        select(RoomScore)
        .where(RoomScore.room_id == room.id)
        .order_by(*order_by)
    ).all()

    return [
        LeaderboardPlayer(
            rank=index,
            user_id=score.user_id,
            username=score.username,
            reps=score.reps,
            sets_completed=score.sets_completed,
            hold_seconds=score.hold_seconds,
            form_score=score.form_score,
            workout_score=score.workout_score,
            status=score.status,
        )
        for index, score in enumerate(scores, start=1)
    ]
