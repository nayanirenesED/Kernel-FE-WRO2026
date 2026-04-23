#!/usr/bin/env python3
"""
Team KERNEL — WRO Future Engineers 2026
calibrar_colores.py — HSV Color Calibration Tool

Shows interactive sliders to adjust HSV ranges in real time.
Press 'S' to save/print current values.
Press 'Q' to quit and print final values.

Use the output values to update the HSV ranges in wro_camera.py.
"""

from picamera2 import Picamera2
import cv2
import numpy as np

# Initialize camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (1280, 720)}))
picam2.start()

# Create windows
cv2.namedWindow("HSV Calibrator", cv2.WINDOW_NORMAL)
cv2.namedWindow("Mask", cv2.WINDOW_NORMAL)
cv2.namedWindow("Result", cv2.WINDOW_NORMAL)

# Create HSV sliders
cv2.createTrackbar("H min", "HSV Calibrator", 0,   179, lambda x: None)
cv2.createTrackbar("H max", "HSV Calibrator", 179, 179, lambda x: None)
cv2.createTrackbar("S min", "HSV Calibrator", 0,   255, lambda x: None)
cv2.createTrackbar("S max", "HSV Calibrator", 255, 255, lambda x: None)
cv2.createTrackbar("V min", "HSV Calibrator", 0,   255, lambda x: None)
cv2.createTrackbar("V max", "HSV Calibrator", 255, 255, lambda x: None)

print("=== KERNEL — HSV Color Calibrator ===")
print("S = save current values | Q = quit")
print()

while True:
    # Capture frame from camera
    frame = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    # Read slider values
    h_min = cv2.getTrackbarPos("H min", "HSV Calibrator")
    h_max = cv2.getTrackbarPos("H max", "HSV Calibrator")
    s_min = cv2.getTrackbarPos("S min", "HSV Calibrator")
    s_max = cv2.getTrackbarPos("S max", "HSV Calibrator")
    v_min = cv2.getTrackbarPos("V min", "HSV Calibrator")
    v_max = cv2.getTrackbarPos("V max", "HSV Calibrator")

    # Apply HSV mask
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask   = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(frame_bgr, frame_bgr, mask=mask)

    # Display current values on the camera frame
    info = f"HSV: [{h_min},{s_min},{v_min}] - [{h_max},{s_max},{v_max}]"
    cv2.putText(frame_bgr, info, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Show windows
    cv2.imshow("HSV Calibrator", frame_bgr)
    cv2.imshow("Mask", mask)
    cv2.imshow("Result", result)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        # Print final values and exit
        print("\n=== FINAL VALUES ===")
        print(f"Lower: [{h_min}, {s_min}, {v_min}]")
        print(f"Upper: [{h_max}, {s_max}, {v_max}]")
        break

    elif key == ord('s'):
        # Save/print current values without exiting
        print(f"[SAVED] Lower: [{h_min}, {s_min}, {v_min}] | Upper: [{h_max}, {s_max}, {v_max}]")

picam2.stop()
cv2.destroyAllWindows()
