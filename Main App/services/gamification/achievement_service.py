from services.persistence.exercise_repository import get_connection


DEFAULT_ACHIEVEMENTS = [
    ("first_workout", "First Workout", "Complete your first workout.", "FIRST", 50, "total_workouts", 1),
    ("total_reps_100", "100 Total Reps", "Complete 100 total reps.", "100", 100, "total_reps", 100),
    ("total_reps_500", "500 Total Reps", "Complete 500 total reps.", "500", 250, "total_reps", 500),
    ("squat_starter", "Squat Starter", "Complete 50 squats.", "SQ", 100, "exercise_reps:Squats", 50),
    ("pushup_warrior", "Push-up Warrior", "Complete 50 push-ups.", "PU", 100, "exercise_reps:Push-ups", 50),
    ("consistency_rookie", "Consistency Rookie", "Build a 3 day workout streak.", "3D", 150, "current_streak", 3),
    ("weekly_beast", "Weekly Beast", "Build a 7 day workout streak.", "7D", 300, "current_streak", 7),
    ("perfect_form", "Perfect Form", "Finish a workout with a form score of 90 or higher.", "90", 200, "workout_form_score", 90),
    ("workout_grinder", "Workout Grinder", "Complete 10 workouts.", "10X", 250, "total_workouts", 10),
]


def seed_achievements() -> None:
    conn = get_connection()

    with conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO achievements
                (code, name, description, icon, xp_reward, condition_type, condition_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            DEFAULT_ACHIEVEMENTS,
        )


def get_achievements_for_user(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT a.*, ua.unlocked_at
        FROM achievements a
        LEFT JOIN user_achievements ua
            ON ua.achievement_id = a.id AND ua.user_id = ?
        ORDER BY a.id
        """,
        (user_id,),
    ).fetchall()

    return [dict(row) for row in rows]


def evaluate_achievements(user_id: int, progress: dict, workout: dict) -> list[dict]:
    seed_achievements()
    conn = get_connection()
    unlocked = []
    achievements = conn.execute("SELECT * FROM achievements ORDER BY id").fetchall()
    unlocked_ids = {
        row["achievement_id"]
        for row in conn.execute(
            "SELECT achievement_id FROM user_achievements WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    }

    for achievement in achievements:
        if achievement["id"] in unlocked_ids:
            continue

        if _condition_met(conn, user_id, achievement, progress, workout):
            with conn:
                conn.execute(
                    "INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?, ?)",
                    (user_id, achievement["id"]),
                )
            unlocked.append(dict(achievement))

    return unlocked


def _condition_met(conn, user_id: int, achievement, progress: dict, workout: dict) -> bool:
    condition_type = achievement["condition_type"]
    target = achievement["condition_value"]

    if condition_type == "total_workouts":
        return progress.get("total_workouts", 0) >= target

    if condition_type == "total_reps":
        return progress.get("total_reps", 0) >= target

    if condition_type == "current_streak":
        return progress.get("current_streak", 0) >= target

    if condition_type == "workout_form_score":
        return workout.get("average_form_score", 0) >= target

    if condition_type.startswith("exercise_reps:"):
        exercise_name = condition_type.split(":", 1)[1]
        row = conn.execute(
            """
            SELECT COALESCE(SUM(total_reps), 0) AS reps
            FROM workout_sessions
            WHERE user_id = ? AND exercise_name = ?
            """,
            (user_id, exercise_name),
        ).fetchone()

        return (row["reps"] or 0) >= target

    return False
