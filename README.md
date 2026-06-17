# AI Real-time Gym Coach

AI Real-time Gym Coach is a Streamlit fitness app that uses your webcam to analyze exercise form, count reps, score movement quality, store workout history, and provide AI voice coaching.

## Features

- Real-time pose detection with MediaPipe
- Webcam workout tracking through `streamlit-webrtc`
- Login/register with SQLite users and hashed passwords
- Rep and set counting
- Live form score out of 100
- Exercise tutorial cards with instructions, common mistakes, muscles, and demo videos
- Groq-powered AI coach feedback
- gTTS voice playback with visible debugging audio player
- SQLite workout history and dashboard charts

## Exercises

Current supported exercises:

- Squats
- Push-ups
- Biceps Curls (Dumbbell)
- Shoulder Press
- Lunges
- Jumping Jacks
- High Knees
- Crunches
- Sit-ups
- Plank
- Mountain Climbers

Each exercise has detector metrics, sidebar feedback, form scoring, and tutorial content. Demo videos use safe YouTube embed links when available; missing links fall back to a clean “Demo video coming soon” card.

## Tech Stack

- Python 3.11
- Streamlit
- streamlit-webrtc
- MediaPipe
- OpenCV
- pandas
- SQLite
- bcrypt
- Groq
- gTTS
- python-dotenv

## Setup

Use Python 3.11. MediaPipe commonly fails on Python 3.13, so avoid Python 3.13 for this project.

```powershell
cd "C:\Apna_colleage Projects\ai-gym-coach-main\Main App"
python -m venv ..\AI_gym
..\AI_gym\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root or inside `Main App`.

```env
GROQ_API_KEY=your_groq_api_key_here
```

If `GROQ_API_KEY` is missing, the app still runs, but AI voice coaching and AI summaries are disabled.

## Run the App

Always run from inside `Main App` so the app can find `static/` and `ml_models/`.

```powershell
cd "C:\Apna_colleage Projects\ai-gym-coach-main\Main App"
..\AI_gym\Scripts\python.exe -m streamlit run main.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Login and Register

- Register with a unique username and password.
- Passwords are hashed before storing in SQLite.
- Existing local users without passwords are upgraded when they log in.
- The local SQLite database is ignored by Git and should not be pushed.

## Camera Troubleshooting

- Run the app from `Main App`, not the repository root.
- Allow camera permission in your browser.
- Close Zoom, Teams, OBS, or any other app using the webcam.
- If the stream does not start, click the camera panel’s Start button.
- Try another port if Streamlit is already running:

```powershell
..\AI_gym\Scripts\python.exe -m streamlit run main.py --server.port 8502
```

- If WebRTC fails, the app shows a camera/WebRTC error message in the UI.

## Common Issues

- MediaPipe install fails: use Python 3.11, not Python 3.13.
- VS Code uses the wrong interpreter: select the `AI_gym` virtual environment.
- Missing `GROQ_API_KEY`: add it to `.env`.
- gTTS fails: check internet access. The app continues without voice.
- Camera is blank: check browser permission and close other webcam apps.

## Git Safety

Ignored files include:

- `.env`
- `*.env`
- `AI_gym/`
- `.venv/`
- `venv/`
- `__pycache__/`
- `*.pyc`
- `data.db`
- `*.db`
- `.streamlit/secrets.toml`

## ML Roadmap

- Stage 1: Rule-based MediaPipe detectors
- Stage 2: Better thresholds and smoothing
- Stage 3: Collect exercise data
- Stage 4: Train exercise classifier
- Stage 5: Train form-quality classifier
- Stage 6: Personalized calibration

## Screenshots

Add screenshots here:

- Login/register screen
- Workout screen
- Tutorial card
- Form score sidebar
- Dashboard
- Workout history
