from io import BytesIO
from gtts import gTTS


class TextToSpeech:
    def __init__(self):
        self.last_error = None

    def speak(self, text, lang="en"):
        cleaned = (text or "").strip()

        if not cleaned:
            return
        
        try:
            buffer = BytesIO()

            gTTS(text=cleaned, lang=lang).write_to_fp(buffer)

            buffer.seek(0)
            self.last_error = None

            return buffer.read()
        except Exception as exc:
            self.last_error = str(exc)
            return None
