import streamlit as st
import html
import os
import time
import pandas as pd
import streamlit.components.v1 as components
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS, EXERCISE_TUTORIALS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises
from services.gamification.achievement_service import get_achievements_for_user
from services.gamification.challenge_service import get_user_daily_challenge
from services.gamification.progression_service import (
    bootstrap_gamification,
    finalize_workout,
    get_leaderboard,
    get_personal_records,
    get_user_progress,
)
from services.gamification.scoring_service import level_progress
from services.vision.detector_registry import DETECTOR_REGISTRY
from services.multiplayer.leaderboard_service import get_room_leaderboard
from services.multiplayer.room_service import (
    add_room_event,
    create_room,
    end_room,
    get_room,
    get_room_by_code,
    get_room_events,
    get_room_members,
    join_room,
    start_room,
)
from services.multiplayer.score_service import upsert_room_score
from groq import Groq
from dotenv import find_dotenv, load_dotenv
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech

from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio, queue_voice_feedback


def safe_text(value):
    return html.escape(str(value))


CAMERA_ANGLE_HINTS = {
    "Squats": "Side view",
    "Push-ups": "Side view",
    "Biceps Curls (Dumbbell)": "Front or side view",
    "Shoulder Press": "Front view",
    "Lunges": "Side view",
    "Jumping Jacks": "Front view",
    "High Knees": "Front view",
    "Crunches": "Side view",
    "Sit-ups": "Side view",
    "Plank": "Side view",
    "Mountain Climbers": "Side view",
}


DIFFICULTY_HINTS = {
    "Squats": "Beginner",
    "Push-ups": "Intermediate",
    "Biceps Curls (Dumbbell)": "Beginner",
    "Shoulder Press": "Intermediate",
    "Lunges": "Intermediate",
    "Jumping Jacks": "Beginner",
    "High Knees": "Beginner",
    "Crunches": "Beginner",
    "Sit-ups": "Intermediate",
    "Plank": "Beginner",
    "Mountain Climbers": "Intermediate",
}


def load_environment():
    load_dotenv()
    env_path = find_dotenv(usecwd=True)

    if env_path:
        load_dotenv(env_path)


def get_groq_api_key():
    api_key = os.environ.get("GROQ_API_KEY", "")

    try:
        if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    return api_key


