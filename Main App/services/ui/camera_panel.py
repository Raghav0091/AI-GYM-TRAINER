import time

import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from services.vision.exercise_video_processor import VideoProcessorClass


CAMERA_QUALITY_PRESETS = {
    "Low": {"width": 640, "height": 360, "frameRate": 20},
    "Standard": {"width": 640, "height": 480, "frameRate": 24},
    "High": {"width": 1280, "height": 720, "frameRate": 30},
}


def camera_constraints(quality="Standard"):
    preset = CAMERA_QUALITY_PRESETS.get(quality, CAMERA_QUALITY_PRESETS["Standard"])
    return {
        "video": {
            "width": {"ideal": preset["width"]},
            "height": {"ideal": preset["height"]},
            "frameRate": {"ideal": preset["frameRate"], "max": 30},
        },
        "audio": False,
    }


def stable_webrtc_key(mode="solo", room_id=None):
    if mode == "room" and room_id:
        return f"webrtc-room-{room_id}"

    return "webrtc-solo-workout"


def render_workout_camera(exercise_name, mode="solo", room_id=None, quality="Standard", draw_pose_overlay=False):
    """Render one stable WebRTC camera component for the active workout.

    Future realtime backends should keep this camera local and only sync derived
    metrics through a room service, Supabase Realtime, or FastAPI WebSocket layer.
    """
    key = stable_webrtc_key(mode, room_id)
    st.session_state.webrtc_key_used = key
    st.session_state.selected_exercise_locked = exercise_name
    st.session_state.camera_quality_used = quality

    try:
        context = webrtc_streamer(
            key=key,
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints=camera_constraints(quality),
            async_processing=True,
        )
    except Exception as exc:
        st.session_state.camera_state = "error"
        st.session_state.camera_status = "Camera/WebRTC failed"
        st.session_state.camera_last_error = str(exc)
        st.error(f"Camera/WebRTC failed to start: {exc}")
        render_camera_troubleshooting()
        return None

    processor = getattr(context, "video_processor", None) if context else None

    if processor:
        processor.set_exercise(exercise_name)
        processor.set_draw_pose_overlay(draw_pose_overlay)
        st.session_state.camera_processor_class = processor.__class__.__name__

        snapshot = processor.get_debug_snapshot()
        st.session_state.last_frame_timestamp = snapshot.get("last_frame_at", 0.0)
        st.session_state.camera_fps_estimate = snapshot.get("fps", 0.0)
        st.session_state.camera_last_error = snapshot.get("last_error", "")

    if context and context.state.playing:
        st.session_state.camera_state = "active"
        st.session_state.workout_state = "workout_active"
        st.session_state.camera_status = st.session_state.get("camera_status", "Camera active")
    else:
        st.session_state.camera_state = "waiting"
        if st.session_state.get("workout_state") == "starting_camera":
            st.session_state.camera_status = "Waiting for camera permission"
        st.info("Camera is waiting. Click Start in the camera panel and allow browser camera permission.")

    return context


def render_camera_troubleshooting():
    st.markdown(
        """
        <div class="camera-troubleshooting">
            <h4>Camera Troubleshooting</h4>
            <ol>
                <li>Allow browser camera permission.</li>
                <li>Close other apps using the webcam.</li>
                <li>Refresh the page once.</li>
                <li>Use Chrome or Edge.</li>
                <li>Stand 2-3 meters away.</li>
                <li>Use good lighting.</li>
                <li>Try Standard camera quality instead of High.</li>
                <li>End the workout before switching exercise.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_camera_debug_panel(context=None):
    processor = getattr(context, "video_processor", None) if context else None
    snapshot = processor.get_debug_snapshot() if processor else {}
    playing = bool(context and getattr(context, "state", None) and context.state.playing)

    st.markdown("##### Camera Debug")
    st.caption(f"Workout state: {st.session_state.get('workout_state', 'idle')}")
    st.caption(f"Camera state: {st.session_state.get('camera_state', 'idle')}")
    st.caption(f"WebRTC playing: {playing}")
    st.caption(f"Selected exercise: {st.session_state.get('exercise_type', 'N/A')}")
    st.caption(f"Detector class: {snapshot.get('detector_class') or st.session_state.get('camera_processor_class', 'N/A')}")
    st.caption(f"Last frame: {_format_age(snapshot.get('last_frame_at'))}")
    st.caption(f"FPS estimate: {snapshot.get('fps', st.session_state.get('camera_fps_estimate', 0.0))}")
    st.caption(f"Last metrics update: {_format_age(st.session_state.get('last_ui_metrics_update'))}")
    st.caption(f"Last room score update: {_format_age(st.session_state.get('last_room_score_update'))}")
    st.caption(f"Last DB write: {_format_age(st.session_state.get('last_db_write'))}")
    st.caption(f"Last voice feedback: {_format_age(st.session_state.get('last_voice_feedback'))}")
    st.caption(f"WebRTC key: {st.session_state.get('webrtc_key_used', 'N/A')}")

    last_error = snapshot.get("last_error") or st.session_state.get("camera_last_error") or st.session_state.get("frame_error")
    if last_error:
        st.warning(last_error)


def _format_age(timestamp):
    if not timestamp:
        return "never"

    try:
        return f"{max(0.0, time.time() - float(timestamp)):.1f}s ago"
    except (TypeError, ValueError):
        return "unknown"
