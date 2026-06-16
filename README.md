# AI Real-time Gym Coach

AI Real-time Gym Coach is a Streamlit fitness app that uses your webcam to track exercise form, count reps, store workout history, and provide AI coaching feedback.

## Features

- Real-time pose detection with MediaPipe
- Exercise detectors for squats, push-ups, biceps curls, shoulder press, and lunges
- Rep and set counting
- Form score out of 100 during workouts
- AI voice coaching with Groq and gTTS
- AI session summary when a workout ends
- SQLite workout history
- Dashboard with totals, best exercise, weekly progress, and exercise distribution

## Tech Stack

- Python 3.11
- Streamlit
- streamlit-webrtc
- MediaPipe
- OpenCV
- pandas
- SQLite
- Groq
- gTTS
- python-dotenv

## Setup

Use Python 3.11. MediaPipe does not currently support every new Python release, and Python 3.13 commonly causes install errors.

```powershell
cd "C:\Apna_colleage Projects\ai-gym-coach-main\Main App"
python -m venv AI_gym
AI_gym\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root or inside `Main App`.

```env
GROQ_API_KEY=your_groq_api_key_here
```

Do not commit `.env`. It is already ignored by Git.

## Run the App

```powershell
cd "C:\Apna_colleage Projects\ai-gym-coach-main\Main App"
AI_gym\Scripts\activate
streamlit run main.py
```

Then open the local Streamlit URL shown in the terminal.

## Common Errors

- `mediapipe` install fails: use Python 3.11 instead of Python 3.13.
- VS Code uses the wrong interpreter: select the `AI_gym` virtual environment from the Python interpreter picker.
- Missing `GROQ_API_KEY`: AI voice coaching and AI summaries will be disabled, but the app will still run.
- Camera does not start: allow browser camera permissions and close other apps using the webcam.
- gTTS fails: check your internet connection. The app keeps working without voice playback.

## Screenshots

Add screenshots here:

- Workout screen
- Form score sidebar
- Dashboard
- Workout history
