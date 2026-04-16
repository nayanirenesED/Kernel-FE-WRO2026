#!/usr/bin/env python3
"""
Team KERNEL — WRO Future Engineers 2026
calibrar_colores.py — Herramienta de calibración HSV

Muestra sliders para ajustar rangos HSV en tiempo real.
Presiona 'S' para guardar los valores actuales.
Presiona 'Q' para salir.
"""

from picamera2 import Picamera2
import cv2
import numpy as np

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (1280, 720)}))
picam2.start()

cv2.namedWindow("Calibrador HSV", cv2.WINDOW_NORMAL)
cv2.namedWindow("Mascara", cv2.WINDOW_NORMAL)
cv2.namedWindow("Resultado", cv2.WINDOW_NORMAL)

# Sliders
cv2.createTrackbar("H min", "Calibrador HSV", 0,   179, lambda x: None)
cv2.createTrackbar("H max", "Calibrador HSV", 179, 179, lambda x: None)
cv2.createTrackbar("S min", "Calibrador HSV", 0,   255, lambda x: None)
cv2.createTrackbar("S max", "Calibrador HSV", 255, 255, lambda x: None)
cv2.createTrackbar("V min", "Calibrador HSV", 0,   255, lambda x: None)
cv2.createTrackbar("V max", "Calibrador HSV", 255, 255, lambda x: None)

print("=== KERNEL — Calibrador de Colores HSV ===")
print("S = guardar valores | Q = salir")
print()

while True:
    frame = picam2.capture_array()
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    h_min = cv2.getTrackbarPos("H min", "Calibrador HSV")
    h_max = cv2.getTrackbarPos("H max", "Calibrador HSV")
    s_min = cv2.getTrackbarPos("S min", "Calibrador HSV")
    s_max = cv2.getTrackbarPos("S max", "Calibrador HSV")
    v_min = cv2.getTrackbarPos("V min", "Calibrador HSV")
    v_max = cv2.getTrackbarPos("V max", "Calibrador HSV")

    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(frame_bgr, frame_bgr, mask=mask)

    # Mostrar valores actuales en el frame
    info = f"HSV: [{h_min},{s_min},{v_min}] - [{h_max},{s_max},{v_max}]"
    cv2.putText(frame_bgr, info, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Calibrador HSV", frame_bgr)
    cv2.imshow("Mascara", mask)
    cv2.imshow("Resultado", result)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("\n=== VALORES FINALES ===")
        print(f"Lower: [{h_min}, {s_min}, {v_min}]")
        print(f"Upper: [{h_max}, {s_max}, {v_max}]")
        break
    elif key == ord('s'):
        print(f"[GUARDADO] Lower: [{h_min}, {s_min}, {v_min}] | Upper: [{h_max}, {s_max}, {v_max}]")

picam2.stop()
cv2.destroyAllWindows()
