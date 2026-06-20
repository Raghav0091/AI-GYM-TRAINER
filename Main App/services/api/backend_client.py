import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_BACKEND_URL = "http://localhost:8000"


def backend_base_url():
    return os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")


def backend_health_check(timeout=1.5):
    return _request("GET", "/health", timeout=timeout)


def register_user_api(username, password):
    return _request("POST", "/auth/register", {"username": username, "password": password})


def login_user_api(username, password):
    return _request("POST", "/auth/login", {"username": username, "password": password})


def create_room_api(payload):
    return _request("POST", "/rooms/create", payload)


def join_room_api(room_code, user_id, username):
    return _request("POST", f"/rooms/join/{room_code}", {"user_id": user_id, "username": username})


def save_workout_api(payload):
    return _request("POST", "/workouts", payload)


def get_leaderboard_api(room_code):
    return _request("GET", f"/rooms/{room_code}/leaderboard")


def _request(method, path, payload=None, timeout=5):
    body = None
    headers = {"Content-Type": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    request = Request(f"{backend_base_url()}{path}", data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "data": json.loads(response_body) if response_body else None,
                "error": None,
            }
    except URLError as exc:
        return {"ok": False, "status_code": None, "data": None, "error": str(exc.reason)}
    except Exception as exc:
        return {"ok": False, "status_code": None, "data": None, "error": str(exc)}
