from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.workout import WorkoutSession
from app.schemas.workout_schema import WorkoutCreate


def is_valid_workout(workout: WorkoutCreate) -> bool:
    if workout.exercise_name.lower() == "plank":
        return workout.hold_seconds >= 10 or workout.total_sets > 0

    return workout.total_reps > 0 or workout.total_sets > 0


def create_workout(db: Session, workout: WorkoutCreate) -> WorkoutSession:
    row = WorkoutSession(**workout.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_workouts(db: Session, user_id: int) -> list[WorkoutSession]:
    return list(
        db.scalars(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user_id)
            .order_by(WorkoutSession.created_at.desc())
        )
    )


def get_workout_summary(db: Session, user_id: int) -> dict:
    row = db.execute(
        select(
            func.count(WorkoutSession.id),
            func.coalesce(func.sum(WorkoutSession.total_reps), 0),
            func.coalesce(func.sum(WorkoutSession.total_sets), 0),
            func.coalesce(func.sum(WorkoutSession.hold_seconds), 0),
            func.coalesce(func.avg(WorkoutSession.average_form_score), 0),
            func.coalesce(func.sum(WorkoutSession.xp_earned), 0),
        ).where(WorkoutSession.user_id == user_id)
    ).one()

    return {
        "user_id": user_id,
        "total_workouts": row[0],
        "total_reps": row[1],
        "total_sets": row[2],
        "total_hold_seconds": row[3],
        "average_form_score": round(float(row[4]), 1),
        "total_xp": row[5],
    }
