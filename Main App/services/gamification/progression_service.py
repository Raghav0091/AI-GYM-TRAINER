from datetime import date, datetime, timedelta

from services.gamification.achievement_service import evaluate_achievements, seed_achievements
from services.gamification.challenge_service import update_daily_challenge
from services.gamification.scoring_service import (
    calculate_calories_estimate,
    calculate_workout_score,
    calculate_xp,
    level_from_xp,
    level_progress,
)
from services.persistence.exercise_repository import get_connection


def bootstrap_gamification() -> None:
    seed_achievements()


def get_user_progress(user_id: int) -> dict:
    conn = get_connection()

    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO user_progress (user_id) VALUES (?)",
            (user_id,),
        )

    return dict(conn.execute("SELECT * FROM user_progress WHERE user_id = ?", (user_id,)).fetchone())


def get_leaderboard(limit: int = 10, sort_by: str = "total_xp") -> list[dict]:
    allowed_sorts = {
        "total_xp": "up.total_xp",
        "total_reps": "up.total_reps",
        "best_streak": "up.longest_streak",
        "most_workouts": "up.total_workouts",
        "best_form_score": "best_form_score",
    }
    order_column = allowed_sorts.get(sort_by, "up.total_xp")
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT
            u.username,
            up.current_level,
            up.total_xp,
            up.total_reps,
            up.current_streak,
            up.longest_streak,
            up.total_workouts,
            COALESCE(MAX(ws.average_form_score), 0) AS best_form_score
        FROM user_progress up
        JOIN users u ON u.id = up.user_id
        LEFT JOIN workout_sessions ws ON ws.user_id = up.user_id
        GROUP BY up.user_id
        ORDER BY {order_column} DESC, up.total_xp DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return [dict(row) for row in rows]


def get_personal_records(user_id: int) -> list[dict]:
    rows = get_connection().execute(
        """
        SELECT * FROM personal_records
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()

    return [dict(row) for row in rows]


def finalize_workout(user_id: int, workout: dict) -> dict:
    conn = get_connection()
    previous_progress = get_user_progress(user_id)
    streak = _calculate_streak(previous_progress.get("last_workout_date"), previous_progress.get("current_streak", 0))
    streak_bonus = _streak_bonus(streak["current_streak"], streak["increased_today"])
    base_xp = calculate_xp(
        workout["total_reps"],
        workout["total_sets"],
        workout["average_form_score"],
        streak_bonus,
    )
    calories = calculate_calories_estimate(
        workout["exercise_name"],
        workout["total_reps"],
        workout["duration_seconds"],
    )

    with conn:
        cursor = conn.execute(
            """
            INSERT INTO workout_sessions
                (user_id, exercise_name, total_reps, total_sets, duration_seconds,
                 average_form_score, xp_earned, calories_estimate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                workout["exercise_name"],
                workout["total_reps"],
                workout["total_sets"],
                workout["duration_seconds"],
                workout["average_form_score"],
                base_xp,
                calories,
            ),
        )
        session_id = cursor.lastrowid

    challenge_result = update_daily_challenge(user_id, workout)
    progress_before_bonus = _update_progress(
        user_id,
        previous_progress,
        workout,
        base_xp + challenge_result["xp_awarded"],
        streak,
    )
    unlocked = evaluate_achievements(user_id, progress_before_bonus, workout)
    achievement_xp = sum(item["xp_reward"] for item in unlocked)
    progress = _add_bonus_xp(user_id, achievement_xp) if achievement_xp else get_user_progress(user_id)
    total_xp_earned = base_xp + challenge_result["xp_awarded"] + achievement_xp

    with conn:
        conn.execute(
            "UPDATE workout_sessions SET xp_earned = ? WHERE id = ?",
            (total_xp_earned, session_id),
        )

    personal_records = update_personal_records(user_id, workout)

    return {
        "session_id": session_id,
        "workout": workout,
        "base_xp": base_xp,
        "streak_bonus": streak_bonus,
        "challenge": challenge_result,
        "achievements": unlocked,
        "achievement_xp": achievement_xp,
        "personal_records": personal_records,
        "xp_earned": total_xp_earned,
        "calories_estimate": calories,
        "workout_score": calculate_workout_score(
            workout["total_reps"],
            workout["total_sets"],
            workout["average_form_score"],
            workout["duration_seconds"],
        ),
        "progress": progress,
        "level_progress": level_progress(progress["total_xp"]),
    }


