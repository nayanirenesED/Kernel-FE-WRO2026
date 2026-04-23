#!/usr/bin/env python3
"""
Team KERNEL — WRO Future Engineers 2026
kernel_robot_r1.py — Main program (Round 1 and Round 2)

Round 1: 3 autonomous laps detecting orange/blue floor lines
Round 2: same logic + red/green obstacle avoidance + reverse parallel parking
Camera only — ToF and IMU waiting for testing
"""

import requests
import time
from buildhat import Motor

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
VISION_URL      = "http://localhost:5000/detections"
MOTOR_TRACTION  = 'A'       # Large motor — Port A
MOTOR_STEERING  = 'B'       # Medium motor — Port B

SPEED           = 40       # Traction speed % (negative = forward)
TURN_ANGLE      = 90        # Degrees to turn at each corner
CENTER_ANGLE    = 0         # Steering motor center position
LAPS_TARGET     = 3         # Number of laps to complete

TURN_BLOCK      = 3.0       # Seconds to ignore detections after each turn

# Parking parameters
PARK_SPEED      = -20       # Slower speed for parking maneuver
PARK_REVERSE    = 30        # Reverse speed for parking (positive = backward)

# ── MOTORS ────────────────────────────────────────────────────────────────────
traction  = Motor(MOTOR_TRACTION)
steering  = Motor(MOTOR_STEERING)

# ── MOVEMENT FUNCTIONS ────────────────────────────────────────────────────────

def get_detections():
    """Fetch current detections from the vision server (Flask)."""
    try:
        r = requests.get(VISION_URL, timeout=0.3)
        return r.json()
    except:
        return {}

def line_detected(detections, color):
    """Return True if the given color line is detected."""
    return color in detections and len(detections[color]) > 0

def obstacle_detected(detections, color):
    """Return True if an obstacle of the given color is detected."""
    return color in detections and len(detections[color]) > 0

def parking_detected(detections):
    """Return True if the magenta parking zone is detected."""
    return "estacionamiento_magenta" in detections and len(detections["estacionamiento_magenta"]) > 0

def center_steering():
    """Return steering motor to center position."""
    steering.run_to_position(CENTER_ANGLE, speed=50)

def turn_right():
    print("[TURN] Right >>>")
    steering.run_to_position(TURN_ANGLE, speed=50)

def turn_left():
    print("[TURN] Left <<<")
    steering.run_to_position(-TURN_ANGLE, speed=50)

def avoid_right():
    """Bypass a red obstacle on the right side."""
    print("[OBSTACLE] Red → bypassing right")
    steering.run_to_position(TURN_ANGLE, speed=40)
    time.sleep(1.0)
    center_steering()
    time.sleep(0.5)
    steering.run_to_position(-TURN_ANGLE, speed=40)
    time.sleep(1.0)
    center_steering()

def avoid_left():
    """Bypass a green obstacle on the left side."""
    print("[OBSTACLE] Green → bypassing left")
    steering.run_to_position(-TURN_ANGLE, speed=40)
    time.sleep(1.0)
    center_steering()
    time.sleep(0.5)
    steering.run_to_position(TURN_ANGLE, speed=40)
    time.sleep(1.0)
    center_steering()

def move_forward():
    traction.start(SPEED)

def move_slow():
    """Move forward slowly for parking approach."""
    traction.start(PARK_SPEED)

def stop():
    traction.stop()
    center_steering()
    print("[STOP] Robot stopped")

# ── PARKING MANEUVER ──────────────────────────────────────────────────────────

def reverse_parallel_park():
    """
    Reverse parallel parking maneuver.
    The parking zone is identified by two magenta walls.
    Strategy:
      1. Move forward past the parking zone entry
      2. Steer right and reverse into the zone
      3. Straighten and stop inside the zone
    """
    print("[PARKING] Magenta zone detected — starting reverse parallel park")

    stop()
    time.sleep(0.5)

    # Step 1: Move forward slightly to align with parking zone
    move_slow()
    time.sleep(0.8)
    stop()
    time.sleep(0.3)

    # Step 2: Steer right and reverse into the parking zone
    steering.run_to_position(TURN_ANGLE, speed=30)
    traction.start(PARK_REVERSE)
    time.sleep(1.2)

    # Step 3: Straighten steering while continuing to reverse
    center_steering()
    time.sleep(0.8)

    # Step 4: Stop inside the parking zone
    stop()
    print("[PARKING] Reverse parallel park complete")

# ── MAIN LOGIC ────────────────────────────────────────────────────────────────

def main():
    corners  = 0
    laps     = 0
    blocked  = False
    t_block  = 0
    parked   = False

    print(f"[KERNEL] Starting — Target: {LAPS_TARGET} laps")
    print("[KERNEL] Press Ctrl+C to stop\n")

    center_steering()
    time.sleep(0.5)
    move_forward()

    try:
        while laps < LAPS_TARGET or not parked:
            now = time.time()

            # Lift block if enough time has passed since last turn
            if blocked and (now - t_block) >= TURN_BLOCK:
                blocked = False
                center_steering()
                print("[OK] Ready for next corner")

            if not blocked:
                detections = get_detections()

                # ── After completing all laps: look for parking zone ──
                if laps >= LAPS_TARGET and not parked:
                    if parking_detected(detections):
                        reverse_parallel_park()
                        parked = True
                        break
                    # Keep moving slowly while searching for parking zone
                    move_slow()
                    time.sleep(0.05)
                    continue

                # ── Obstacle detection (Round 2) ──
                if obstacle_detected(detections, "obstaculo_rojo"):
                    avoid_right()

                elif obstacle_detected(detections, "obstaculo_verde"):
                    avoid_left()

                # ── Corner line detection (Round 1 and 2) ──
                elif line_detected(detections, "linea_naranja"):
                    print(f"[LINE] Orange → Right | Corner #{corners + 1}")
                    turn_right()
                    corners += 1
                    blocked  = True
                    t_block  = now

                elif line_detected(detections, "linea_azul"):
                    print(f"[LINE] Blue → Left | Corner #{corners + 1}")
                    turn_left()
                    corners += 1
                    blocked  = True
                    t_block  = now

                # ── Lap counting ──
                if corners > 0 and corners % 4 == 0 and not blocked and laps < corners // 4:
                    laps += 1
                    print(f"\n[LAP] Lap {laps}/{LAPS_TARGET} complete!\n")

            time.sleep(0.05)  # ~20Hz loop

    except KeyboardInterrupt:
        print("\n[KERNEL] Stopped by user")

    finally:
        stop()
        print(f"[KERNEL] Result: {laps}/{LAPS_TARGET} laps | {corners} corners | Parked: {parked}")

if __name__ == "__main__":
    main()
