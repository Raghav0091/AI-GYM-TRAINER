# AI Gym Coach Architecture Explained

This project is growing from a Streamlit prototype into a production-style fitness platform. Here are the main engineering pieces in plain language.

## Frontend

The frontend is what the user sees and clicks. In this project, the frontend is the Streamlit app in `Main App/main.py`.

It shows login/register, workout controls, camera panels, form score, voice feedback, dashboard, history, and Fitness Arena screens.

## Backend

The backend is the server that stores data, checks passwords, manages rooms, and sends real-time updates. The new backend lives in `backend/app`.

Streamlit can keep working locally while the backend grows in parallel.

## API

An API is a set of URLs that the frontend can call. Example:

```text
GET /health
POST /auth/login
POST /rooms/create
GET /rooms/GYM-742/leaderboard
```

The frontend sends data to the API and receives structured JSON responses.

## Database

A database stores long-term data. The current app uses SQLite locally. SQLite is simple and beginner-friendly, but it is not ideal for real multiplayer because every user would need access to the same local file.

PostgreSQL is better for production because it can handle many users, concurrent writes, indexes, backups, and hosted deployment.

## Cache

A cache stores short-lived data very quickly. Redis is a common cache.

For AI Fitness Arena, Redis can later store:

- live leaderboard state,
- active room users,
- voice feedback cooldowns,
- rate limits,
- WebSocket Pub/Sub messages.

## WebSocket

Normal API calls ask a question and get one response. WebSockets stay open.

That matters for Fitness Arena because users need live leaderboard updates without constantly refreshing the page.

Example:

1. Raghav does 20 reps.
2. Browser sends a WebSocket score update.
3. Backend broadcasts a new leaderboard to everyone in the room.

## Load Balancer

A load balancer receives public traffic and sends it to the right service. In the future:

```text
/       -> Streamlit frontend
/api/*  -> FastAPI backend
/ws/*   -> WebSocket room backend
```

NGINX, Caddy, Cloudflare Tunnel, or a cloud load balancer can do this.

## Microservice

A microservice is a focused app that does one job. This project may later split into:

- Streamlit or React frontend,
- FastAPI API service,
- WebSocket room service,
- AI coaching service,
- database and cache services.

For now, one FastAPI backend is enough.

## Docker

Docker packages software so it runs the same way on different machines.

`docker-compose.yml` starts:

- FastAPI backend,
- PostgreSQL database,
- Redis cache.

## Why HTTPS Is Needed For Camera

Browsers protect camera access. Camera APIs work on:

- `http://localhost:8501`
- `https://your-domain.com`

Camera APIs often fail on:

- `http://192.168.x.x:8501`
- plain HTTP remote URLs

The error usually looks like:

```text
navigator.mediaDevices is undefined
The current document is not loaded securely
```

This is a browser security rule, not a bug in MediaPipe. For phone or multi-device testing, use HTTPS through Streamlit Cloud, Caddy, NGINX, Cloudflare Tunnel, or another secure deployment.

## Why PostgreSQL + Redis + WebSocket Is Better For Multiplayer

SQLite is great for local history, but real multiplayer needs shared services:

- PostgreSQL stores users, workouts, rooms, members, and scores.
- Redis keeps live room state fast.
- WebSockets broadcast updates instantly.
- HTTPS lets browser camera access work on real devices.