def update_personal_records(user_id: int, workout: dict) -> list[dict]:
    records = [
        ("most_reps_workout", workout["total_reps"], "Most reps in one workout"),
        ("best_form_score", workout["average_form_score"], "Highest form score"),
        ("longest_duration", workout["duration_seconds"], "Longest workout duration"),
    ]

    if workout["exercise_name"] == "Plank":
        records.append(("longest_plank_hold", workout["duration_seconds"], "Longest plank hold"))

    conn = get_connection()
    new_records = []

    for record_type, value, label in records:
        current = conn.execute(
            """
            SELECT * FROM personal_records
            WHERE user_id = ? AND exercise_name = ? AND record_type = ?
            """,
            (user_id, workout["exercise_name"], record_type),
        ).fetchone()

        if current and current["record_value"] >= value:
            continue

        with conn:
            conn.execute(
                """
                INSERT INTO personal_records (user_id, exercise_name, record_type, record_value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, exercise_name, record_type)
                DO UPDATE SET record_value = excluded.record_value, created_at = CURRENT_TIMESTAMP
                """,
                (user_id, workout["exercise_name"], record_type, value),
            )

        new_records.append(
            {
                "exercise_name": workout["exercise_name"],
                "record_type": record_type,
                "label": label,
                "record_value": value,
            }
        )

    return new_records


def _update_progress(user_id: int, previous: dict, workout: dict, xp_to_add: int, streak: dict) -> dict:
    total_xp = previous["total_xp"] + xp_to_add
    conn = get_connection()

    with conn:
        conn.execute(
            """
            UPDATE user_progress
            SET total_xp = ?,
                current_level = ?,
                current_streak = ?,
                longest_streak = ?,
                total_workouts = total_workouts + 1,
                total_reps = total_reps + ?,
                total_sets = total_sets + ?,
                total_time_seconds = total_time_seconds + ?,
                last_workout_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (
                total_xp,
                level_from_xp(total_xp),
                streak["current_streak"],
                max(previous["longest_streak"], streak["current_streak"]),
                workout["total_reps"],
                workout["total_sets"],
                workout["duration_seconds"],
                date.today().isoformat(),
                user_id,
            ),
        )

    return get_user_progress(user_id)


def _add_bonus_xp(user_id: int, xp_to_add: int) -> dict:
    progress = get_user_progress(user_id)
    total_xp = progress["total_xp"] + xp_to_add
    conn = get_connection()

    with conn:
        conn.execute(
            """
            UPDATE user_progress
            SET total_xp = ?, current_level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (total_xp, level_from_xp(total_xp), user_id),
        )

    return get_user_progress(user_id)


def _calculate_streak(last_workout_date: str | None, previous_streak: int) -> dict:
    today = date.today()

    if not last_workout_date:
        return {"current_streak": 1, "increased_today": True}

    try:
        last_date = datetime.strptime(last_workout_date, "%Y-%m-%d").date()
    except ValueError:
        return {"current_streak": 1, "increased_today": True}

    if last_date == today:
        return {"current_streak": max(1, previous_streak), "increased_today": False}

    if last_date == today - timedelta(days=1):
        return {"current_streak": previous_streak + 1, "increased_today": True}

    return {"current_streak": 1, "increased_today": True}


def _streak_bonus(current_streak: int, increased_today: bool) -> int:
    if not increased_today:
        return 0

    if current_streak >= 7:
        return 100

    if current_streak >= 3:
        return 50

    return 0
