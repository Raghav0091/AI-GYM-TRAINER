import math


def calculate_angle(a, b, c):
    """Calculate the 2D joint angle ABC in degrees."""
    if not a or not b or not c:
        return 0.0

    ax, ay = a[0] - b[0], a[1] - b[1]
    cx, cy = c[0] - b[0], c[1] - b[1]
    dot = ax * cx + ay * cy
    mag_a = math.sqrt(ax**2 + ay**2)
    mag_c = math.sqrt(cx**2 + cy**2)

    if mag_a * mag_c == 0:
        return 0.0

    cos_angle = max(-1.0, min(1.0, dot / (mag_a * mag_c)))
    return max(0.0, min(180.0, math.degrees(math.acos(cos_angle))))
