EXERCISE_OPTIONS = [
    "Squats",
    "Push-ups",
    "Plank",
]


POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
]


METRICS_FIELDS = {
    "Squats": {
        "knee_angle": 0,
        "back_angle": 0,
        "depth_status": "N/A",
    },
    "Push-ups": {
        "elbow_angle": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
    "Plank": {
        "hold_seconds": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
}


EXERCISE_TUTORIALS = {
    "Squats": {
        "description": "A lower-body strength movement focused on controlled hip and knee bending.",
        "muscles": "Quads, glutes, hamstrings, core",
        "steps": [
            "Stand with feet about shoulder-width apart.",
            "Brace your core and keep your chest lifted.",
            "Push hips back and bend knees until thighs approach parallel.",
            "Drive through your heels to stand tall.",
        ],
        "mistakes": ["Shallow depth", "Knees collapsing inward", "Leaning too far forward"],
        "video_url": "https://www.youtube.com/embed/aclHkVaku9U",
    },
    "Push-ups": {
        "description": "A bodyweight upper-body exercise that trains pressing strength and trunk control.",
        "muscles": "Chest, shoulders, triceps, core",
        "steps": [
            "Start in a straight plank with hands under shoulders.",
            "Lower your chest while keeping hips level.",
            "Press the floor away until arms are straight.",
            "Keep your body in one line throughout.",
        ],
        "mistakes": ["Sagging hips", "Piked hips", "Half reps"],
        "video_url": "https://www.youtube.com/embed/IODxDxX7oi4",
    },
    "Plank": {
        "description": "A core stability hold that trains full-body tension and posture.",
        "muscles": "Core, shoulders, glutes",
        "steps": [
            "Set elbows or hands under your shoulders.",
            "Step feet back into a straight line.",
            "Brace your core and squeeze your glutes.",
            "Hold without letting hips sag or pike up.",
        ],
        "mistakes": ["Sagging hips", "Hips too high", "Holding breath"],
        "video_url": "https://www.youtube.com/embed/pSHjTRCQxIw",
    },
}


PROMPT = (
    "You are Apna AI Coach, a professional AI gym trainer monitoring a user's workout via live camera.\n\n"
    "Give short coaching feedback for voice playback. Keep responses to 2-4 sentences.\n"
    "If a form issue is provided, explain what is wrong, why it matters, how to fix it, "
    "and end with one short motivational line."
)
