# Future Production Architecture

AI Gym Coach currently keeps the Streamlit app as the working frontend and adds a FastAPI backend foundation beside it. The next production step is to place a reverse proxy in front of both services.

## Suggested Gateway Routing

```text
https://your-domain.com/       -> Streamlit frontend
https://your-domain.com/api/*  -> FastAPI REST backend
https://your-domain.com/ws/*   -> FastAPI WebSocket backend
```

## Why Use NGINX, Caddy, or Cloudflare Tunnel?

- HTTPS termination: browser camera APIs require HTTPS outside localhost.
- Reverse proxy: one public domain can route traffic to Streamlit and FastAPI.
- Load balancing: future backend replicas can share traffic.
- WebSocket upgrade handling: `/ws/*` traffic can stay connected to the room service.
- Cleaner deployment: frontend, backend, database, and cache can run as separate services.

## Future Service Layout

```text
Browser
  |
HTTPS
  |
NGINX / Caddy / Cloudflare Tunnel
  |-------------------> Streamlit frontend
  |-------------------> FastAPI REST API
  |-------------------> FastAPI WebSocket rooms
                          |
                          |---- PostgreSQL: users, workouts, rooms, scores
                          |---- Redis: live room state, cooldowns, pub/sub
```

## Scaling WebSockets

The current backend WebSocket manager stores connected clients in memory. That is fine for one backend process. For multiple backend workers or multiple servers, publish room score messages through Redis Pub/Sub so every worker can broadcast the same leaderboard state to its connected clients.

## Load Balancer Notes

A load balancer receives user traffic and forwards it to healthy app instances. For this project, it can later:

- keep HTTPS certificates in one place,
- route `/api` requests to backend containers,
- route `/ws` WebSocket connections to the realtime service,
- keep the Streamlit UI separate from backend compute,
- support multiple backend containers when traffic grows.
