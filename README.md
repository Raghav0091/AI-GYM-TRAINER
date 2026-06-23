# AI Real-time Gym Coach

AI Real-time Gym Coach is a Streamlit fitness app that uses your webcam to analyze exercise form, count reps, score movement quality, store workout history, and provide AI voice coaching.

Version 3 adds a game-style progression system so workouts feel more rewarding: earn XP, level up, unlock badges, protect streaks, complete daily challenges, and compare progress on a local leaderboard.

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
- XP, levels, streaks, achievements, personal records, and daily challenges
- Local leaderboard foundation for future multiplayer scoring
- AI Fitness Arena local multiplayer rooms with room codes and live leaderboard
- FastAPI backend foundation for production auth, workouts, rooms, and WebSocket score updates
- PostgreSQL and Redis architecture prepared through Docker Compose
- Exercise Intelligence Engine with pose normalization, heuristic auto-detect, and prediction smoothing

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
- FastAPI
- PostgreSQL
- Redis
- Docker Compose
- WebSockets

## Setup

Use Python 3.11. MediaPipe commonly fails on Python 3.13, so avoid Python 3.13 for this project.

```powershell
cd "C:\Apna_colleage Projects\ai-gym-coach-main\Main App"
python -m venv ..\AI_gym
..\AI_gym\Scripts\activate
uv pip install -r requirements.txt
```

If you are not using `uv`, install with `python -m pip install -r requirements.txt`.

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

## Streamlit Cloud Deployment

Use the root wrapper as the single public Streamlit entrypoint.

Streamlit Cloud settings:

- Repository: `Raghav0091/AI-GYM-TRAINER`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: `3.11` from Advanced settings
- Requirements file: root `requirements.txt`
- Linux packages file: root `packages.txt`

Secrets:

```toml
GROQ_API_KEY = "your_key_here"
```

Do not set the main file path to `backend/main.py`.
Do not set the main file path to `Main App/main.py`.
Use `streamlit_app.py` so Streamlit Cloud does not need to handle the `Main App` folder space directly.

If Streamlit Cloud shows a `cv2` import error, reboot/redeploy the app after this root `packages.txt` is present. OpenCV and MediaPipe need Linux system packages such as `libgl1` and `libglib2.0-0` during deployment.

The backend dependency file is now `backend/backend-requirements.txt`. It is for the future FastAPI Docker service, not for Streamlit Cloud.

## Production Backend Foundation

Version 5.0 adds a new FastAPI backend beside the existing Streamlit app. The current Streamlit app still works locally with SQLite, but the backend prepares the project for real deployment.

Backend structure:

- `backend/app/main.py` FastAPI entrypoint
- `backend/app/core/` config, database, security
- `backend/app/models/` SQLAlchemy PostgreSQL models
- `backend/app/schemas/` Pydantic request/response schemas
- `backend/app/services/` auth, workout, room, leaderboard, Redis cache services
- `backend/app/routers/` REST and WebSocket routes

Backend endpoints:

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /workouts`
- `GET /workouts/{user_id}`
- `GET /workouts/{user_id}/summary`
- `POST /rooms/create`
- `POST /rooms/join/{room_code}`
- `POST /rooms/{room_code}/start`
- `POST /rooms/{room_code}/end`
- `GET /rooms/{room_code}`
- `GET /rooms/{room_code}/leaderboard`
- `WS /ws/rooms/{room_code}`

Install and run the backend locally with `uv`:

```powershell
cd "C:\Apna_colleage Projects\ai-gym-coach-main"
uv pip install -r backend\backend-requirements.txt --python .\AI_gym\Scripts\python.exe --system-certs
cd "C:\Apna_colleage Projects\ai-gym-coach-main\backend"
..\AI_gym\Scripts\python.exe -m uvicorn app.main:app --reload
```

Health check:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "ai-fitness-arena-backend"
}
```

## Docker Compose

Copy `.env.example` to `.env` and change secrets before deploying.

```powershell
cd "C:\Apna_colleage Projects\ai-gym-coach-main"
docker compose up --build
```

Docker Compose starts:

- `backend` FastAPI service on port `8000`
- `postgres` PostgreSQL database on port `5432`
- `redis` cache on port `6379`

