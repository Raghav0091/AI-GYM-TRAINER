from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.workout_schema import WorkoutCreate, WorkoutResponse, WorkoutSummary
from app.services.workout_service import create_workout, get_workout_summary, is_valid_workout, list_workouts


router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create(payload: WorkoutCreate, db: Session = Depends(get_db)):
    if not is_valid_workout(payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workout. No valid reps, sets, or hold time detected.",
        )

    return create_workout(db, payload)


@router.get("/{user_id}", response_model=list[WorkoutResponse])
def by_user(user_id: int, db: Session = Depends(get_db)):
    return list_workouts(db, user_id)


@router.get("/{user_id}/summary", response_model=WorkoutSummary)
def summary(user_id: int, db: Session = Depends(get_db)):
    return get_workout_summary(db, user_id)
