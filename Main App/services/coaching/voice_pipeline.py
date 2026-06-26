import time
import streamlit as st


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    def _find_form_issue(self, exercise, metrics):
        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)
            
            if depth == "TOO HIGH":
                return "The user's squat is not deep enough. Knees are not bending sufficiently."

            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")
            
            if alignment == "Poor Form":
                return "The user's body is not straight during the push-up."

            if hip_status == "SAGGING":
                return "The user's hips are sagging down during the push-up."

            if hip_status == "PIKED UP":
                return "The user's hips are too high. Lower them to form a straight line."

        elif exercise == "Plank":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")

            if alignment == "POOR FORM":
                return "Your plank line is breaking. Brace your core, squeeze your glutes, and make a straight line from shoulders to ankles."

            if hip_status == "SAGGING":
                return "Your hips are sagging in the plank. Lift them slightly to protect your lower back and keep your core active."

            if hip_status == "PIKED UP":
                return "Your hips are too high in the plank. Lower them until your body forms one strong straight line."

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)

        now = time.time()

        allowed_events = {"workout_started", "set_completed", "workout_completed", "major_form_issue"}
        if event not in allowed_events:
            return None

        is_major_issue = event in ["workout_started", "set_completed", "workout_completed"]

        if not is_major_issue:
            if not issue:
                return None
            
            if now - self.last_spoken_at < 15:
                return None
            
        try:
            text = self.llm.give_feedback(event, issue)
        except Exception as exc:
            st.error(f"Groq voice coach failed: {exc}")
            return None

        voice = self.tts.speak(text)

        if voice is None and getattr(self.tts, "last_error", None):
            st.error(f"gTTS voice playback failed: {self.tts.last_error}")

        self.last_spoken_at = now

        return voice, text


def queue_voice_feedback(result):
    if not result:
        return

    audio_bytes, feedback_text = result
    st.session_state.coach_feedback = feedback_text

    if audio_bytes:
        st.session_state.audio_to_play = audio_bytes
        st.session_state.audio_played = False
    else:
        st.session_state.audio_to_play = None
        st.session_state.audio_played = True
    

def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return
    
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    st.session_state.audio_played = True
    st.session_state.audio_pause_until = time.time() + 6
