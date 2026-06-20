import streamlit as st
import time
from services.config.workout_config import METRICS_FIELDS
from services.persistence.exercise_repository import add_exercise
from services.tracking.form_score import update_form_score_state
from services.coaching.voice_pipeline import queue_voice_feedback
from services.multiplayer.room_service import add_room_event, get_room, maybe_mark_race_winner
from services.multiplayer.score_service import should_update_room_score, upsert_room_score


def sync_metrics_update(context):
    if not context or not hasattr(context, "state") or not context.state.playing:
        return
    
    processor = getattr(context, "video_processor", None)

    if not processor:
        return 
    
    exercise = st.session_state.get("exercise_type")

    if not exercise:
        return
    
    processor.set_exercise(exercise)
    latest_metrics = processor.get_latest_metrics()

    if not latest_metrics:
        return

    st.session_state.camera_status = latest_metrics.get("camera_status", "Camera active")
    st.session_state.detector_stage = latest_metrics.get("stage", st.session_state.get("detector_stage", "setup"))
    st.session_state.landmark_confidence = latest_metrics.get("landmark_confidence", st.session_state.get("landmark_confidence", 0.0))
    st.session_state.camera_guidance = latest_metrics.get("camera_guidance", st.session_state.get("camera_guidance", "Keep your full body visible."))
    st.session_state.processing_status = latest_metrics.get("processing_status", st.session_state.get("processing_status", "tracking"))
    st.session_state.frame_error = latest_metrics.get("frame_error", "")
    st.session_state.detector_issue = latest_metrics.get("issue")
    st.session_state.is_valid_rep = latest_metrics.get("is_valid_rep", False)
    st.session_state.detector_debug = latest_metrics.get("debug", {})
    
    reps = latest_metrics.get("reps", 0)
    hold_seconds = int(latest_metrics.get("hold_seconds", 0) or 0)

    if reps is None:
        reps = 0
        
    st.session_state.reps = 0 if exercise == "Plank" else reps
    st.session_state.hold_seconds = hold_seconds

    fields = METRICS_FIELDS.get(exercise)

    if not fields:
        return 

    for key, default in fields.items():
        st.session_state[key] = latest_metrics.get(key, default)

    live_form_score = update_form_score_state(exercise, latest_metrics)
    st.session_state.detector_debug = {
        **st.session_state.get("detector_debug", {}),
        "form_score": live_form_score,
    }

    reps_per_set = st.session_state.get("reps_per_set", 0)
    target_sets = st.session_state.get("target_sets", 0)

    if exercise == "Plank" and reps_per_set > 0 and target_sets > 0:
        sets_completed = hold_seconds // reps_per_set
        current_set_reps = hold_seconds % reps_per_set
        workout_completed = sets_completed >= target_sets
    elif reps is not None and reps_per_set > 0 and target_sets > 0:
        sets_completed = reps // reps_per_set
        current_set_reps = reps % reps_per_set
        workout_completed = sets_completed >= target_sets 
    else:
        sets_completed = 0
        current_set_reps = 0
        workout_completed = False

    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed
    st.session_state.detector_debug = {
        **st.session_state.get("detector_debug", {}),
        "valid_workout": _is_current_workout_valid(exercise),
    }
    _sync_room_score_if_needed(exercise, latest_metrics)

    last_saved_sets = st.session_state.get("last_saved_sets_completed", 0)

    if target_sets > 0 and reps_per_set > 0 and sets_completed > last_saved_sets:
        newly_completed = sets_completed - last_saved_sets
        now_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at", now_ts)
        time_taken = now_ts - started_at
        user_id = st.session_state.get("user_id", 0)

        add_exercise(
            user_id,
            exercise,
            0 if exercise == "Plank" else newly_completed * reps_per_set,
            newly_completed,
            time_taken,
            st.session_state.get("average_form_score", 0),
        )

        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event="set_completed",
                exercise=exercise,
                metrics=latest_metrics,
            )

            queue_voice_feedback(result)

        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed

        if st.session_state.get("arena_room_id"):
            add_room_event(
                st.session_state.arena_room_id,
                st.session_state.get("user_id"),
                "set_completed",
                f"{st.session_state.get('username', 'Athlete')} completed Set {sets_completed}.",
            )

    if workout_completed and not st.session_state.get("last_notified_workout_complete", False):
        st.session_state.last_notified_workout_complete = True

        if st.session_state.get("voice_pipeline"):
            result = st.session_state.voice_pipeline.process_event(
                event="workout_completed",
                exercise=exercise,
                metrics=latest_metrics,
            )

            queue_voice_feedback(result)
                
    pose_detected = latest_metrics.get("pose_detected", True)
    
    if not pose_detected:
        st.session_state.camera_status = "Pose not detected"
        st.session_state.camera_guidance = latest_metrics.get("camera_guidance", "Move farther back so your full body is visible.")

    if not pose_detected and st.session_state.get("voice_pipeline"):
        result = st.session_state.voice_pipeline.process_event(
            event="no_pose_detected",
            exercise=exercise,
            metrics={"issue": "No pose detected! Please step into the camera frame."},
        )
    
        queue_voice_feedback(result)

    if st.session_state.get("voice_pipeline"):
        result = st.session_state.voice_pipeline.process_event(
            event="ongoing_form_check",
            exercise=exercise,
            metrics=latest_metrics,
        )
        
        queue_voice_feedback(result)


def _is_current_workout_valid(exercise):
    reps = int(st.session_state.get("reps", 0) or 0)
    sets_completed = int(st.session_state.get("sets_completed", 0) or 0)
    reps_per_set = int(st.session_state.get("reps_per_set", 0) or 0)
    hold_seconds = int(st.session_state.get("hold_seconds", 0) or 0)

    if exercise == "Plank":
        return hold_seconds >= 10 or sets_completed > 0

    return (reps > 0 and sets_completed > 0) or (reps_per_set > 0 and reps >= reps_per_set)


def _sync_room_score_if_needed(exercise, latest_metrics):
    room_id = st.session_state.get("arena_room_id")

    if not room_id or not st.session_state.get("room_mode_active"):
        return

    room = get_room(room_id)

    if not room or room["status"] != "active":
        return

    now_ts = time.time()
    metrics = {
        "reps": 0 if exercise == "Plank" else int(st.session_state.get("reps", 0) or 0),
        "sets_completed": int(st.session_state.get("sets_completed", 0) or 0),
        "hold_seconds": int(st.session_state.get("hold_seconds", 0) or 0),
        "form_score": int(st.session_state.get("average_form_score") or st.session_state.get("form_score", 0) or 0),
    }
    previous = st.session_state.get("last_room_score_snapshot")

    if not should_update_room_score(previous, metrics, exercise, now_ts):
        return

    upsert_room_score(
        room,
        st.session_state.get("user_id"),
        st.session_state.get("username", "Athlete"),
        metrics,
        status="active",
    )
    maybe_mark_race_winner(
        room,
        st.session_state.get("user_id"),
        st.session_state.get("username", "Athlete"),
        metrics,
    )
    st.session_state.last_room_score_snapshot = {**metrics, "updated_at": now_ts}
