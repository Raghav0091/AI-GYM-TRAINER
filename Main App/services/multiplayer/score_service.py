from services.persistence.exercise_repository import get_connection


def calculate_room_score(exercise_name, reps, sets_completed, hold_seconds, form_score):
    if exercise_name == "Plank":
        return int(max(0, hold_seconds) * 5 + max(0, sets_completed) * 100 + max(0, form_score))

    return int(max(0, reps) * 10 + max(0, sets_completed) * 50 + max(0, form_score))


def upsert_room_score(room, user_id, username, metrics, status="active"):
    conn = get_connection()
    exercise_name = room["exercise_name"]
    reps = int(metrics.get("reps", 0) or 0)
    sets_completed = int(metrics.get("sets_completed", 0) or 0)
    hold_seconds = float(metrics.get("hold_seconds", 0) or 0)
    form_score = int(metrics.get("form_score", 0) or 0)
    workout_score = calculate_room_score(exercise_name, reps, sets_completed, hold_seconds, form_score)

    with conn:
        conn.execute(
            """
            INSERT INTO room_scores
                (room_id, user_id, username, exercise_name, reps, sets_completed, hold_seconds,
                 form_score, workout_score, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(room_id, user_id)
            DO UPDATE SET
                reps = excluded.reps,
                sets_completed = excluded.sets_completed,
                hold_seconds = excluded.hold_seconds,
                form_score = excluded.form_score,
                workout_score = excluded.workout_score,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                room["id"],
                user_id,
                username,
                exercise_name,
                reps,
                sets_completed,
                hold_seconds,
                form_score,
                workout_score,
                status,
            ),
        )

    return workout_score


def should_update_room_score(previous, metrics, exercise_name, now_ts):
    if previous is None:
        return True

    if metrics.get("reps", 0) != previous.get("reps", 0):
        return True

    if metrics.get("sets_completed", 0) != previous.get("sets_completed", 0):
        return True

    if abs(metrics.get("form_score", 0) - previous.get("form_score", 0)) >= 5:
        return True

    if exercise_name == "Plank" and now_ts - previous.get("updated_at", 0) >= 4:
        return True

    return False
