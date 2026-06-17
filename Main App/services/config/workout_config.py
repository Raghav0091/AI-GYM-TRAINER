EXERCISE_OPTIONS=[
    "Squats",
    "Push-ups",
    "Biceps Curls (Dumbbell)",
    "Shoulder Press",
    "Lunges",
    "Jumping Jacks",
    "High Knees",
    "Crunches",
    "Sit-ups",
    "Plank",
    "Mountain Climbers",
]


POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),       # Shoulders & Arms
    (11, 23), (12, 24), (23, 24),                           # Torso / Hips
    (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)  # Legs
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
    "Biceps Curls (Dumbbell)": {
        "elbow_angle": 0,
        "shoulder_status": "N/A",
        "swing_status": "N/A",
    },
    "Shoulder Press": {
        "elbow_angle": 0,
        "extension_status": "N/A",
        "back_arch_status": "N/A",
    },
    "Lunges": {
        "front_knee_angle": 0,
        "torso_angle": 0,
        "balance_status": "N/A",
    },
    "Jumping Jacks": {
        "arm_status": "N/A",
        "foot_status": "N/A",
        "jumping_jack_stage": "N/A",
    },
    "High Knees": {
        "knee_height": "N/A",
        "pace_status": "N/A",
        "active_knee": "N/A",
    },
    "Crunches": {
        "torso_angle": 0,
        "range_status": "N/A",
        "neck_status": "N/A",
    },
    "Sit-ups": {
        "torso_angle": 0,
        "range_status": "N/A",
        "control_status": "N/A",
    },
    "Plank": {
        "hold_seconds": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
    "Mountain Climbers": {
        "knee_drive": "N/A",
        "hip_status": "N/A",
        "active_knee": "N/A",
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
    "Biceps Curls (Dumbbell)": {
        "description": "An arm isolation exercise focused on controlled elbow flexion.",
        "muscles": "Biceps, brachialis, forearms",
        "steps": [
            "Stand tall with elbows close to your ribs.",
            "Curl the weight without swinging your torso.",
            "Squeeze at the top, then lower with control.",
            "Keep shoulders quiet and wrists neutral.",
        ],
        "mistakes": ["Swinging", "Elbows drifting forward", "Dropping the weight"],
        "video_url": "https://www.youtube.com/embed/ykJmrZ5v0Oo",
    },
    "Shoulder Press": {
        "description": "A vertical press that develops shoulder strength and overhead control.",
        "muscles": "Shoulders, triceps, upper chest, core",
        "steps": [
            "Start with elbows below wrists near shoulder height.",
            "Brace your core and keep ribs down.",
            "Press overhead until arms are extended.",
            "Lower back to shoulder height with control.",
        ],
        "mistakes": ["Excessive back arch", "Partial extension", "Shrugging hard"],
        "video_url": "https://www.youtube.com/embed/qEwKCR5JCog",
    },
    "Lunges": {
        "description": "A single-leg strength pattern that challenges balance and lower-body control.",
        "muscles": "Quads, glutes, hamstrings, calves",
        "steps": [
            "Step one foot forward with a stable stance.",
            "Lower until both knees bend under control.",
            "Keep torso tall and front knee tracking over toes.",
            "Push through the front foot to stand.",
        ],
        "mistakes": ["Losing balance", "Front knee collapsing", "Torso leaning"],
        "video_url": "https://www.youtube.com/embed/QOVaHwm-Q6U",
    },
    "Jumping Jacks": {
        "description": "A full-body cardio movement using coordinated arm and leg rhythm.",
        "muscles": "Calves, shoulders, glutes, core",
        "steps": [
            "Start tall with feet together and arms by your sides.",
            "Jump feet out while raising hands overhead.",
            "Jump back to the starting position.",
            "Land softly and keep a steady rhythm.",
        ],
        "mistakes": ["Low arm raise", "Tiny foot step", "Hard landings"],
        "video_url": "https://www.youtube.com/embed/c4DAnQ6DtF8",
    },
    "High Knees": {
        "description": "A cardio drill that trains knee drive, rhythm, and core posture.",
        "muscles": "Hip flexors, quads, calves, core",
        "steps": [
            "Stand tall with elbows bent.",
            "Drive one knee up toward hip height.",
            "Switch quickly to the other knee.",
            "Stay light on your feet and keep posture tall.",
        ],
        "mistakes": ["Low knees", "Leaning backward", "Slow uneven rhythm"],
        "video_url": "https://www.youtube.com/embed/oDdkytliOqE",
    },
    "Crunches": {
        "description": "A core exercise focused on controlled spinal flexion.",
        "muscles": "Rectus abdominis, obliques",
        "steps": [
            "Lie down with knees bent and feet planted.",
            "Brace your core and lift shoulders from the floor.",
            "Pause briefly at the top.",
            "Lower with control without pulling your neck.",
        ],
        "mistakes": ["Pulling on the neck", "Using momentum", "Very short range"],
        "video_url": "https://www.youtube.com/embed/Xyd_fa5zoEU",
    },
    "Sit-ups": {
        "description": "A larger-range core movement that brings your torso up toward your thighs.",
        "muscles": "Abs, hip flexors, obliques",
        "steps": [
            "Lie on your back with knees bent and feet planted.",
            "Brace your core and curl your torso upward.",
            "Sit up toward your thighs without yanking your neck.",
            "Lower back down slowly before the next rep.",
        ],
        "mistakes": ["Pulling the neck", "Using too much momentum", "Feet lifting off the floor"],
        "video_url": "https://www.youtube.com/embed/jDwoBqPH0jk",
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
    "Mountain Climbers": {
        "description": "A fast plank-based cardio drill using alternating knee drives.",
        "muscles": "Core, shoulders, hip flexors, quads",
        "steps": [
            "Start in a strong high plank.",
            "Drive one knee toward your chest.",
            "Switch legs quickly while keeping shoulders stacked.",
            "Keep hips level and move with control.",
        ],
        "mistakes": ["Hips bouncing high", "Short knee drive", "Shoulders drifting behind hands"],
        "video_url": "https://www.youtube.com/embed/nmwgirgXLYM",
    },
}


PROMPT = (
    "You are Apna AI Coach, a professional AI gym trainer monitoring a user's workout via live camera.\n\n"
    "### Your Role\n"
    "Provide short but useful coaching feedback for voice playback. Keep responses to 2-4 sentences.\n\n"
    "### Input Format\n"
    "You receive updates in the format: 'Event: [state] Form Issue: [description]'.\n"
    "- 'Event': workout_started, set_completed, workout_completed, no_pose_detected, ongoing_form_check.\n"
    "- 'Form Issue': A technical description of a pose error (if any).\n\n"
    "### Guidelines\n"
    "1. If a form issue is provided, explain what is wrong, why it matters, and how to fix it.\n"
    "2. NO generic greetings or redundant questions. Focus on the workout.\n"
    "3. Use the second person (e.g., 'Straighten your back' instead of 'The user should straighten their back').\n"
    "4. End with one short motivational line.\n"
    "5. Maintain a professional coaching tone and prioritize safety.\n\n"
    "### Scenario Response Styles\n"
    "- 'workout_started' -> A motivating and sharp command to begin.\n"
    "- 'workout_completed' -> A warm and encouraging closing for the session.\n"
    "- 'set_completed' -> Direct praise for finishing the set.\n"
    "- 'no_pose_detected' -> A clear instruction for the user to reposition within the camera frame.\n"
    "- 'ongoing_form_check' + Form Issue -> Mention the issue, why it matters, and one specific fix.\n"
    "- 'ongoing_form_check' (No Issue) -> Brief, energetic words of encouragement.\n"
)
