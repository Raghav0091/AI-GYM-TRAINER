# AI Gym Trainer

AI Gym Trainer is a Streamlit fitness coach that uses your webcam, MediaPipe Pose, and exercise-specific rules to count reps and give simple form feedback.

This public MVP is intentionally stable and manual-first. Auto exercise detection, multiplayer rooms, and the future FastAPI backend are kept out of the Streamlit app flow so camera tracking works reliably on local machines and Streamlit Cloud.

## MVP Features

- Manual exercise selection
- Webcam camera through `streamlit-webrtc`
- MediaPipe Pose skeleton detection
- Squat rep counter
- Push-up rep counter
- Plank hold timer
- Basic form score
- Workout summary
- Local SQLite workout history
- Optional login/register
- Optional Groq/gTTS voice coaching outside the live frame loop
- Dark fitness UI

## Supported Exercises

- Squats
- Push-ups
- Plank

## Tech Stack

- Python 3.11
- Streamlit
- streamlit-webrtc
- MediaPipe Pose
- OpenCV headless
- NumPy
- Pandas
- SQLite
- bcrypt
- Optional Groq and gTTS

## Setup With uv

Create and activate a Python 3.11 environment:

```powershell
uv venv AI_gym --python 3.11
.\AI_gym\Scripts\activate
uv pip install -r requirements.txt
```

MediaPipe does not support Python 3.13. Use Python 3.11 for this project.

## Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

The app still runs without `GROQ_API_KEY`, but AI voice coaching and AI summaries are disabled.

Never commit `.env`.

## Run Locally

From the project root:

```powershell
streamlit run streamlit_app.py
```

Then open the local URL Streamlit prints, usually:

```text
http://localhost:8501
```

## Streamlit Cloud

Use this repository root and set the main file to:

```text
streamlit_app.py
```

Do not set the main file to `Main App/main.py` or any backend file.

The root `packages.txt` installs the Linux libraries OpenCV needs on Streamlit Cloud:

```text
libgl1
libglib2.0-0t64
```

## Camera Tips

- Use Chrome or Edge.
- Allow browser camera permission.
- Close Zoom, Teams, OBS, or other apps using the camera.
- Stand 2-3 meters away.
- Use good lighting.
- Keep the body parts needed for the exercise visible.
- Try Standard or Low camera quality if the camera is slow.
- Refresh the page once after changing browser permissions.

The app does not require face visibility. It tracks shoulders, elbows, wrists, hips, knees, and ankles.

## Common Errors

### MediaPipe does not install

Use Python 3.11. MediaPipe does not support Python 3.13.

### VS Code uses the wrong interpreter

Select the `AI_gym` Python interpreter:

```text
Ctrl+Shift+P -> Python: Select Interpreter -> AI_gym
```

### Missing GROQ_API_KEY

Add `GROQ_API_KEY` to `.env`. The app will still work without voice coaching.

### Camera does not open

Check browser permission, close other camera apps, and try Standard camera quality.

## Future Work

The repository may contain experimental folders for backend services, multiplayer rooms, or exercise intelligence research. They are not imported by the public Streamlit MVP.

Future improvements can include trained exercise classification, production authentication, cloud workout sync, and scalable multiplayer.

## Screenshots

Screenshots coming soon.
