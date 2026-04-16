#!/usr/bin/env python3
"""
Team KERNEL — WRO Future Engineers 2026
kernel_robot_r1.py — Programa principal (Ronda 1 y Ronda 2)

Ronda 1: 3 vueltas autónomas detectando líneas naranja/azul
Ronda 2: misma lógica + evasión de obstáculos rojo/verde
Solo cámara — sin ToF ni IMU para esta regional
"""

import requests
import time
from buildhat import Motor

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────
VISION_URL      = "http://localhost:5000/detections"
MOTOR_TRACCION  = 'A'       # Motor grande — Puerto A
MOTOR_DIRECCION = 'B'       # Motor mediano — Puerto B

VELOCIDAD       = -40       # % velocidad de tracción (negativo = adelante)
ANGULO_GIRO     = 90        # Grados para doblar en esquina
ANGULO_CENTRO   = 0         # Centro del motor de dirección
VUELTAS_META    = 3         # Vueltas a completar

BLOQUEO_GIRO    = 3.0       # Segundos de bloqueo tras cada giro

# ─── MOTORES ─────────────────────────────────────────────────────────────────
traccion  = Motor(MOTOR_TRACCION)
direccion = Motor(MOTOR_DIRECCION)

# ─── FUNCIONES DE MOVIMIENTO ─────────────────────────────────────────────────

def get_detecciones():
    """Obtiene detecciones del servidor de visión (Flask)."""
    try:
        r = requests.get(VISION_URL, timeout=0.3)
        return r.json()
    except:
        return {}

def linea_detectada(detecciones, color):
    """Retorna True si la línea del color está detectada."""
    return color in detecciones and len(detecciones[color]) > 0

def obstaculo_detectado(detecciones, color):
    """Retorna True si hay un obstáculo del color detectado."""
    return color in detecciones and len(detecciones[color]) > 0

def centrar_direccion():
    direccion.run_to_position(ANGULO_CENTRO, speed=50)

def girar_derecha():
    print("[GIRO] Derecha >>>")
    direccion.run_to_position(ANGULO_GIRO, speed=50)

def girar_izquierda():
    print("[GIRO] Izquierda <<<")
    direccion.run_to_position(-ANGULO_GIRO, speed=50)

def esquivar_derecha():
    """Esquiva un obstáculo rojo por la derecha."""
    print("[OBSTACULO] Rojo → esquivando derecha")
    direccion.run_to_position(ANGULO_GIRO, speed=40)
    time.sleep(1.0)
    centrar_direccion()
    time.sleep(0.5)
    direccion.run_to_position(-ANGULO_GIRO, speed=40)
    time.sleep(1.0)
    centrar_direccion()

def esquivar_izquierda():
    """Esquiva un obstáculo verde por la izquierda."""
    print("[OBSTACULO] Verde → esquivando izquierda")
    direccion.run_to_position(-ANGULO_GIRO, speed=40)
    time.sleep(1.0)
    centrar_direccion()
    time.sleep(0.5)
    direccion.run_to_position(ANGULO_GIRO, speed=40)
    time.sleep(1.0)
    centrar_direccion()

def avanzar():
    traccion.start(VELOCIDAD)

def detener():
    traccion.stop()
    centrar_direccion()
    print("[STOP] Robot detenido")

# ─── LÓGICA PRINCIPAL ────────────────────────────────────────────────────────

def main():
    esquinas  = 0
    vueltas   = 0
    bloqueado = False
    t_bloqueo = 0

    print(f"[KERNEL] Iniciando — Meta: {VUELTAS_META} vueltas")
    print("[KERNEL] Presiona Ctrl+C para detener\n")

    centrar_direccion()
    time.sleep(0.5)
    avanzar()

    try:
        while vueltas < VUELTAS_META:
            ahora = time.time()

            # Levantar bloqueo si ya pasó el tiempo
            if bloqueado and (ahora - t_bloqueo) >= BLOQUEO_GIRO:
                bloqueado = False
                centrar_direccion()
                print("[OK] Listo para próxima esquina")

            if not bloqueado:
                detecciones = get_detecciones()

                # ── Detección de obstáculos (Ronda 2) ──
                if obstaculo_detectado(detecciones, "obstaculo_rojo"):
                    esquivar_derecha()

                elif obstaculo_detectado(detecciones, "obstaculo_verde"):
                    esquivar_izquierda()

                # ── Detección de líneas de esquina (Ronda 1 y 2) ──
                elif linea_detectada(detecciones, "linea_naranja"):
                    print(f"[LINEA] Naranja → Derecha | Esquina #{esquinas + 1}")
                    girar_derecha()
                    esquinas  += 1
                    bloqueado  = True
                    t_bloqueo  = ahora

                elif linea_detectada(detecciones, "linea_azul"):
                    print(f"[LINEA] Azul → Izquierda | Esquina #{esquinas + 1}")
                    girar_izquierda()
                    esquinas  += 1
                    bloqueado  = True
                    t_bloqueo  = ahora

                # ── Conteo de vueltas ──
                if esquinas > 0 and esquinas % 4 == 0 and not bloqueado and vueltas < esquinas // 4:
                    vueltas += 1
                    print(f"\n[VUELTA] Vuelta {vueltas}/{VUELTAS_META} completada!\n")

            time.sleep(0.05)  # ~20Hz

    except KeyboardInterrupt:
        print("\n[KERNEL] Interrumpido por usuario")

    finally:
        detener()
        print(f"[KERNEL] Resultado: {vueltas}/{VUELTAS_META} vueltas | {esquinas} esquinas")

if __name__ == "__main__":
    main()
