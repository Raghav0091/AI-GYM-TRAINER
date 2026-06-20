from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    room_name: str | None = None
    host_user_id: int
    host_username: str
    exercise_name: str
    target_reps: int = Field(default=0, ge=0)
    target_sets: int = Field(default=1, ge=1)
    target_hold_seconds: int = Field(default=0, ge=0)


class RoomJoin(BaseModel):
    user_id: int
    username: str


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_code: str
    room_name: str | None
    host_user_id: int
    exercise_name: str
    target_reps: int
    target_sets: int
    target_hold_seconds: int
    status: str
    created_at: datetime
    started_at: datetime | None
    ended_at: datetime | None


class ScoreUpdate(BaseModel):
    room_code: str
    user_id: int
    username: str
    reps: int = Field(default=0, ge=0)
    sets_completed: int = Field(default=0, ge=0)
    hold_seconds: float = Field(default=0, ge=0)
    form_score: int = Field(default=0, ge=0, le=100)
    status: str = "active"


class LeaderboardPlayer(BaseModel):
    rank: int
    user_id: int
    username: str
    reps: int
    sets_completed: int
    hold_seconds: float
    form_score: int
    workout_score: int
    status: str
