def xp_required_for_level(level: int) -> int:
    if level <= 1:
        return 0

    return int(round(250 * (level - 1) * 1.25))


def level_from_xp(total_xp: int) -> int:
    level = 1

    while total_xp >= xp_required_for_level(level + 1):
        level += 1

    return level


def level_progress(total_xp: int) -> dict:
    level = level_from_xp(total_xp)
    current_floor = xp_required_for_level(level)
    next_level = level + 1
    next_floor = xp_required_for_level(next_level)
    span = max(1, next_floor - current_floor)

    return {
        "level": level,
        "next_level": next_level,
        "current_xp": total_xp,
        "level_floor": current_floor,
        "next_level_xp": next_floor,
        "xp_into_level": max(0, total_xp - current_floor),
        "xp_needed": span,
        "progress": min(1.0, max(0.0, (total_xp - current_floor) / span)),
    }


def calculate_xp(total_reps: int, total_sets: int, average_form_score: int, streak_bonus: int = 0, hold_seconds: int = 0) -> int:
    hold_xp = max(0, hold_seconds) if hold_seconds else 0

    return (
        25
        + max(0, total_reps) * 2
        + max(0, total_sets) * 10
        + hold_xp
        + int(round(max(0, average_form_score) * 0.5))
        + streak_bonus
    )


def calculate_calories_estimate(exercise_name: str, total_reps: int, duration_seconds: int) -> int:
    cardio_exercises = {"Jumping Jacks", "High Knees", "Mountain Climbers"}
    multiplier = 0.32 if exercise_name in cardio_exercises else 0.22
    time_bonus = max(0, duration_seconds) / 60 * 3

    return int(round((max(0, total_reps) * multiplier) + time_bonus))


def calculate_workout_score(total_reps: int, total_sets: int, average_form_score: int, duration_seconds: int) -> int:
    """Future multiplayer hook: reusable score for rooms, teams, or live leaderboards."""
    return int((total_reps * 10) + (total_sets * 50) + (average_form_score * 4) + max(0, duration_seconds) * 0.5)
