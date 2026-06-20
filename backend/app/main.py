from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers import auth, rooms, users, websocket, workouts


app = FastAPI(title="AI Fitness Arena Backend", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    try:
        init_db()
    except Exception as exc:
        # Keep /health available even if Postgres is still booting or not started
        # during local development. Database-backed routes will still report
        # connection errors until DATABASE_URL points to a running database.
        print(f"Database initialization skipped: {exc}")


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.service_name}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(workouts.router)
app.include_router(rooms.router)
app.include_router(websocket.router)