def render_section_header(title, subtitle=""):
    subtitle_html = f"<p class='section-subtitle'>{safe_text(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-shell">
            <div class="section-kicker">Performance Dashboard</div>
            <h2 class="section-title">{safe_text(title)}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_start_screen():
    selected_exercise = st.session_state.get("plan_exercise", "Squats")
    tutorial = EXERCISE_TUTORIALS.get(selected_exercise, {})
    muscles = tutorial.get("muscles", "Full body")
    camera_angle = CAMERA_ANGLE_HINTS.get(selected_exercise, "Full body view")
    difficulty = DIFFICULTY_HINTS.get(selected_exercise, "Beginner")

    st.markdown(
        f"""
        <section class="hero hero-pro">
            <div class="hero-panel">
                <div class="hero-badge">AI FITNESS COACH</div>
                <h1>Train Smarter.<br>Move Better.<br>Level Up.</h1>
                <p>
                    A real-time training console for rep tracking, form scoring, AI coaching,
                    daily challenges, XP, and personal records.
                </p>
                <div class="hero-actions">
                    <span>Choose a workout in the left panel</span>
                    <strong>Camera analysis starts when you press Start Workout</strong>
                </div>
            </div>
            <div class="hero-console">
                <div class="console-orbit">
                    <span>FORM</span>
                    <strong>92</strong>
                </div>
                <div class="console-row"><span>Pose AI</span><strong>Ready</strong></div>
                <div class="console-row"><span>Voice Coach</span><strong>Armed</strong></div>
                <div class="console-row"><span>Daily XP</span><strong>+120</strong></div>
            </div>
        </section>
        <div class="exercise-preview">
            <div>
                <div class="section-kicker">Selected Workout</div>
                <h2>{safe_text(selected_exercise)}</h2>
                <p>{safe_text(tutorial.get("description", "Get ready for a guided AI workout."))}</p>
            </div>
            <div class="preview-stat"><span>Muscles</span><strong>{safe_text(muscles)}</strong></div>
            <div class="preview-stat"><span>Difficulty</span><strong>{safe_text(difficulty)}</strong></div>
            <div class="preview-stat"><span>Camera</span><strong>{safe_text(camera_angle)}</strong></div>
        </div>
        <div class="feature-grid">
            <div class="glass-card feature-card">
                <div class="feature-icon">01</div>
                <h3>AI Voice Coach</h3>
                <p>Short, focused coaching cues while you train.</p>
            </div>
            <div class="glass-card feature-card">
                <div class="feature-icon">02</div>
                <h3>Form Score</h3>
                <p>Live movement quality scoring for every session.</p>
            </div>
            <div class="glass-card feature-card">
                <div class="feature-icon">03</div>
                <h3>Progress Tracking</h3>
                <p>See your reps, sets, time, and weekly trends.</p>
            </div>
            <div class="glass-card feature-card">
                <div class="feature-icon">04</div>
                <h3>Real-time Rep Counter</h3>
                <p>Automatic counting through live pose detection.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_camera_setup_tips():
    st.markdown(
        """
        <div class="camera-tips">
            <div class="section-kicker">Camera Setup Tips</div>
            <ul>
                <li>Allow camera permission in your browser.</li>
                <li>Stand 2-3 meters away so your full body is visible.</li>
                <li>Use good lighting and avoid very baggy clothing.</li>
                <li>Use side view for squats, push-ups, lunges, planks, and sit-ups.</li>
                <li>Use front view for curls, shoulder press, high knees, and jumping jacks.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workout_header():
    exercise = st.session_state.get("exercise_type", "Workout")
    sets_completed = st.session_state.get("sets_completed", 0)
    target_sets = st.session_state.get("target_sets", 0)
    reps = st.session_state.get("reps", 0)
    form_score = st.session_state.get("form_score", 0)

    camera_status = st.session_state.get("camera_status", "Camera loading")
    st.markdown(
        f"""
        <div class="workout-card">
            <div class="workout-card__row">
                <div>
                    <div class="section-kicker">Workout Active</div>
                    <h2>{safe_text(exercise)}</h2>
                    <p>{sets_completed} / {target_sets} sets completed | {reps} total reps</p>
                </div>
                <div class="status-stack">
                    <div class="camera-pill">{safe_text(camera_status)}</div>
                    <div class="score-pill">Form Score {form_score} / 100</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_active_workout_grid():
    exercise = st.session_state.get("exercise_type", "Workout")
    total_reps = st.session_state.get("reps", 0)
    hold_seconds = st.session_state.get("hold_seconds", 0)
    sets_completed = st.session_state.get("sets_completed", 0)
    target_sets = st.session_state.get("target_sets", 0)
    reps_per_set = st.session_state.get("reps_per_set", 0)
    form_score = st.session_state.get("form_score", 0)
    stage = st.session_state.get("detector_stage", "setup")
    duration = int(time.time() - (st.session_state.get("workout_started_at") or time.time()))
    primary_label = "Hold Time" if exercise == "Plank" else "Reps"
    primary_value = f"{int(hold_seconds)}s" if exercise == "Plank" else total_reps
    target_label = "Target Hold" if exercise == "Plank" else "Sets"
    target_value = f"{int(hold_seconds) % max(1, reps_per_set)} / {reps_per_set}s" if exercise == "Plank" else f"{sets_completed}/{target_sets}"

    st.markdown(
        f"""
        <div class="active-grid">
            <div class="active-card">
                <span>Exercise</span>
                <strong>{safe_text(exercise)}</strong>
            </div>
            <div class="active-card accent-purple">
                <span>Form Score</span>
                <strong>{form_score}/100</strong>
            </div>
            <div class="active-card">
                <span>{safe_text(primary_label)}</span>
                <strong>{primary_value}</strong>
            </div>
            <div class="active-card">
                <span>{safe_text(target_label)}</span>
                <strong>{target_value}</strong>
            </div>
            <div class="active-card accent-purple">
                <span>Stage</span>
                <strong>{safe_text(stage)}</strong>
            </div>
            <div class="active-card">
                <span>Duration</span>
                <strong>{duration}s</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_technique_card(exercise):
    tutorial = EXERCISE_TUTORIALS.get(exercise, {})
    mistakes = tutorial.get("mistakes", [])[:3]
    mistake_html = "".join(f"<li>{safe_text(item)}</li>" for item in mistakes)
    st.markdown(
        f"""
        <div class="technique-card">
            <div class="section-kicker">Technique</div>
            <h3>{safe_text(exercise)} guide</h3>
            <p><strong>Recommended camera:</strong> {safe_text(CAMERA_ANGLE_HINTS.get(exercise, "Full body view"))}</p>
            <p><strong>Focus:</strong> {safe_text(tutorial.get("muscles", "Full body"))}</p>
            <ul>{mistake_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_coach_card(message):
    st.markdown(
        f"""
        <div class="coach-card">
            <div class="coach-label">AI Coach</div>
            <h3>Live Feedback</h3>
            <p>{safe_text(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_session_summary(summary):
    st.markdown(
        f"""
        <div class="coach-card">
            <div class="coach-label">Session Summary</div>
            <h3>Workout Recap</h3>
            <p>{safe_text(summary).replace(chr(10), "<br>")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_level_card(progress):
    level = level_progress(progress.get("total_xp", 0))
    st.markdown(
        f"""
        <div class="level-card">
            <div>
                <div class="section-kicker">Level {level["level"]} Athlete</div>
                <h3>{progress.get("total_xp", 0)} XP</h3>
                <p>{level["xp_into_level"]} / {level["xp_needed"]} XP to Level {level["next_level"]}</p>
            </div>
            <div class="level-ring">{int(level["progress"] * 100)}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(level["progress"])


def render_daily_challenge_card(challenge):
    progress_label = "Workout"
    progress_value = 1 if challenge.get("completed") else 0
    progress_target = 1

    if challenge.get("target_reps", 0):
        progress_label = "Reps"
        progress_value = challenge.get("progress_reps", 0)
        progress_target = challenge.get("target_reps", 1)
    elif challenge.get("target_sets", 0):
        progress_label = "Sets"
        progress_value = challenge.get("progress_sets", 0)
        progress_target = challenge.get("target_sets", 1)
    elif challenge.get("target_form", 0):
        progress_label = "Form Score"
        progress_target = challenge.get("target_form", 1)

    st.markdown(
        f"""
        <div class="challenge-card">
            <div class="section-kicker">Today's Challenge</div>
            <h3>{safe_text(challenge.get("title", "Daily Challenge"))}</h3>
            <p>{safe_text(challenge.get("description", ""))}</p>
            <div class="challenge-meta">
                <span>{safe_text(progress_label)}: {progress_value} / {progress_target}</span>
                <strong>+{challenge.get("xp_reward", 0)} XP</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, progress_value / max(1, progress_target)))


def render_reward_screen(result):
    if not result:
        return

    workout = result["workout"]
    if result.get("cancelled"):
        st.markdown(
            f"""
            <div class="reward-screen reward-screen--cancelled">
                <div class="reward-kicker">Workout Cancelled</div>
                <h2>{safe_text(workout["exercise_name"])}</h2>
                <p>{safe_text(result.get("message", "No valid movement was detected."))}</p>
                <div class="reward-grid">
                    <div><span>Reps</span><strong>{workout.get("total_reps", 0)}</strong></div>
                    <div><span>Hold</span><strong>{int(workout.get("hold_seconds", 0))}s</strong></div>
                    <div><span>Sets</span><strong>{workout.get("total_sets", 0)}</strong></div>
                    <div><span>XP</span><strong>+0</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    progress = result["progress"]
    level = result["level_progress"]
    achievements = result.get("achievements", [])
    records = result.get("personal_records", [])
    challenge = result.get("challenge", {})
    challenge_info = challenge.get("challenge", {})
    challenge_status = "Completed" if challenge.get("completed_now") else "In progress"
    primary_label = "Hold" if workout["exercise_name"] == "Plank" else "Reps"
    primary_value = f"{int(workout.get('hold_seconds', 0))}s" if workout["exercise_name"] == "Plank" else workout["total_reps"]
    achievement_html = "".join(
        f"<li><strong>{safe_text(item['name'])}</strong> +{item['xp_reward']} XP</li>"
        for item in achievements
    ) or "<li>No new badges this time. Keep stacking progress.</li>"
    record_html = "".join(
        f"<li><strong>{safe_text(item['label'])}</strong>: {item['record_value']}</li>"
        for item in records
    ) or "<li>No new PR, but the session still moved you forward.</li>"

    st.markdown(
        f"""
        <div class="reward-screen">
            <div class="reward-kicker">Workout Complete</div>
            <h2>{safe_text(workout["exercise_name"])}</h2>
            <div class="reward-grid">
                <div><span>{safe_text(primary_label)}</span><strong>{primary_value}</strong></div>
                <div><span>Sets</span><strong>{workout["total_sets"]}</strong></div>
                <div><span>Form</span><strong>{workout["average_form_score"]}/100</strong></div>
                <div><span>XP</span><strong>+{result["xp_earned"]}</strong></div>
            </div>
            <div class="reward-split">
                <div>
                    <h3>Level Progress</h3>
                    <p>Level {progress["current_level"]} | {level["xp_into_level"]} / {level["xp_needed"]} XP to Level {level["next_level"]}</p>
                    <p>Workout score: {result["workout_score"]} | Calories estimate: {result["calories_estimate"]}</p>
                </div>
                <div>
                    <h3>Daily Challenge</h3>
                    <p>{safe_text(challenge_info.get("title", "Daily Challenge"))}: {challenge_status}</p>
                    <p>Bonus: +{challenge.get("xp_awarded", 0)} XP</p>
                </div>
            </div>
            <div class="reward-split">
                <div>
                    <h3>Achievements</h3>
                    <ul>{achievement_html}</ul>
                </div>
                <div>
                    <h3>Personal Records</h3>
                    <ul>{record_html}</ul>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_gamification_dashboard(user_id):
    progress = get_user_progress(user_id)
    challenge = get_user_daily_challenge(user_id)
    achievements = get_achievements_for_user(user_id)
    records = get_personal_records(user_id)
    leaderboard = get_leaderboard()

    render_section_header("Progression", "XP, levels, streaks, daily challenges, badges, and local rankings.")
    render_level_card(progress)

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Streak", f"{progress['current_streak']} days")
    col2.metric("Longest Streak", f"{progress['longest_streak']} days")
    col3.metric("Total XP", progress["total_xp"])

    render_daily_challenge_card(challenge)

    unlocked_count = sum(1 for item in achievements if item.get("unlocked_at"))
    st.markdown("##### Achievements")
    badge_cards = []

    for item in achievements:
        locked_class = " badge-card--locked" if not item.get("unlocked_at") else ""
        status_text = "Unlocked" if item.get("unlocked_at") else f"+{item['xp_reward']} XP"
        badge_cards.append(
            f"<div class='badge-card{locked_class}'>"
            f"<div class='badge-icon'>{safe_text(item['icon'])}</div>"
            f"<h4>{safe_text(item['name'])}</h4>"
            f"<p>{safe_text(item['description'])}</p>"
            f"<span>{safe_text(status_text)}</span>"
            "</div>"
        )

    badge_html = "".join(badge_cards)
    st.markdown(
        f"<p class='section-subtitle'>{unlocked_count} / {len(achievements)} badges unlocked</p><div class='badge-grid'>{badge_html}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("##### Personal Records")
    if records:
        st.dataframe(
            pd.DataFrame(records)[["exercise_name", "record_type", "record_value", "created_at"]],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("End a workout to set your first personal record.")

    st.markdown("##### Local Leaderboard")
    if leaderboard:
        leaderboard_df = pd.DataFrame(leaderboard)
        leaderboard_df.index = leaderboard_df.index + 1
        st.dataframe(
            leaderboard_df.rename(
                columns={
                    "username": "User",
                    "current_level": "Level",
                    "total_xp": "XP",
                    "total_reps": "Total Reps",
                    "current_streak": "Streak",
                    "longest_streak": "Best Streak",
                    "total_workouts": "Workouts",
                    "best_form_score": "Best Form",
                }
            ),
            width="stretch",
        )
    else:
        st.info("Leaderboard unlocks after the first workout.")


def render_room_leaderboard(room):
    leaderboard = get_room_leaderboard(room["id"], room["exercise_name"])
    st.markdown("##### Live Leaderboard")

    if not leaderboard:
        st.info("Scores appear when players start moving.")
        return

    cards = []
    for index, row in enumerate(leaderboard, start=1):
        primary = f"{int(row['hold_seconds'])}s" if room["exercise_name"] == "Plank" else int(row["reps"])
        primary_label = "Hold" if room["exercise_name"] == "Plank" else "Reps"
        cards.append(
            f"<div class='leaderboard-card'>"
            f"<div class='rank-pill'>#{index}</div>"
            f"<h3>{safe_text(row['username'])}</h3>"
            f"<div class='leaderboard-stats'>"
            f"<span>{primary_label}<strong>{primary}</strong></span>"
            f"<span>Sets<strong>{int(row['sets_completed'])}</strong></span>"
            f"<span>Form<strong>{int(row['form_score'])}</strong></span>"
            f"<span>Score<strong>{int(row['workout_score'])}</strong></span>"
            f"</div>"
            f"<p>{safe_text(row['status'])}</p>"
            f"</div>"
        )

    st.markdown(f"<div class='leaderboard-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_room_events(room_id):
    events = get_room_events(room_id)
    st.markdown("##### Activity Feed")

    if not events:
        st.info("Room activity will appear here.")
        return

    event_html = "".join(
        f"<li><span>{safe_text(event['event_type'])}</span>{safe_text(event['message'])}</li>"
        for event in events
    )
    st.markdown(f"<ul class='activity-feed'>{event_html}</ul>", unsafe_allow_html=True)


def render_fitness_arena():
    render_section_header(
        "AI Fitness Arena",
        "Create a local workout room, invite players with a room code, and compete on a live leaderboard.",
    )

    room_id = st.session_state.get("arena_room_id")
    room = get_room(room_id) if room_id else None

    if room:
        render_room_lobby(room)
        return

    create_tab, join_tab = st.tabs(["Create Room", "Join Room"])

    with create_tab:
        with st.form("create_arena_room", clear_on_submit=False):
            room_name = st.text_input("Room name", value=f"{st.session_state.get('username', 'Athlete')}'s Arena")
            exercise_name = st.selectbox("Exercise", EXERCISE_OPTIONS, key="arena_create_exercise")
            game_mode = st.selectbox("Game mode", ["Practice", "Race", "Team Challenge"])
            target_sets = st.number_input("Target sets", min_value=1, max_value=20, value=3, step=1)

            if exercise_name == "Plank":
                target_hold_seconds = st.number_input("Target hold seconds", min_value=10, max_value=300, value=30, step=5)
                target_reps = 0
            else:
                target_reps = st.number_input("Target reps", min_value=5, max_value=500, value=30, step=5)
                target_hold_seconds = 0

            submitted = st.form_submit_button("Create Room", width="stretch")

        if submitted:
            if game_mode == "Team Challenge":
                st.info("Team Challenge coming soon. Use Practice or Race for now.")
            elif exercise_name not in DETECTOR_REGISTRY:
                st.error("Detector not available for this exercise yet.")
            else:
                room = create_room(
                    st.session_state.user_id,
                    st.session_state.username,
                    room_name,
                    exercise_name,
                    int(target_reps),
                    int(target_sets),
                    int(target_hold_seconds),
                    game_mode,
                )
                st.session_state.arena_room_id = room["id"]
                st.session_state.arena_room_code = room["room_code"]
                st.rerun()

    with join_tab:
        with st.form("join_arena_room", clear_on_submit=False):
            room_code = st.text_input("Room code", placeholder="GYM-742").upper()
            submitted = st.form_submit_button("Join Room", width="stretch")

        if submitted:
            room, error = join_room(room_code, st.session_state.user_id, st.session_state.username)

            if error:
                st.error(error)
            else:
                st.session_state.arena_room_id = room["id"]
                st.session_state.arena_room_code = room["room_code"]
                st.rerun()


def render_room_lobby(room):
    members = get_room_members(room["id"])
    is_host = room["host_user_id"] == st.session_state.get("user_id")
    target_text = (
        f"{room['target_hold_seconds']} sec x {room['target_sets']} sets"
        if room["exercise_name"] == "Plank"
        else f"{room['target_reps']} reps / {room['target_sets']} sets"
    )

    st.markdown(
        f"""
        <div class="arena-room-card">
            <div>
                <div class="section-kicker">Room Code</div>
                <h1>{safe_text(room["room_code"])}</h1>
                <p>{safe_text(room.get("room_name") or "Fitness Arena")} | {safe_text(room["status"].title())}</p>
            </div>
            <div class="arena-room-meta">
                <span>Exercise<strong>{safe_text(room["exercise_name"])}</strong></span>
                <span>Mode<strong>{safe_text(room["game_mode"])}</strong></span>
                <span>Target<strong>{safe_text(target_text)}</strong></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if room["game_mode"] == "Team Challenge":
        st.info("Team Challenge coming soon.")

    if room.get("winner_user_id"):
        winner = next((member for member in members if member["user_id"] == room["winner_user_id"]), None)
        winner_name = winner["username"] if winner else "Winner"
        st.success(f"{winner_name} won the race!")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("##### Joined Players")
        member_html = "".join(
            f"<div class='player-pill'>{safe_text(member['username'])}{' <span>Host</span>' if member['is_host'] else ''}</div>"
            for member in members
        )
        st.markdown(f"<div class='player-list'>{member_html}</div>", unsafe_allow_html=True)

    with col2:
        if st.button("Refresh Room", width="stretch"):
            st.rerun()

        if is_host and room["status"] == "waiting":
            if st.button("Start Room Workout", width="stretch"):
                if start_room(room["id"], st.session_state.user_id):
                    st.session_state.room_mode_active = True
                    st.session_state.arena_room_id = room["id"]
                    reset_workout_state(
                        room["exercise_name"],
                        room["target_sets"],
                        room["target_hold_seconds"] if room["exercise_name"] == "Plank" else room["target_reps"],
                    )
                    st.rerun()

        elif room["status"] == "waiting":
            st.info("Waiting for host to start.")

        if room["status"] == "active" and not st.session_state.get("workout_started"):
            if st.button("Start My Camera Workout", width="stretch"):
                st.session_state.room_mode_active = True
                st.session_state.arena_room_id = room["id"]
                reset_workout_state(
                    room["exercise_name"],
                    room["target_sets"],
                    room["target_hold_seconds"] if room["exercise_name"] == "Plank" else room["target_reps"],
                )
                st.rerun()

        if is_host and room["status"] != "completed":
            if st.button("End Room", width="stretch"):
                end_room(room["id"], st.session_state.user_id)
                st.session_state.room_mode_active = False
                st.rerun()

        if st.button("Leave Room View", width="stretch"):
            st.session_state.arena_room_id = None
            st.session_state.arena_room_code = ""
            st.session_state.room_mode_active = False
            st.rerun()

    render_room_leaderboard(room)
    render_room_events(room["id"])


def render_exercise_tutorial(exercise):
    tutorial = EXERCISE_TUTORIALS.get(exercise, {})
    steps = tutorial.get("steps", [])
    mistakes = tutorial.get("mistakes", [])
    muscles = tutorial.get("muscles", "Full body")
    description = tutorial.get("description", "Tutorial details coming soon.")
    video_url = tutorial.get("video_url")

    steps_html = "".join(f"<li>{safe_text(step)}</li>" for step in steps)
    mistakes_html = "".join(f"<li>{safe_text(mistake)}</li>" for mistake in mistakes)

    st.markdown(
        f"""
        <div class="tutorial-card">
            <div class="section-kicker">Exercise Tutorial</div>
            <h2>{safe_text(exercise)}</h2>
            <p>{safe_text(description)}</p>
            <div class="tutorial-meta"><strong>Muscles:</strong> {safe_text(muscles)}</div>
            <div class="tutorial-columns">
                <div>
                    <h3>How to perform</h3>
                    <ol>{steps_html}</ol>
                </div>
                <div>
                    <h3>Common mistakes</h3>
                    <ul>{mistakes_html}</ul>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if video_url:
        components.html(
            f"""
            <div style="position:relative;width:100%;padding-top:56.25%;border-radius:24px;overflow:hidden;border:1px solid rgba(255,255,255,.09);background:#1A1A1A;">
                <iframe src="{safe_text(video_url)}" title="{safe_text(exercise)} demo video" style="position:absolute;inset:0;width:100%;height:100%;border:0;" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
            </div>
            """,
            height=360,
        )
    else:
        st.markdown(
            """
            <div class="tutorial-card tutorial-placeholder">
                <h3>Demo video coming soon.</h3>
                <p>This exercise still includes instructions and live camera analysis.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )



def setup_voice_pipeline():
    if "voice_pipeline" in st.session_state:
        return

    api_key = get_groq_api_key()

    if not api_key:
        st.session_state.voice_pipeline = None
        st.warning("GROQ_API_KEY is missing. AI voice coaching and AI summaries are disabled until you add it to .env.")
        return

    try:
        groq_client = Groq(api_key=api_key)
        llm_coach = LLMCoach(groq_client)
        tts = TextToSpeech()
        st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
    except Exception as e:
        st.session_state.voice_pipeline = None
        st.error(f"Voice coach failed to load: {e}")


def reset_workout_state(plan_exercise, plan_sets, plan_reps):
    st.session_state.exercise_type = plan_exercise
    st.session_state.target_sets = int(plan_sets)
    st.session_state.reps_per_set = int(plan_reps)
    st.session_state.reps = 0
    st.session_state.current_set_reps = 0
    st.session_state.sets_completed = 0
    st.session_state.hold_seconds = 0
    st.session_state.form_score = 0
    st.session_state.form_score_total = 0
    st.session_state.form_score_samples = 0
    st.session_state.average_form_score = 0
    st.session_state.session_summary = ""
    st.session_state.summary_generated = False
    st.session_state.gamification_result = None
    st.session_state.gamification_processed = False
    st.session_state.audio_to_play = None
    st.session_state.coach_feedback = ""
    st.session_state.audio_played = True
    st.session_state.audio_pause_until = 0.0
    st.session_state.workout_started = True
    st.session_state.workout_started_at = time.time()
    st.session_state.set_cycle_started_at = time.time()
    st.session_state.last_saved_sets_completed = 0
    st.session_state.last_notified_sets_completed = 0
    st.session_state.last_notified_workout_complete = False


def complete_workout_session(exercise):
    if st.session_state.get("gamification_processed"):
        return st.session_state.get("gamification_result")

    started_at = st.session_state.get("workout_started_at") or st.session_state.get("set_cycle_started_at") or time.time()
    hold_seconds = int(st.session_state.get("hold_seconds", 0))
    workout = {
        "exercise_name": exercise,
        "total_reps": 0 if exercise == "Plank" else int(st.session_state.get("reps", 0)),
        "total_sets": int(st.session_state.get("sets_completed", 0)),
        "duration_seconds": max(1, int(time.time() - started_at)),
        "average_form_score": int(st.session_state.get("average_form_score") or st.session_state.get("form_score", 0)),
        "hold_seconds": hold_seconds,
    }

    reps_per_set = int(st.session_state.get("reps_per_set", 0))
    valid_workout = (
        (hold_seconds >= 10 or workout["total_sets"] > 0)
        if exercise == "Plank"
        else ((workout["total_reps"] > 0 and workout["total_sets"] > 0) or (reps_per_set > 0 and workout["total_reps"] >= reps_per_set))
    )

    if not valid_workout:
        result = {
            "cancelled": True,
            "workout": workout,
            "xp_earned": 0,
            "message": "Workout cancelled. No valid reps or hold time were detected, so no XP was awarded.",
        }
        st.session_state.gamification_result = result
        st.session_state.gamification_processed = True
        st.session_state.session_summary = result["message"]
        st.session_state.summary_generated = True
        st.session_state.coach_feedback = "Workout cancelled. I did not detect enough movement to save this session."
        return result

    result = finalize_workout(st.session_state.get("user_id"), workout)
    st.session_state.gamification_result = result
    st.session_state.gamification_processed = True
    return result


def generate_session_summary(exercise):
    if st.session_state.get("summary_generated"):
        return

    sets_completed = st.session_state.get("sets_completed", 0)
    total_reps = st.session_state.get("reps", 0)
    form_score = st.session_state.get("average_form_score") or st.session_state.get("form_score", 0)
    gamification = st.session_state.get("gamification_result") or {}
    progress = gamification.get("progress", {})
    xp_earned = gamification.get("xp_earned", 0)
    current_level = progress.get("current_level", 1)
    pipeline = st.session_state.get("voice_pipeline")

    if not pipeline:
        st.session_state.session_summary = (
            f"AI summary unavailable because GROQ_API_KEY is missing. "
            f"{exercise}: {sets_completed} sets, {total_reps} reps, form score {form_score}/100, "
            f"+{xp_earned} XP earned."
        )
        st.session_state.summary_generated = True
        return

    try:
        st.session_state.session_summary = pipeline.llm.summarize_session(
            exercise=exercise,
            sets_completed=sets_completed,
            total_reps=total_reps,
            form_score=form_score,
            xp_earned=xp_earned,
            current_level=current_level,
        )
    except Exception as exc:
        st.warning(f"AI session summary failed: {exc}")
        st.session_state.session_summary = (
            f"{exercise}: {sets_completed} sets, {total_reps} reps, form score {form_score}/100. "
            f"You earned {xp_earned} XP and reached Level {current_level}. "
            "Keep your movement controlled and review form cues before the next session."
        )

    st.session_state.summary_generated = True


def render_workout_dashboard(history_rows):
    render_section_header(
        "Workout Dashboard",
        "Your total training volume, weekly progress, and exercise mix.",
    )

    df = pd.DataFrame(
        [
            {
                "Exercise": row["exercise_name"],
                "Reps": row["reps"],
                "Sets": row["sets"],
                "Time (sec)": row["time"],
                "Form Score": row["form_score"] if "form_score" in row.keys() else 0,
                "Date": row["created_at"],
            }
            for row in history_rows
        ]
    )

    if df.empty:
        st.info("Complete a workout to unlock your dashboard.")
        return df

    df["Date"] = pd.to_datetime(df["Date"])
    total_workouts = len(df)
    total_reps = int(df["Reps"].sum())
    total_sets = int(df["Sets"].sum())
    total_time = int(df["Time (sec)"].sum())
    best_exercise = df.groupby("Exercise")["Reps"].sum().idxmax()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Workouts", total_workouts)
    col2.metric("Total Reps", total_reps)
    col3.metric("Total Sets", total_sets)
    col4.metric("Workout Time", f"{total_time // 60}m {total_time % 60}s")

    st.metric("Best Exercise by Reps", best_exercise)

    weekly = df.set_index("Date").resample("W")["Reps"].sum().reset_index()
    weekly["Week"] = weekly["Date"].dt.strftime("%b %d")
    st.markdown("##### Weekly Progress")
    st.line_chart(weekly, x="Week", y="Reps")

    distribution = df.groupby("Exercise", as_index=False)["Reps"].sum()
    st.markdown("##### Exercise Distribution")
    st.bar_chart(distribution, x="Exercise", y="Reps")

    return df


def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="wide"
    )
    load_environment()

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()
    bootstrap_gamification()

    if not render_login_wall():
        return 

    initial_session_defaults()

    setup_voice_pipeline()

    workout_started = st.session_state.get("workout_started", False)
    
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div class="sidebar-brand__kicker">Training OS</div>
                <div class="sidebar-brand__title">AI Gym Coach</div>
                <div class="sidebar-brand__caption">Live form intelligence, XP, and coaching.</div>
            </div>
            <div class="sidebar-card profile-card">
                <div class="profile-avatar">R</div>
                <div>
                    <div class="sidebar-card__label">Athlete</div>
                    <div class="sidebar-card__value">{safe_text(st.session_state.get("username", "Guest"))}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.title("🏋️‍♂️ Apna AI Coach")

        if st.session_state.username:
            st.caption(f"👤 Login as {st.session_state.username}")

        st.divider()

        progress = get_user_progress(st.session_state.get("user_id"))
        st.markdown(
            f"""
            <div class="sidebar-card sidebar-card--section">
                <div class="sidebar-card__label">Progression</div>
                <div class="sidebar-card__value">Level {progress['current_level']} | {progress['total_xp']} XP</div>
                <div class="sidebar-card__label">Streak: {progress['current_streak']} days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.session_state.debug_mode = st.toggle(
            "Advanced debug mode",
            value=st.session_state.get("debug_mode", False),
            help="Shows camera and detector internals for tuning rep counting.",
        )
        app_mode = st.radio(
            "Mode",
            ["Solo Workout", "Fitness Arena", "Dashboard / History"],
            key="app_mode",
        )

        if app_mode == "Solo Workout":
            st.markdown(
                """
                <div class="sidebar-card sidebar-card--section">
                    <div class="sidebar-card__label">Workout Plan</div>
                    <div class="sidebar-card__value">Choose your training target</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if app_mode == "Solo Workout" and not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            if plan_exercise == "Plank" and st.session_state.get("plan_reps", 10) < 30:
                st.session_state.plan_reps = 30

            st.caption("Minimum 1 set and 5 reps required. For plank, use at least 10 hold seconds.")

            plan_sets = st.number_input("Sets", min_value=1, max_value=50, key="plan_sets", step=1)

            if plan_exercise == "Plank":
                plan_reps = st.number_input("Hold seconds per set", min_value=10, max_value=180, key="plan_reps", step=5)
            else:
                plan_reps = st.number_input("Reps per Set", min_value=5, max_value=50, key="plan_reps", step=1)

            st.markdown("")

            start_session_button = st.button("Start Workout", width="stretch", key="start_session_button")

            if start_session_button:
                if plan_exercise not in DETECTOR_REGISTRY:
                    st.error("Detector not available for this exercise yet.")
                    st.stop()

                reset_workout_state(plan_exercise, plan_sets, plan_reps)

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )
                    
                    queue_voice_feedback(result)

                st.rerun()
        elif workout_started:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            label = "Hold seconds" if exercise == "Plank" else "Reps"
            st.info(f"**{exercise}** -- {sets} Sets / {reps} {label}")
            st.session_state.show_pose_overlay = st.toggle(
                "Show pose guide lines",
                value=st.session_state.get("show_pose_overlay", False),
                help="Turn this on only when debugging body landmark detection.",
            )

            end_session_button = st.button("End Workout", key="end_session_button", width="stretch")

            if end_session_button:
                workout_result = complete_workout_session(exercise)
                if st.session_state.get("arena_room_id"):
                    room = get_room(st.session_state.arena_room_id)
                    if room:
                        status = "cancelled" if workout_result and workout_result.get("cancelled") else "completed"
                        metrics = {
                            "reps": int(st.session_state.get("reps", 0) or 0),
                            "sets_completed": int(st.session_state.get("sets_completed", 0) or 0),
                            "hold_seconds": int(st.session_state.get("hold_seconds", 0) or 0),
                            "form_score": int(st.session_state.get("average_form_score") or st.session_state.get("form_score", 0) or 0),
                        }
                        upsert_room_score(
                            room,
                            st.session_state.user_id,
                            st.session_state.username,
                            metrics,
                            status=status,
                        )
                        add_room_event(
                            room["id"],
                            st.session_state.user_id,
                            status,
                            f"{st.session_state.username} {'cancelled' if status == 'cancelled' else 'finished'} their workout.",
                        )
                    st.session_state.room_mode_active = False
                generate_session_summary(exercise)
                st.session_state.workout_started = False
                
                if workout_result and workout_result.get("cancelled"):
                    st.session_state.coach_feedback = "Workout cancelled. I did not detect enough movement to save this session."
                elif st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={}
                    )
                    queue_voice_feedback(result)

                st.rerun()

        if workout_started:
            st.divider()

            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets")

            st.markdown(
                """
                <div class="sidebar-card sidebar-card--section">
                    <div class="sidebar-card__label">Progress</div>
                    <div class="sidebar-card__value">Live session stats</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.metric("Total Reps", f"{total_reps}")
            if exercise == "Plank":
                st.metric("Hold Time", f"{st.session_state.get('hold_seconds', 0)}s")
                st.metric("Current Hold", f"{current_set_reps} / {reps_per_set}s")
                st.metric("Target Hold", f"{reps_per_set}s")
            else:
                st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")
            st.metric("Form Score", f"{st.session_state.get('form_score', 0)} / 100")
            st.metric("Camera Status", st.session_state.get("camera_status", "Camera loading"))
            st.metric("Current Stage", st.session_state.get("detector_stage", "setup"))

            if st.session_state.get("debug_mode", False):
                st.markdown("##### Detector Debug")
                st.caption(f"Selected detector: {exercise}")
                st.caption(f"Landmark confidence: {st.session_state.get('landmark_confidence', 0)}")
                st.caption(f"Processing: {st.session_state.get('processing_status', 'waiting')}")
                st.caption(f"Guidance: {st.session_state.get('camera_guidance', '')}")
                st.caption(f"Form score: {st.session_state.get('form_score', 0)}")
                st.caption(f"Issue: {st.session_state.get('detector_issue') or 'None'}")
                st.caption(f"Hold seconds: {st.session_state.get('hold_seconds', 0)}")
                st.caption(f"Valid rep: {st.session_state.get('is_valid_rep', False)}")
                st.json(st.session_state.get("detector_debug", {}))
                if st.session_state.get("frame_error"):
                    st.warning(st.session_state.frame_error)

            st.divider()

            if exercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            elif exercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Biceps Curls (Dumbbell)":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)

            elif exercise == "Jumping Jacks":
                st.subheader("Jumping Jack Metrics")
                st.metric("Arm Status", st.session_state.arm_status)
                st.metric("Foot Status", st.session_state.foot_status)
                st.metric("Stage", st.session_state.jumping_jack_stage)

            elif exercise == "High Knees":
                st.subheader("High Knee Metrics")
                st.metric("Knee Height", st.session_state.knee_height)
                st.metric("Pace", st.session_state.pace_status)
                st.metric("Active Knee", st.session_state.active_knee)

            elif exercise == "Crunches":
                st.subheader("Crunch Metrics")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Range", st.session_state.range_status)
                st.metric("Neck", st.session_state.neck_status)

            elif exercise == "Sit-ups":
                st.subheader("Sit-up Metrics")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Range", st.session_state.range_status)
                st.metric("Control", st.session_state.control_status)

            elif exercise == "Plank":
                st.subheader("Plank Metrics")
                st.metric("Hold Time", f"{st.session_state.hold_seconds}s")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Mountain Climbers":
                st.subheader("Mountain Climber Metrics")
                st.metric("Knee Drive", st.session_state.knee_drive)
                st.metric("Hip Position", st.session_state.hip_status)
                st.metric("Active Knee", st.session_state.active_knee)

    if st.session_state.get("audio_to_play") and not st.session_state.get("audio_played", False):
        autoplay_audio(st.session_state.audio_to_play)

    if workout_started:
        render_workout_header()
        render_active_workout_grid()
        render_camera_setup_tips()
        render_technique_card(st.session_state.get("exercise_type", "Squats"))

    if st.session_state.get("coach_feedback"):
        render_coach_card(st.session_state.coach_feedback)

    if st.session_state.get("session_summary") and not workout_started:
        render_session_summary(st.session_state.session_summary)

    if st.session_state.get("gamification_result") and not workout_started:
        render_reward_screen(st.session_state.gamification_result)

    if app_mode == "Fitness Arena":
        render_fitness_arena()
    elif not workout_started and app_mode == "Solo Workout":
        render_start_screen()
        render_exercise_tutorial(st.session_state.get("plan_exercise", "Squats"))

    if workout_started:
        exercise_key = st.session_state.get("exercise_type", "exercise").lower()
        exercise_key = "".join(ch if ch.isalnum() else "-" for ch in exercise_key).strip("-")

        try:
            context = webrtc_streamer(
                key=f"exercise-analysis-{exercise_key}",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=VideoProcessorClass,
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                media_stream_constraints={
                    "video": {
                        "width": {"ideal": 960},
                        "height": {"ideal": 540},
                        "frameRate": {"ideal": 30, "max": 60},
                    },
                    "audio": False
                },
                async_processing=True
            )
        except Exception as exc:
            st.error(f"Camera/WebRTC failed to start: {exc}")
            st.info("Check browser camera permission, close other apps using the webcam, then restart the workout.")
            st.session_state.camera_status = "Camera permission blocked"
            context = None

        if context and getattr(context, "video_processor", None):
            context.video_processor.set_draw_pose_overlay(st.session_state.get("show_pose_overlay", False))

        sync_metrics_update(context)

        if context and not context.state.playing:
            st.session_state.camera_status = "Camera stopped"
            st.info("Camera is not streaming yet. Click Start in the camera panel and allow browser camera permission.")
        elif context and context.state.playing:
            st.session_state.camera_status = st.session_state.get("camera_status", "Camera active")

        if context and context.state.playing and time.time() >= st.session_state.get("audio_pause_until", 0.0):
            time.sleep(1.0)
            st.rerun()

        inject_webrtc_styles()

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int) and app_mode == "Dashboard / History":
        st.divider()
        render_gamification_dashboard(user_id)
        st.divider()

        history_rows = get_users_exercises(user_id)
        render_workout_dashboard(history_rows)

        st.divider()
        render_section_header(
            "Workout History",
            "Your saved sessions remain available below with average form score.",
        )

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": row['time'],
                "Form Score": row["form_score"] if "form_score" in row.keys() else 0,
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": 'sum',
                "Sets": "sum",
                "Time (sec)": "sum",
                "Form Score": "mean"
            }).reset_index()
            agg_df["Form Score"] = agg_df["Form Score"].round(0).astype(int)
            agg_df.index += 1
            st.table(agg_df, border="horizontal")
        else:
            st.info("No workout history found.")


if __name__ == "__main__":
    main()
