from datetime import date

from services.persistence.exercise_repository import get_connection


CHALLENGE_TEMPLATES = [
    ("Squat Power", "Complete 30 squats today.", "Squats", 30, 0, 0, 120),
    ("Push-up Push", "Complete 25 push-ups today.", "Push-ups", 25, 0, 0, 120),
    ("Cardio Spark", "Complete 50 jumping jacks today.", "Jumping Jacks", 50, 0, 0, 140),
    ("Set Builder", "Complete 3 sets of any exercise.", "Any", 0, 3, 0, 110),
    ("Clean Form", "Finish one workout with a form score above 80.", "Any", 0, 0, 80, 130),
]


def ensure_daily_challenge(challenge_date: date | None = None) -> dict:
    conn = get_connection()
    challenge_date = challenge_date or date.today()
    date_text = challenge_date.isoformat()
    existing = conn.execute(
        "SELECT * FROM daily_challenges WHERE challenge_date = ?",
        (date_text,),
    ).fetchone()

    if existing:
        return dict(existing)

    template = CHALLENGE_TEMPLATES[challenge_date.toordinal() % len(CHALLENGE_TEMPLATES)]

    with conn:
        conn.execute(
            """
            INSERT INTO daily_challenges
                (title, description, exercise_name, target_reps, target_sets, target_form, xp_reward, challenge_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*template, date_text),
        )

    return dict(
        conn.execute(
            "SELECT * FROM daily_challenges WHERE challenge_date = ?",
            (date_text,),
        ).fetchone()
    )


def get_user_daily_challenge(user_id: int) -> dict:
    conn = get_connection()
    challenge = ensure_daily_challenge()

    with conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO user_daily_challenges (user_id, challenge_id)
            VALUES (?, ?)
            """,
            (user_id, challenge["id"]),
        )

    row = conn.execute(
        """
        SELECT c.*, uc.progress_reps, uc.progress_sets, uc.completed, uc.completed_at
        FROM daily_challenges c
        JOIN user_daily_challenges uc ON uc.challenge_id = c.id
        WHERE uc.user_id = ? AND c.id = ?
        """,
        (user_id, challenge["id"]),
    ).fetchone()

    return dict(row)


def update_daily_challenge(user_id: int, workout: dict) -> dict:
    conn = get_connection()
    challenge = get_user_daily_challenge(user_id)

    if challenge["completed"]:
        return {"challenge": challenge, "completed_now": False, "xp_awarded": 0}

    exercise_matches = challenge["exercise_name"] == "Any" or challenge["exercise_name"] == workout["exercise_name"]
    reps_to_add = workout["total_reps"] if exercise_matches else 0
    sets_to_add = workout["total_sets"] if exercise_matches else 0
    progress_reps = challenge["progress_reps"]
    progress_sets = challenge["progress_sets"]

    if challenge["target_reps"]:
        progress_reps = min(challenge["target_reps"], progress_reps + reps_to_add)

    if challenge["target_sets"]:
        progress_sets = min(challenge["target_sets"], progress_sets + sets_to_add)

    reps_done = not challenge["target_reps"] or progress_reps >= challenge["target_reps"]
    sets_done = not challenge["target_sets"] or progress_sets >= challenge["target_sets"]
    form_done = not challenge["target_form"] or workout["average_form_score"] >= challenge["target_form"]
    completed_now = bool(reps_done and sets_done and form_done and (exercise_matches or challenge["target_form"]))

    with conn:
        conn.execute(
            """
            UPDATE user_daily_challenges
            SET progress_reps = ?, progress_sets = ?, completed = ?,
                completed_at = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE user_id = ? AND challenge_id = ?
            """,
            (progress_reps, progress_sets, int(completed_now), int(completed_now), user_id, challenge["id"]),
        )

    updated = get_user_daily_challenge(user_id)

    return {
        "challenge": updated,
        "completed_now": completed_now,
        "xp_awarded": updated["xp_reward"] if completed_now else 0,
    }
