from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.room_schema import LeaderboardPlayer, RoomCreate, RoomJoin, RoomResponse
from app.services.leaderboard_service import get_leaderboard
from app.services.room_service import create_room, end_room, get_room_by_code, join_room, start_room


router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/create", response_model=RoomResponse)
def create(payload: RoomCreate, db: Session = Depends(get_db)):
    return create_room(db, payload)


@router.post("/join/{room_code}", response_model=RoomResponse)
def join(room_code: str, payload: RoomJoin, db: Session = Depends(get_db)):
    return join_room(db, room_code, payload)


@router.post("/{room_code}/start", response_model=RoomResponse)
def start(room_code: str, db: Session = Depends(get_db)):
    return start_room(db, room_code)


@router.post("/{room_code}/end", response_model=RoomResponse)
def end(room_code: str, db: Session = Depends(get_db)):
    return end_room(db, room_code)


@router.get("/{room_code}", response_model=RoomResponse)
def get_room(room_code: str, db: Session = Depends(get_db)):
    return get_room_by_code(db, room_code)


@router.get("/{room_code}/leaderboard", response_model=list[LeaderboardPlayer])
def leaderboard(room_code: str, db: Session = Depends(get_db)):
    room = get_room_by_code(db, room_code)
    return get_leaderboard(db, room)
