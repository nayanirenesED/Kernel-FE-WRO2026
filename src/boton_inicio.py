#!/usr/bin/env python3
"""
Team KERNEL — WRO Future Engineers 2026
boton_inicio.py — Physical Start Button Listener (GPIO 17)

Waits for the green button press and launches kernel_robot_r1.py.
Started automatically on boot via systemd (wro-boton.service).

Wiring:
  GPIO 17 (Pin 11) → Button pin 1
  GND     (Pin 9)  → Button pin 2 (diagonal)
"""

import RPi.GPIO as GPIO
import subprocess
import time
import os

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
BUTTON_PIN   = 17          # GPIO 17 — physical pin 11
SCRIPT_PATH  = "/home/wro_kernel/kernel_robot_r1.py"
DEBOUNCE_MS  = 300         # Milliseconds to ignore repeated presses (debounce)

# ── GPIO SETUP ────────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# PUD_UP: pin reads HIGH when button is not pressed, LOW when pressed

robot_process = None  # Reference to the running robot process

def button_pressed(channel):
    """Called when the button press is detected (falling edge)."""
    global robot_process

    # If the robot is already running, ignore the press
    if robot_process is not None and robot_process.poll() is None:
        print("[BUTTON] Robot already running — ignoring press")
        return

    print("[BUTTON] Pressed! Starting robot...")
    robot_process = subprocess.Popen(
        ["sudo", "-E", "python3", SCRIPT_PATH],
        cwd=os.path.dirname(SCRIPT_PATH)
    )
    print(f"[BUTTON] Robot started with PID {robot_process.pid}")

# ── EVENT LISTENER ────────────────────────────────────────────────────────────
GPIO.add_event_detect(
    BUTTON_PIN,
    GPIO.FALLING,        # Detect when button is pressed (HIGH → LOW)
    callback=button_pressed,
    bouncetime=DEBOUNCE_MS
)

print("[KERNEL] System ready. Waiting for start button on GPIO 17...")
print("[KERNEL] Press the green button to start the robot.")

try:
    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n[KERNEL] Stopped by user")

finally:
    GPIO.cleanup()
    if robot_process is not None and robot_process.poll() is None:
        robot_process.terminate()
        print("[KERNEL] Robot process terminated")
