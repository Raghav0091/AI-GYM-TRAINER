from services.persistence.exercise_repository import get_connection


def get_room_leaderboard(room_id, exercise_name):
    conn = get_connection()
    order_clause = (
        "hold_seconds DESC, form_score DESC, workout_score DESC"
        if exercise_name == "Plank"
        else "reps DESC, form_score DESC, sets_completed DESC, workout_score DESC"
    )
    rows = conn.execute(
        f"""
        SELECT username, user_id, reps, sets_completed, hold_seconds, form_score,
               workout_score, status, updated_at
        FROM room_scores
        WHERE room_id = ?
        ORDER BY {order_clause}
        """,
        (room_id,),
    ).fetchall()

    return [dict(row) for row in rows]
