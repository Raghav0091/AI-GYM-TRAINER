from services.config.workout_config import PROMPT


class LLMCoach:
    def __init__(self, groq_client):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT

    def give_feedback(self, event, issue):
        prompt = f"Event: {event}"

        if issue:
            prompt += f" Form Issue: {issue}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-10:],
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4,
            max_tokens=100,
        )

        text = response.choices[0].message.content.strip()
        self.history.append({"role": "assistant", "content": text})

        return text

    def summarize_session(self, exercise, sets_completed, total_reps, form_score):
        prompt = (
            "Create a short workout session summary for the app UI. "
            "Use 5 concise bullet lines covering: exercise name, sets completed, "
            "total reps, form score, strengths, improvement tips, and next-session suggestion.\n"
            f"Exercise: {exercise}\n"
            f"Sets completed: {sets_completed}\n"
            f"Total reps: {total_reps}\n"
            f"Form score: {form_score}/100"
        )

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=100,
        )

        return response.choices[0].message.content.strip()