Do not commit a real `.env` file.

## Login and Register

- Register with a unique username and password.
- Passwords are hashed before storing in SQLite.
- Existing local users without passwords are upgraded when they log in.
- The local SQLite database is ignored by Git and should not be pushed.

## Gamification System

The app now tracks progression in SQLite:

- `workout_sessions` stores completed workout summaries, XP, form score, and calories estimate.
- `user_progress` stores total XP, current level, streaks, workouts, reps, sets, and time.
- `achievements` and `user_achievements` store badge definitions and unlocks.
- `daily_challenges` and `user_daily_challenges` store one local challenge per day.
- `personal_records` stores best reps, best form score, longest workout, and plank hold records.

XP is awarded from workout completion, reps, sets, form score, streak bonuses, daily challenges, and achievement rewards.

Level progress uses a scalable formula:

```text
XP required for next level = 250 * current_level * 1.25
```

Default badges include First Workout, 100 Total Reps, 500 Total Reps, Squat Starter, Push-up Warrior, Consistency Rookie, Weekly Beast, Perfect Form, and Workout Grinder.

Daily challenges are generated locally from templates, so Groq is not required for challenge creation. Challenge rewards are only awarded once.

The local leaderboard ranks users on the same device by XP, reps, streaks, workouts, and best form score. The scoring service includes a future multiplayer hook for rooms, live scores, and team challenges later.

## AI Fitness Arena

AI Fitness Arena lets users create or join local workout rooms with a room code such as `GYM-742`.

Current room features:

- Create a room with name, exercise, targets, sets, and game mode.
- Join a room using a room code.
- Practice mode shows a live leaderboard without declaring a winner.
- Race mode declares the first player to hit the target reps or plank hold time.
- Team Challenge is a placeholder for a future update.
- Each user's webcam stays local. The app only stores workout metrics such as reps, sets, hold seconds, form score, and score.
- Room activity feed shows joins, starts, set completions, finishes, winners, and ended rooms.

This is a local SQLite prototype. It works best for testing multiple browser sessions on the same computer or same local app/database. It is not a true internet multiplayer backend yet.

Future real-time upgrade plan:

- Move rooms to Supabase PostgreSQL.
- Use Supabase Realtime presence to show online users.
- Use Supabase broadcasts or Postgres changes for low-latency leaderboard updates.
- Add a FastAPI WebSocket backend for scalable room channels.
- Build a React frontend later for smoother multiplayer UX.
- Add fitness games such as Squat Bird and Push-up Racer.

## Exercise Intelligence Engine

The Exercise Intelligence Engine adds DeepFit-style pose processing on top of the existing MediaPipe detectors.

Current flow:

1. MediaPipe finds body landmarks from the camera frame.
2. `pose_normalizer.py` extracts 18 important keypoints: nose, neck, shoulders, elbows, wrists, hips, knees, ankles, eyes, and ears.
3. The keypoints are normalized around the body center and body scale, producing a 36-value feature vector.
4. `exercise_classifier.py` uses safe geometry heuristics to estimate the exercise.
5. `prediction_smoother.py` looks at recent predictions so the app does not flicker between exercises.
6. The video processor runs the matching detector only when confidence is high enough.

Manual mode vs Auto Detect mode:

- Manual mode uses the exercise selected in the sidebar.
- Auto Detect mode predicts the exercise from body movement and switches detector after smoothing.
- If confidence is below `0.55`, the app shows `Unknown` and asks you to move farther back with your full body visible.

Current auto-detect limitations:

- It is a rule-based heuristic classifier, not a trained deep learning model yet.
- It works best when the full body is visible.
- Camera angle still matters. Side view is better for squats, push-ups, planks, lunges, sit-ups, crunches, and mountain climbers. Front view is better for jumping jacks, high knees, curls, and shoulder press.
- Very fast movement or low light can reduce confidence.

Future ML plan:

- Collect normalized pose samples with the developer-only `Enable Pose Data Collection` toggle.
- Store samples locally in `Main App/data/pose_samples/`, which is ignored by Git.
- Train future models for exercise classification, rep stage classification, and form quality classification.
- Add a future optional TFLite model at `Main App/ml_models/exercise_classifier.tflite`.
- If the TFLite file exists later, the classifier code has a hook where the heuristic logic can be replaced.

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

