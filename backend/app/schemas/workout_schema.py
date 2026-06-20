from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkoutCreate(BaseModel):
    user_id: int
    exercise_name: str
    total_reps: int = Field(default=0, ge=0)
    total_sets: int = Field(default=0, ge=0)
    hold_seconds: int = Field(default=0, ge=0)
    duration_seconds: int = Field(default=0, ge=0)
    average_form_score: int = Field(default=0, ge=0, le=100)
    xp_earned: int = Field(default=0, ge=0)


class WorkoutResponse(WorkoutCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class WorkoutSummary(BaseModel):
    user_id: int
    total_workouts: int
    total_reps: int
    total_sets: int
    total_hold_seconds: int
    average_form_score: float
    total_xp: int
