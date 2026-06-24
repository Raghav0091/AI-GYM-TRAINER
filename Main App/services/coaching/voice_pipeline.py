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
                return "The user's squat is not deep enough — knees are not bending sufficiently."

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
                return "The user's hips are too high — lower them to form a straight line."

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")
            
            if swing == "SWINGING":
                return "The user is swinging their torso during the curl — keep the body still."

            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from their side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            extension = metrics.get("extension_status", "")
            
            if back_arch == "Excessive Arch":
                return "The user is arching their lower back excessively during the press."

            if back_arch == "Slight Arch":
                return "Slight back arch detected — encourage the user to brace their core."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")
            
            if balance == "OFF BALANCE":
                return "The user is losing balance during the lunge — feet should be hip-width apart."

        elif exercise == "Jumping Jacks":
            arms = metrics.get("arm_status", "")
            feet = metrics.get("foot_status", "")

            if arms == "RAISE ARMS":
                return "Your arms are not reaching overhead. Raise your hands higher so each rep uses your shoulders and keeps the rhythm strong."

            if feet == "FEET TOGETHER":
                return "Your feet are not opening wide enough. Jump to a wider stance, land softly, and keep the movement light."

        elif exercise == "High Knees":
            knee_height = metrics.get("knee_height", "")

            if knee_height == "LOW KNEES":
                return "Your knees are staying low. Drive each knee closer to hip height to build intensity and engage your core."

        elif exercise == "Crunches":
            crunch_range = metrics.get("range_status", "")
            neck = metrics.get("neck_status", "")

            if crunch_range == "LOW RANGE":
                return "Your crunch range is a little short. Lift your shoulders higher with control so your abs do more of the work."

            if neck == "CHECK POSITION":
                return "Your neck position is hard to read. Keep your chin slightly tucked and lift from your ribs, not your head."

        elif exercise == "Sit-ups":
            situp_range = metrics.get("range_status", "")

            if situp_range == "LOW RANGE":
                return "Your sit-up range is short. Curl higher toward your thighs with control so your core works through a fuller range."

        elif exercise == "Plank":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")

            if alignment == "POOR FORM":
                return "Your plank line is breaking. Brace your core, squeeze your glutes, and make a straight line from shoulders to ankles."

            if hip_status == "SAGGING":
                return "Your hips are sagging in the plank. Lift them slightly to protect your lower back and keep your core active."

            if hip_status == "PIKED UP":
                return "Your hips are too high in the plank. Lower them until your body forms one strong straight line."

        elif exercise == "Mountain Climbers":
            knee_drive = metrics.get("knee_drive", "")
            hip_status = metrics.get("hip_status", "")

            if knee_drive == "LOW DRIVE":
                return "Your knee drive is short. Pull each knee closer toward your chest while keeping your shoulders stacked over your hands."

            if hip_status == "HIPS HIGH":
                return "Your hips are rising during mountain climbers. Keep your plank lower and stable so the core does more work."
        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)

        now = time.time()

        allowed_events = {"workout_started", "set_completed", "workout_completed", "major_form_issue", "achievement_unlocked"}
        if event not in allowed_events:
            return None

        is_major_issue = event in ["workout_started", "set_completed", "workout_completed", "achievement_unlocked"]

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
