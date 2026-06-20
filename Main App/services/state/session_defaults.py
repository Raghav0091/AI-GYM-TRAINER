import streamlit as st


def initial_session_defaults():
    defaults = {
        "reps": 0,
        "target_sets": 0,
        "reps_per_set": 0,
        "sets_completed": 0,
        "current_set_reps": 0,
        "workout_complete": False,
        "last_notified_sets_completed": 0,
        "last_notified_workout_complete": False,
        "last_saved_sets_completed": 0,
        "set_cycle_started_at": 0.0,
        "last_exercise_type": "Squats",
        "form_score": 0,
        "form_score_total": 0,
        "form_score_samples": 0,
        "average_form_score": 0,
        "session_summary": "",
        "summary_generated": False,
        "audio_to_play": None,
        "coach_feedback": "",
        "audio_played": True,
        "audio_pause_until": 0.0,
        "gamification_result": None,
        "gamification_processed": False,
        "workout_started_at": 0.0,
        "show_pose_overlay": False,
        "debug_mode": False,
        "camera_status": "Camera loading",
        "landmark_confidence": 0.0,
        "camera_guidance": "Allow camera permission in your browser. Make sure your full body is visible.",
        "processing_status": "waiting",
        "detector_stage": "setup",
        "frame_error": "",
        "detector_issue": None,
        "is_valid_rep": False,
        "detector_debug": {},
        "app_mode": "Solo Workout",
        "arena_room_id": None,
        "arena_room_code": "",
        "room_mode_active": False,
        "last_room_score_snapshot": None,

        # Workout plan (set before starting)
        "workout_started": False,
        "plan_exercise": "Squats",
        "plan_sets": 3,
        "plan_reps": 10,

        # Common Angles
        "knee_angle": 0,
        "back_angle": 0,
        "elbow_angle": 0,
        "front_knee_angle": 0,
        "torso_angle": 0,

        # Status fields
        "depth_status": "N/A",
        "body_alignment": "N/A",
        "hip_status": "N/A",
        "shoulder_status": "N/A",
        "swing_status": "N/A",
        "extension_status": "N/A",
        "back_arch_status": "N/A",
        "balance_status": "N/A",
        "arm_status": "N/A",
        "foot_status": "N/A",
        "jumping_jack_stage": "N/A",
        "knee_height": "N/A",
        "pace_status": "N/A",
        "active_knee": "N/A",
        "range_status": "N/A",
        "neck_status": "N/A",
        "control_status": "N/A",
        "hold_seconds": 0,
        "knee_drive": "N/A",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
