#!/usr/bin/env python3
"""
Team KERNEL — WRO Future Engineers 2026
wro_camera.py — Servidor de visión (Flask + HSV detection)

Detecta colores en la cámara y publica resultados como JSON en:
  GET http://localhost:5000/detections
  GET http://localhost:5000/video_feed  (stream en vivo)
"""

from flask import Flask, Response, render_template_string, jsonify
from picamera2 import Picamera2
import cv2
import numpy as np
import threading

app = Flask(__name__)
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (1280, 720)}))
picam2.start()

lock = threading.Lock()
output_frame = None
detection_data = {}

FRAME_W = 1280
FRAME_H = 720

# === RANGOS HSV CALIBRADOS PARA WRO — KERNEL ===
# Colores oficiales del reglamento WRO 2026:
#   Naranja: CMYK(0,60,100,0) | Azul: CMYK(100,80,0,0)
#   Rojo obstáculo: RGB(238,39,55) | Verde obstáculo: RGB(68,214,44)
#   Magenta parqueo: RGB(255,0,255)
WRO_COLORS = {
    "obstaculo_rojo": {
        "ranges": [
            ([0,   150, 80],  [10,  255, 255]),
            ([170, 150, 80],  [179, 255, 255])
        ],
        "draw_color": (0, 0, 255),
        "min_area": 1500
    },
    "obstaculo_verde": {
        "ranges": [([45, 150, 50], [80, 255, 255])],
        "draw_color": (0, 255, 0),
        "min_area": 1500
    },
    "linea_naranja": {
        "ranges": [([8, 150, 100], [22, 255, 255])],
        "draw_color": (0, 165, 255),
        "min_area": 800
    },
    "linea_azul": {
        "ranges": [([100, 150, 50], [130, 255, 255])],
        "draw_color": (255, 100, 0),
        "min_area": 800
    },
    "pared_negra": {
        "ranges": [([0, 0, 0], [179, 80, 35])],
        "draw_color": (128, 128, 128),
        "min_area": 3000
    },
    "estacionamiento_magenta": {
        "ranges": [([140, 150, 50], [170, 255, 255])],
        "draw_color": (255, 0, 255),
        "min_area": 1000
    },
}

def get_distance(area):
    if area > 50000:
        return "muy_cerca"
    elif area > 20000:
        return "cerca"
    elif area > 8000:
        return "medio"
    return "lejos"

def get_position(cx):
    if cx < FRAME_W // 3:
        return "izquierda"
    elif cx < 2 * FRAME_W // 3:
        return "centro"
    return "derecha"

def process_frame(frame_bgr):
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    detections = {}

    # Zonas de detección (divide el frame en IZQ / CENTRO / DER)
    zone_w = FRAME_W // 3
    cv2.line(frame_bgr, (zone_w, 0), (zone_w, FRAME_H), (50,50,50), 1)
    cv2.line(frame_bgr, (2*zone_w, 0), (2*zone_w, FRAME_H), (50,50,50), 1)
    cv2.putText(frame_bgr, "IZQ", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    cv2.putText(frame_bgr, "CENTRO", (zone_w+10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    cv2.putText(frame_bgr, "DER", (2*zone_w+10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

    for name, config in WRO_COLORS.items():
        mask = np.zeros((FRAME_H, FRAME_W), dtype=np.uint8)
        for (lower, upper) in config["ranges"]:
            m = cv2.inRange(hsv, np.array(lower), np.array(upper))
            mask = cv2.add(mask, m)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections[name] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > config["min_area"]:
                x, y, w, h = cv2.boundingRect(cnt)

                # ZONA FILTER: líneas naranja y azul solo en mitad inferior
                cy_cnt = y + h // 2
                if name in ["linea_naranja", "linea_azul"] and cy_cnt < FRAME_H // 2:
                    continue

                cx = x + w // 2
                pos = get_position(cx)
                dist = get_distance(area)

                detections[name].append({
                    "cx": cx,
                    "cy": cy_cnt,
                    "area": int(area),
                    "pos": pos,
                    "distancia": dist
                })

                # Dibujar en el frame
                color = config["draw_color"]
                cv2.rectangle(frame_bgr, (x, y), (x+w, y+h), color, 2)
                cv2.circle(frame_bgr, (cx, cy_cnt), 4, color, -1)
                label = f"{name} | {pos} | {dist}"
                cv2.putText(frame_bgr, label, (x, y-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    # Panel de detecciones activas
    y_text = 40
    cv2.putText(frame_bgr, "Detecciones activas:", (FRAME_W-250, y_text),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)
    for name, dets in detections.items():
        if dets:
            y_text += 18
            cv2.putText(frame_bgr, name, (FRAME_W-250, y_text),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                        WRO_COLORS[name]["draw_color"], 1)
            for d in dets:
                y_text += 14
                cv2.putText(frame_bgr, f"  #? pos:{d['pos']} dist:{d['distancia']}",
                            (FRAME_W-250, y_text),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200,200,200), 1)

    return frame_bgr, detections

def capture_frames():
    global output_frame, detection_data
    while True:
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        processed, detections = process_frame(frame_bgr)
        with lock:
            output_frame = processed.copy()
            detection_data = detections

def generate():
    global output_frame
    while True:
        with lock:
            if output_frame is None:
                continue
            _, encoded = cv2.imencode('.jpg', output_frame,
                                      [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_bytes = encoded.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

HTML = """<!DOCTYPE html>
<html>
<head>
  <title>KERNEL Vision</title>
  <style>
    body { background:#111; color:#0f0; font-family:monospace; text-align:center; margin:0; padding:20px; }
    h1 { font-size:1.4em; }
    img { border: 2px solid #0f0; max-width:100%; }
  </style>
</head>
<body>
  <h1>KERNEL — Vision Stream</h1>
  <img src="/video_feed">
</body>
</html>"""

@app.route('/')
def index():
    return HTML

@app.route('/video_feed')
def video_feed():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detections')
def detections():
    with lock:
        return jsonify(detection_data)

if __name__ == '__main__':
    t = threading.Thread(target=capture_frames, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000, threaded=True)
