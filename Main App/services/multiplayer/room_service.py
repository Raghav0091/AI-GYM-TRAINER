import random

from services.persistence.exercise_repository import get_connection


def generate_room_code():
    conn = get_connection()

    for _ in range(100):
        code = f"GYM-{random.randint(100, 999)}"
        existing = conn.execute("SELECT id FROM workout_rooms WHERE room_code = ?", (code,)).fetchone()

        if existing is None:
            return code

    return f"GYM-{random.randint(1000, 9999)}"


def create_room(user_id, username, room_name, exercise_name, target_reps, target_sets, target_hold_seconds, game_mode):
    conn = get_connection()
    room_code = generate_room_code()

    with conn:
        cursor = conn.execute(
            """
            INSERT INTO workout_rooms
                (room_code, room_name, host_user_id, exercise_name, target_reps,
                 target_sets, target_hold_seconds, game_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (room_code, room_name, user_id, exercise_name, target_reps, target_sets, target_hold_seconds, game_mode),
        )
        room_id = cursor.lastrowid

    join_room_by_id(room_id, user_id, username, is_host=True)
    add_room_event(room_id, user_id, "room_created", f"{username} created the room.")
    return get_room(room_id)


def get_room(room_id):
    row = get_connection().execute("SELECT * FROM workout_rooms WHERE id = ?", (room_id,)).fetchone()
    return dict(row) if row else None


def get_room_by_code(room_code):
    clean_code = (room_code or "").strip().upper()
    row = get_connection().execute("SELECT * FROM workout_rooms WHERE room_code = ?", (clean_code,)).fetchone()
    return dict(row) if row else None


def join_room(room_code, user_id, username):
    room = get_room_by_code(room_code)

    if room is None:
        return None, "Room not found. Check the code and try again."

    if room["status"] == "completed":
        return None, "This room has already ended."

    join_room_by_id(room["id"], user_id, username, is_host=room["host_user_id"] == user_id)
    add_room_event(room["id"], user_id, "user_joined", f"{username} joined the room.")
    return get_room(room["id"]), None


def join_room_by_id(room_id, user_id, username, is_host=False):
    room = get_room(room_id)
    conn = get_connection()

    with conn:
        conn.execute(
            """
            INSERT INTO room_members (room_id, user_id, username, is_host, status)
            VALUES (?, ?, ?, ?, 'joined')
            ON CONFLICT(room_id, user_id)
            DO UPDATE SET username = excluded.username, status = 'joined'
            """,
            (room_id, user_id, username, int(is_host)),
        )
        conn.execute(
            """
            INSERT INTO room_scores (room_id, user_id, username, exercise_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(room_id, user_id)
            DO UPDATE SET username = excluded.username
            """,
            (room_id, user_id, username, room["exercise_name"]),
        )


def get_room_members(room_id):
    rows = get_connection().execute(
        """
        SELECT * FROM room_members
        WHERE room_id = ?
        ORDER BY is_host DESC, joined_at ASC
        """,
        (room_id,),
    ).fetchall()

    return [dict(row) for row in rows]


def add_room_event(room_id, user_id, event_type, message):
    conn = get_connection()

    with conn:
        conn.execute(
            """
            INSERT INTO room_events (room_id, user_id, event_type, message)
            VALUES (?, ?, ?, ?)
            """,
            (room_id, user_id, event_type, message),
        )


def get_room_events(room_id, limit=12):
    rows = get_connection().execute(
        """
        SELECT * FROM room_events
        WHERE room_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (room_id, limit),
    ).fetchall()

    return [dict(row) for row in rows]


def start_room(room_id, user_id):
    room = get_room(room_id)

    if not room or room["host_user_id"] != user_id:
        return False

    conn = get_connection()

    with conn:
        conn.execute(
            "UPDATE workout_rooms SET status = 'active', started_at = CURRENT_TIMESTAMP WHERE id = ?",
            (room_id,),
        )

    add_room_event(room_id, user_id, "room_started", "Host started the workout.")
    return True


def end_room(room_id, user_id):
    room = get_room(room_id)

    if not room or room["host_user_id"] != user_id:
        return False

    conn = get_connection()

    with conn:
        conn.execute(
            "UPDATE workout_rooms SET status = 'completed', ended_at = CURRENT_TIMESTAMP WHERE id = ?",
            (room_id,),
        )

    add_room_event(room_id, user_id, "room_ended", "Room ended.")
    return True


def maybe_mark_race_winner(room, user_id, username, metrics):
    if not room or room["game_mode"] != "Race" or room["status"] != "active" or room["winner_user_id"]:
        return False

    reached_target = False

    if room["exercise_name"] == "Plank":
        reached_target = metrics.get("hold_seconds", 0) >= room["target_hold_seconds"]
    else:
        reached_target = metrics.get("reps", 0) >= room["target_reps"]

    if not reached_target:
        return False

    conn = get_connection()

    with conn:
        conn.execute(
            "UPDATE workout_rooms SET winner_user_id = ?, status = 'completed', ended_at = CURRENT_TIMESTAMP WHERE id = ? AND winner_user_id IS NULL",
            (user_id, room["id"]),
        )

    add_room_event(room["id"], user_id, "winner_declared", f"{username} won the race!")
    return True