### Camera HTTPS Requirement

Browser camera APIs only work in secure contexts. Camera access works on:

- `http://localhost:8501`
- `https://deployed-domain.com`

Camera access may fail on:

- `http://192.168.x.x:8501`
- insecure remote URLs

If you see this error:

```text
navigator.mediaDevices is undefined
The current document is not loaded securely
```

that means the browser blocked camera access because the page is not loaded from `localhost` or HTTPS. For phone and multi-device testing, deploy with HTTPS using Streamlit Cloud, Caddy, NGINX, Cloudflare Tunnel, or another secure hosting option. Do not expect phone camera access to work over a plain HTTP LAN IP.

## Production Architecture Docs

See:

- `docs/architecture_explained.md`
- `docs/future_architecture.md`

These explain frontend/backend/API/database/cache/WebSocket concepts, why SQLite is not enough for production multiplayer, and how a future NGINX or Caddy gateway can route:

- `/` to Streamlit
- `/api/*` to FastAPI
- `/ws/*` to the WebSocket room service

## Common Issues

- MediaPipe install fails: use Python 3.11, not Python 3.13.
- VS Code uses the wrong interpreter: select the `AI_gym` virtual environment.
- Missing `GROQ_API_KEY`: add it to `.env`.
- gTTS fails: check internet access. The app continues without voice.
- Camera is blank: check browser permission and close other webcam apps.
- Room code not found: make sure the host created the room on the same local database.
- Leaderboard not updating: click Refresh Room, then make sure your camera workout is active and reps/hold time are changing.
- SQLite multiplayer is local-only. For real remote users, move the room services to Supabase or WebSockets.
- Auto detect says Unknown: move farther back, improve lighting, and keep your full body visible.
- Pose visibility is low: check camera angle, avoid cropped feet/hands, and turn on pose guide lines in debug mode.

## Camera Positioning

- Keep your full body visible in the frame.
- Stand about 2-3 meters away from the camera.
- Use bright, even lighting.
- Avoid very baggy clothing when landmarks are unstable.
- Use side view for squats, push-ups, lunges, planks, sit-ups, and mountain climbers.
- Use front view for shoulder press, curls, jumping jacks, and high knees.
- Turn on `Advanced debug mode` and `Show pose guide lines` only when tuning camera setup.

## Exercise Detection Limitations

The current system uses MediaPipe pose landmarks plus rule-based stage machines. It is not yet a custom trained rep-counting model. Very fast reps, poor lighting, partial body visibility, loose clothing, or a low-FPS webcam can still cause missed reps or false reps.

Recent improvements include:

- landmark visibility checks
- left/right side fallback
- rolling angle smoothing
- safer frame processing
- stage and confidence debug metrics
- more tolerant jumping-jack thresholds
- a standard detector output adapter so missing detector fields do not crash the app
- workout validation that cancels zero-rep or zero-hold sessions without awarding XP

## Plank Tracking

Plank is treated as a time-based exercise, not a rep-based exercise. The app tracks hold seconds, current hold progress, completed sets, body alignment, hip position, and form score. A plank workout must include at least 10 valid hold seconds or a completed hold set before XP is awarded.

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
- `.vscode/`
- `postgres_data/`
- `redis_data/`

## Future ML Roadmap

1. Current system: rule-based MediaPipe landmark detection.
2. Improve rules with smoothing, visibility checks, side fallback, and stage machines.
3. Collect labeled workout videos and per-frame landmark sequences.
4. Train a time-series model such as LSTM, GRU, TCN, or Transformer.
5. Train separate models for exercise recognition, rep stage classification, form issue classification, and form score prediction.
6. Add personalized calibration per user.
7. Evaluate using precision, recall, F1-score, missed-rep rate, and false-rep rate.

## Screenshots

Add screenshots here:

- Login/register screen
- Workout screen
- Tutorial card
- Form score sidebar
- Dashboard
- Workout history
- XP reward screen
- Achievements and leaderboard
