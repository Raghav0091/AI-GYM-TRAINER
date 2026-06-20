from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.schemas.room_schema import ScoreUpdate


router = APIRouter(prefix="/ws", tags=["websocket"])


class RoomConnectionManager:
    def __init__(self):
        self.active_rooms: dict[str, list[WebSocket]] = defaultdict(list)
        self.room_scores: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)

    async def connect(self, room_code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_rooms[room_code].append(websocket)

    def disconnect(self, room_code: str, websocket: WebSocket) -> None:
        if websocket in self.active_rooms[room_code]:
            self.active_rooms[room_code].remove(websocket)

        if not self.active_rooms[room_code]:
            self.active_rooms.pop(room_code, None)

    async def broadcast(self, room_code: str, message: dict[str, Any]) -> None:
        stale_connections = []

        for websocket in self.active_rooms.get(room_code, []):
            try:
                await websocket.send_json(message)
            except RuntimeError:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            self.disconnect(room_code, websocket)

    def update_score(self, payload: ScoreUpdate) -> list[dict[str, Any]]:
        scores = self.room_scores[payload.room_code]
        scores[payload.user_id] = {
            "user_id": payload.user_id,
            "username": payload.username,
            "reps": payload.reps,
            "sets_completed": payload.sets_completed,
            "hold_seconds": payload.hold_seconds,
            "form_score": payload.form_score,
            "status": payload.status,
        }

        ranked_players = sorted(
            scores.values(),
            key=lambda item: (item["reps"], item["form_score"], item["sets_completed"], item["hold_seconds"]),
            reverse=True,
        )

        return [
            {
                **player,
                "rank": rank,
            }
            for rank, player in enumerate(ranked_players, start=1)
        ]


manager = RoomConnectionManager()


@router.websocket("/rooms/{room_code}")
async def room_socket(websocket: WebSocket, room_code: str):
    clean_room_code = room_code.upper().strip()
    await manager.connect(clean_room_code, websocket)

    try:
        await manager.broadcast(
            clean_room_code,
            {"type": "room_status", "room_code": clean_room_code, "message": "Player connected."},
        )

        while True:
            data = await websocket.receive_json()

            if data.get("type") != "score_update":
                await websocket.send_json({"type": "error", "message": "Unsupported message type."})
                continue

            try:
                payload = ScoreUpdate(**{**data, "room_code": clean_room_code})
            except ValidationError as exc:
                await websocket.send_json({"type": "error", "message": exc.errors()})
                continue

            players = manager.update_score(payload)
            await manager.broadcast(
                clean_room_code,
                {
                    "type": "leaderboard_update",
                    "room_code": clean_room_code,
                    "players": players,
                },
            )
    except WebSocketDisconnect:
        manager.disconnect(clean_room_code, websocket)
        await manager.broadcast(
            clean_room_code,
            {"type": "room_status", "room_code": clean_room_code, "message": "Player disconnected."},
        )


# Scaling note:
# This in-memory manager works for one backend process. For multiple workers or
# multiple servers, publish score updates through Redis Pub/Sub and rebuild
# room presence from Redis or Postgres-backed state.
