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
from groq import Groq
from dotenv import find_dotenv, load_dotenv
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech

from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio, queue_voice_feedback


def safe_text(value):
    return html.escape(str(value))


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
    st.markdown(
        """
        <section class="hero">
            <div class="hero-badge">AI FITNESS COACH</div>
            <h1>Train Smarter.<br>Move Better.<br>Track Everything.</h1>
            <p>
                Real-time AI powered workout analysis with voice coaching.
            </p>
            <div class="callout">
                Build your workout plan in the sidebar, start the camera, and let AI coach every rep.
            </div>
        </section>
        <div class="feature-grid">
            <div class="glass-card feature-card">
                <div class="feature-icon">AI</div>
                <h3>AI Voice Coach</h3>
                <p>Short, focused coaching cues while you train.</p>
            </div>
            <div class="glass-card feature-card">
                <div class="feature-icon">100</div>
                <h3>Form Score</h3>
                <p>Live movement quality scoring for every session.</p>
            </div>
            <div class="glass-card feature-card">
                <div class="feature-icon">UP</div>
                <h3>Progress Tracking</h3>
                <p>See your reps, sets, time, and weekly trends.</p>
            </div>
            <div class="glass-card feature-card">
                <div class="feature-icon">REP</div>
                <h3>Real-time Rep Counter</h3>
                <p>Automatic counting through live pose detection.</p>
            </div>
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

    st.markdown(
        f"""
        <div class="workout-card">
            <div class="workout-card__row">
                <div>
                    <div class="section-kicker">Workout Active</div>
                    <h2>{safe_text(exercise)}</h2>
                    <p>{sets_completed} / {target_sets} sets completed | {reps} total reps</p>
                </div>
                <div class="score-pill">Form Score {form_score} / 100</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_active_workout_grid():
    exercise = st.session_state.get("exercise_type", "Workout")
    total_reps = st.session_state.get("reps", 0)
    sets_completed = st.session_state.get("sets_completed", 0)
    target_sets = st.session_state.get("target_sets", 0)
    form_score = st.session_state.get("form_score", 0)

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
                <span>Reps</span>
                <strong>{total_reps}</strong>
            </div>
            <div class="active-card">
                <span>Sets</span>
                <strong>{sets_completed}/{target_sets}</strong>
            </div>
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
    st.session_state.form_score = 0
    st.session_state.form_score_total = 0
    st.session_state.form_score_samples = 0
    st.session_state.average_form_score = 0
    st.session_state.session_summary = ""
    st.session_state.summary_generated = False
    st.session_state.audio_to_play = None
    st.session_state.coach_feedback = ""
    st.session_state.audio_played = True
    st.session_state.audio_pause_until = 0.0
    st.session_state.workout_started = True
    st.session_state.set_cycle_started_at = time.time()
    st.session_state.last_saved_sets_completed = 0
    st.session_state.last_notified_sets_completed = 0
    st.session_state.last_notified_workout_complete = False


def generate_session_summary(exercise):
    if st.session_state.get("summary_generated"):
        return

    sets_completed = st.session_state.get("sets_completed", 0)
    total_reps = st.session_state.get("reps", 0)
    form_score = st.session_state.get("average_form_score") or st.session_state.get("form_score", 0)
    pipeline = st.session_state.get("voice_pipeline")

    if not pipeline:
        st.session_state.session_summary = (
            f"AI summary unavailable because GROQ_API_KEY is missing. "
            f"{exercise}: {sets_completed} sets, {total_reps} reps, form score {form_score}/100."
        )
        st.session_state.summary_generated = True
        return

    try:
        st.session_state.session_summary = pipeline.llm.summarize_session(
            exercise=exercise,
            sets_completed=sets_completed,
            total_reps=total_reps,
            form_score=form_score,
        )
    except Exception as exc:
        st.warning(f"AI session summary failed: {exc}")
        st.session_state.session_summary = (
            f"{exercise}: {sets_completed} sets, {total_reps} reps, form score {form_score}/100. "
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
        layout="centered"
    )
    load_environment()

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return 

    initial_session_defaults()

    setup_voice_pipeline()

    workout_started = st.session_state.get("workout_started", False)
    
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand">
                <div class="sidebar-brand__kicker">Premium Training</div>
                <div class="sidebar-brand__title">AI Gym Coach</div>
                <div class="sidebar-brand__caption">Form intelligence for every rep.</div>
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

        st.markdown(
            """
            <div class="sidebar-card sidebar-card--section">
                <div class="sidebar-card__label">Workout Plan</div>
                <div class="sidebar-card__value">Choose your training target</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            st.caption("Minimum 1 set and 5 reps required.")

            plan_sets = st.number_input("Sets", min_value=1, max_value=50, key="plan_sets", step=1)

            plan_reps = st.number_input("Reps per Set", min_value=5, max_value=50, key="plan_reps", step=1)

            st.markdown("")

            start_session_button = st.button("Start Workout", width="stretch", key="start_session_button")

            if start_session_button:
                reset_workout_state(plan_exercise, plan_sets, plan_reps)

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )
                    
                    queue_voice_feedback(result)

                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Workout", key="end_session_button", width="stretch")

            if end_session_button:
                generate_session_summary(exercise)
                st.session_state.workout_started = False
                
                if st.session_state.voice_pipeline:
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
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")
            st.metric("Form Score", f"{st.session_state.get('form_score', 0)} / 100")

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

    if st.session_state.get("coach_feedback"):
        render_coach_card(st.session_state.coach_feedback)

    if st.session_state.get("session_summary") and not workout_started:
        render_session_summary(st.session_state.session_summary)

    if not workout_started:
        render_start_screen()
        render_exercise_tutorial(st.session_state.get("plan_exercise", "Squats"))
    else:
        exercise_key = st.session_state.get("exercise_type", "exercise").lower()
        exercise_key = "".join(ch if ch.isalnum() else "-" for ch in exercise_key).strip("-")

        try:
            context = webrtc_streamer(
                key=f"exercise-analysis-{exercise_key}",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=VideoProcessorClass,
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                media_stream_constraints={
                    "video": True,
                    "audio": False
                },
                async_processing=True
            )
        except Exception as exc:
            st.error(f"Camera/WebRTC failed to start: {exc}")
            st.info("Check browser camera permission, close other apps using the webcam, then restart the workout.")
            context = None

        sync_metrics_update(context)

        if context and not context.state.playing:
            st.info("Camera is not streaming yet. Click Start in the camera panel and allow browser camera permission.")

        if context and context.state.playing and time.time() >= st.session_state.get("audio_pause_until", 0.0):
            time.sleep(1.0)
            st.rerun()

        inject_webrtc_styles()

    st.divider()

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
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
