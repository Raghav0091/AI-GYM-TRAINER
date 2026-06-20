import sqlite3
import streamlit as st
from pathlib import Path
import hashlib
import hmac
import os

try:
    import bcrypt
except ImportError:
    bcrypt = None

_DB_PATH = str(Path(__file__).parent.parent.parent / "data.db")


@st.cache_resource
def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_connection() -> sqlite3.Connection:
    return _get_connection()


def init_db() -> None:
    conn = _get_connection()

    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exercises (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT    NOT NULL,
                reps          INTEGER NOT NULL DEFAULT 0,
                sets          INTEGER NOT NULL DEFAULT 0,
                time          INTEGER NOT NULL DEFAULT 0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        user_columns = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]

        if "password_hash" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

        columns = [row["name"] for row in conn.execute("PRAGMA table_info(exercises)").fetchall()]

        if "form_score" not in columns:
            conn.execute("ALTER TABLE exercises ADD COLUMN form_score INTEGER DEFAULT 0")

        if "form_score_samples" not in columns:
            conn.execute("ALTER TABLE exercises ADD COLUMN form_score_samples INTEGER DEFAULT 0")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_sessions (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id            INTEGER NOT NULL REFERENCES users(id),
                exercise_name      TEXT    NOT NULL,
                total_reps         INTEGER NOT NULL DEFAULT 0,
                total_sets         INTEGER NOT NULL DEFAULT 0,
                duration_seconds   INTEGER NOT NULL DEFAULT 0,
                average_form_score INTEGER NOT NULL DEFAULT 0,
                xp_earned          INTEGER NOT NULL DEFAULT 0,
                calories_estimate  INTEGER NOT NULL DEFAULT 0,
                created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id            INTEGER PRIMARY KEY REFERENCES users(id),
                total_xp           INTEGER NOT NULL DEFAULT 0,
                current_level      INTEGER NOT NULL DEFAULT 1,
                current_streak     INTEGER NOT NULL DEFAULT 0,
                longest_streak     INTEGER NOT NULL DEFAULT 0,
                total_workouts     INTEGER NOT NULL DEFAULT 0,
                total_reps         INTEGER NOT NULL DEFAULT 0,
                total_sets         INTEGER NOT NULL DEFAULT 0,
                total_time_seconds INTEGER NOT NULL DEFAULT 0,
                last_workout_date  TEXT,
                updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS achievements (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                code            TEXT UNIQUE NOT NULL,
                name            TEXT NOT NULL,
                description     TEXT NOT NULL,
                icon            TEXT NOT NULL DEFAULT '*',
                xp_reward       INTEGER NOT NULL DEFAULT 0,
                condition_type  TEXT NOT NULL,
                condition_value INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_achievements (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL REFERENCES users(id),
                achievement_id INTEGER NOT NULL REFERENCES achievements(id),
                unlocked_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_challenges (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                title          TEXT NOT NULL,
                description    TEXT NOT NULL,
                exercise_name  TEXT NOT NULL,
                target_reps    INTEGER NOT NULL DEFAULT 0,
                target_sets    INTEGER NOT NULL DEFAULT 0,
                target_form    INTEGER NOT NULL DEFAULT 0,
                xp_reward      INTEGER NOT NULL DEFAULT 0,
                challenge_date TEXT UNIQUE NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_daily_challenges (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                challenge_id  INTEGER NOT NULL REFERENCES daily_challenges(id),
                progress_reps INTEGER NOT NULL DEFAULT 0,
                progress_sets INTEGER NOT NULL DEFAULT 0,
                completed     INTEGER NOT NULL DEFAULT 0,
                completed_at  TIMESTAMP,
                UNIQUE(user_id, challenge_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS personal_records (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT NOT NULL,
                record_type   TEXT NOT NULL,
                record_value  INTEGER NOT NULL DEFAULT 0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, exercise_name, record_type)
            )
            """
        )


def get_user(username: str) -> sqlite3.Row:
    conn = _get_connection()

    return conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()


def create_user(username: str) -> sqlite3.Row:
    conn = _get_connection()
    
    with conn:
        conn.execute(
            "INSERT INTO users (username) VALUES (?)", (username,)
        )

    return get_user(username) 


def _hash_password(password: str) -> str:
    if bcrypt is not None:
        return "bcrypt$" + bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"pbkdf2${salt.hex()}:{digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        if stored_hash.startswith("bcrypt$"):
            if bcrypt is None:
                return False

            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.removeprefix("bcrypt$").encode("utf-8"))

        if stored_hash.startswith("pbkdf2$"):
            stored_hash = stored_hash.removeprefix("pbkdf2$")

        salt_hex, digest_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def set_user_password(user_id: int, password: str) -> None:
    conn = _get_connection()

    with conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_password(password), user_id),
        )


def register_user(username: str, password: str) -> sqlite3.Row | None:
    existing_user = get_user(username)

    if existing_user is not None:
        if existing_user["password_hash"]:
            return None

        set_user_password(existing_user["id"], password)
        return get_user(username)

    conn = _get_connection()

    with conn:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, _hash_password(password)),
        )

    return get_user(username)


def authenticate_user(username: str, password: str) -> sqlite3.Row | None:
    user = get_user(username)

    if user is None:
        return None

    stored_hash = user["password_hash"]

    if not stored_hash:
        set_user_password(user["id"], password)
        return get_user(username)

    if _verify_password(password, stored_hash):
        return user

    return None


def get_or_create_user(username: str) -> sqlite3.Row:
    user = get_user(username)

    if user is None:
        user = create_user(username)
    
    return user


def add_exercise(user_id, exercise_name, reps, sets, time, form_score=0):
    conn = _get_connection()

    with conn:
        existing = conn.execute("""
            SELECT * FROM exercises 
            WHERE user_id = ? AND exercise_name = ? AND Date('created_at') = Date('now')
        """, (user_id, exercise_name)).fetchone()

        if existing:
            existing_score = existing["form_score"] or 0
            existing_samples = existing["form_score_samples"] or 0
            new_samples = 1 if form_score else 0
            total_samples = existing_samples + new_samples
            averaged_score = existing_score

            if total_samples:
                averaged_score = round(
                    ((existing_score * existing_samples) + (form_score * new_samples)) / total_samples
                )

            conn.execute("""
                UPDATE exercises 
                SET reps = reps + ?, sets = sets + ?, time = time + ?,
                    form_score = ?, form_score_samples = ?
                WHERE id = ?
            """, (reps, sets, time, averaged_score, total_samples, existing['id']))
        else:
            conn.execute("""
                INSERT INTO exercises (user_id, exercise_name, sets, reps, time, form_score, form_score_samples)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, exercise_name, sets, reps, time, form_score, 1 if form_score else 0))


def get_users_exercises(user_id):
    conn = _get_connection()

    return conn.execute("""
        SELECT * FROM exercises 
        WHERE user_id = ?
    """, (user_id,)).fetchall()
