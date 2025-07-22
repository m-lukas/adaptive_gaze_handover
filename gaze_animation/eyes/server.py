import copy
import math
import random
import sys
import threading
import time
from math import pi as PI

import numpy as np
import pygame
from flask import Flask, jsonify, request

from programs import GazeProgram, Transition, programs

pygame.init()

WIDTH = 1024
HEIGHT = 600
TICKS_PER_SECOND = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LARO")

# Farben definieren
BG = (35.7, 70.2, 74.9)
MOUTH = (73.5, 91.5, 93.5)
LID = (14.5, 47.1, 54.1)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKIN = (240, 200, 170)

# Variablen fuer die Augenposition und Blickrichtung
eye_radius = 200
eye_radius_ = 350
pupil_radius = 50
eye_left_pos = ((WIDTH * 0.25) - eye_radius_ * 0.5, HEIGHT / 2 - eye_radius / 2)
eye_right_pos = ((0.75 * WIDTH) - eye_radius_ * 0.5, HEIGHT / 2 - eye_radius / 2)
pupil_offset = [0, 150]  # current offset
max_pupil_offsets = [75, 35]  # Ausweichpos der Pupillen (x,y)

lid_height = 0  # Hoehe des Augenlids (0 bedeutet offen)
saved_lid_height = 0

# Variablen fuer das Augenlid
lid_height = 0  # Hoehe des Augenlids (0 bedeutet offen)
saved_lid_height = 0  # Speichert den Zustand des Augenlids vor dem Zwinkern
lid_hor_delta = 10
lid_vert_delta = 5

brow_delta = {
    "up": (0, -1 * lid_hor_delta),
    "down": (0, 4 * lid_hor_delta),
    "left": (-lid_vert_delta, 0),
    "right": (lid_vert_delta, 0),
}

# Zwinker-Variablen
blink_timer = 0
blink_duration = 100
blink_interval = np.random.normal(
    6000, 2500
)  # Setze Blink-Interval auf Zufalls wert 6s +-3
is_blinking = False

# Bewegungskontrolle
looking_up = False
looking_down = False
looking_left = False
looking_right = False

movements_index = 0

app = Flask(__name__)

animation_lock = threading.Lock()
current_command = {"program": None, "elapsed": 0, "current_pos": [0, 0]}


@app.route("/trigger", methods=["POST"])
def trigger():
    global current_command
    data = request.get_json()
    try:
        name = data["program"]
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input"}), 400

    if name in programs:
        program = copy.copy(programs[name])
        with animation_lock:
            program.start_pos = current_command["current_pos"]
            current_command.update({"program": program, "elapsed": 0})

    return jsonify({"program": name})


@app.route("/move", methods=["POST"])
def move():
    global current_command
    data = request.get_json()
    try:
        x = float(data.get("x"))
        y = float(data.get("y"))
        duration = float(data.get("duration", 0.1))
    except (TypeError, ValueError) as e:
        return jsonify({"error": "Invalid input"}), 400

    with animation_lock:
        current_command.update(
            {
                "program": GazeProgram(
                    saccades=[Transition(x, y, duration)],
                    start_pos=current_command["current_pos"][:],
                ),
                "elapsed": 0,
            }
        )

    return jsonify({"target": [x, y], "duration": duration})


font = pygame.font.SysFont(None, 32)  # You can specify font name instead of None


def looking_straight():
    return not any([looking_up, looking_down, looking_left, looking_right])


def draw_brows():
    brow_offset = [0, 0]
    if looking_up:
        brow_offset[1] = brow_delta["up"][1]
    if looking_down or is_blinking:
        brow_offset[1] = brow_delta["down"][1]
    # Brows horizontal movement
    if looking_left:
        brow_offset[0] = brow_delta["left"][0]
    if looking_right:
        brow_offset[0] = brow_delta["right"][0]

    BROW1 = None
    BROW2 = None

    # Brow
    if looking_straight() and not is_blinking:
        BROW1 = pygame.Rect((eye_left_pos[0] - 50, 100), (eye_radius_ * 1.3, 200))
        BROW2 = pygame.Rect((eye_right_pos[0] - 50, 100), (eye_radius_ * 1.3, 200))
    elif looking_down or is_blinking:
        BROW1 = pygame.Rect(
            (eye_left_pos[0] - 50 + brow_offset[0], 100 + brow_offset[1]),
            (eye_radius_ * 1.3, 50),
        )
        BROW2 = pygame.Rect(
            (eye_right_pos[0] - 50 + brow_offset[0], 100 + brow_offset[1]),
            (eye_radius_ * 1.3, 50),
        )
    else:
        BROW1 = pygame.Rect(
            (eye_left_pos[0] - 50 + brow_offset[0], 100 + brow_offset[1]),
            (eye_radius_ * 1.3, 200),
        )
        BROW2 = pygame.Rect(
            (eye_right_pos[0] - 50 + brow_offset[0], 100 + brow_offset[1]),
            (eye_radius_ * 1.3, 200),
        )

    pygame.draw.arc(
        screen, LID, BROW1, start_angle=2 / 6 * PI, stop_angle=5.5 / 6 * PI, width=25
    )
    pygame.draw.arc(
        screen,
        LID,
        BROW2,
        start_angle=0.5 / 6 * PI,
        stop_angle=PI - 2 / 6 * PI,
        width=25,
    )


def draw_mouth():
    MOUTH_RECT = pygame.Rect((WIDTH / 2 - 100, HEIGHT * 0.65), (200, 100))
    start_angle = PI
    stop_angle = 0
    width = 15
    radius = width // 2

    pygame.draw.arc(screen, MOUTH, MOUTH_RECT, start_angle, stop_angle, width)

    # round corners
    start_pos = (MOUTH_RECT.left + radius, MOUTH_RECT.centery)
    end_pos = (MOUTH_RECT.right - radius, MOUTH_RECT.centery)
    pygame.draw.circle(screen, MOUTH, start_pos, radius)
    pygame.draw.circle(screen, MOUTH, end_pos, radius)


def draw_eyes():
    # Augen zeichnen
    pygame.draw.ellipse(
        screen, WHITE, [eye_left_pos[0], eye_left_pos[1], eye_radius_, eye_radius]
    )
    pygame.draw.ellipse(
        screen, WHITE, [eye_right_pos[0], eye_right_pos[1], eye_radius_, eye_radius]
    )

    # Verdeckungsbox
    if looking_down:
        pygame.draw.rect(
            screen,
            BG,
            (eye_left_pos[0], eye_left_pos[1] - 20, eye_radius_, eye_radius / 2),
        )
        pygame.draw.rect(
            screen,
            BG,
            (eye_right_pos[0], eye_right_pos[1] - 20, eye_radius_, eye_radius / 2),
        )

        pygame.draw.ellipse(
            screen,
            WHITE,
            [
                eye_left_pos[0],
                eye_left_pos[1] + eye_radius / 5,
                eye_radius_,
                eye_radius / 2,
            ],
        )
        pygame.draw.ellipse(
            screen,
            WHITE,
            [
                eye_right_pos[0],
                eye_right_pos[1] + eye_radius / 5,
                eye_radius_,
                eye_radius / 2,
            ],
        )

    if looking_up:
        pygame.draw.rect(
            screen,
            BG,
            (
                eye_left_pos[0],
                eye_left_pos[1] + eye_radius / 2 + 20,
                eye_radius_,
                eye_radius / 2,
            ),
        )
        pygame.draw.rect(
            screen,
            BG,
            (
                eye_right_pos[0],
                eye_right_pos[1] + eye_radius / 2 + 20,
                eye_radius_,
                eye_radius / 2,
            ),
        )

        pygame.draw.ellipse(
            screen,
            WHITE,
            [
                eye_left_pos[0],
                eye_left_pos[1] + eye_radius / 4.5,
                eye_radius_,
                eye_radius / 1.5,
            ],
        )
        pygame.draw.ellipse(
            screen,
            WHITE,
            [
                eye_right_pos[0],
                eye_right_pos[1] + eye_radius / 4.5,
                eye_radius_,
                eye_radius / 1.5,
            ],
        )

    # Pupillenposition basierend auf der Blickrichtung
    left_pupil_pos = (
        eye_left_pos[0] + eye_radius_ / 2 + pupil_offset[0],
        eye_left_pos[1] + eye_radius / 2 + pupil_offset[1],
    )
    right_pupil_pos = (
        eye_right_pos[0] + eye_radius_ / 2 + pupil_offset[0],
        eye_right_pos[1] + eye_radius / 2 + pupil_offset[1],
    )
    pygame.draw.circle(screen, BLACK, left_pupil_pos, pupil_radius)
    pygame.draw.circle(screen, BLACK, right_pupil_pos, pupil_radius)

    # if (looking_down or looking_up) and (looking_left or looking_right):
    left_mini_pupil_pos = (
        left_pupil_pos[0] + 0.71 * pupil_offset[0] / 2,
        left_pupil_pos[1] + 0.71 * pupil_offset[1],
    )
    right_mini_pupil_pos = (
        right_pupil_pos[0] + 0.71 * pupil_offset[0] / 2,
        right_pupil_pos[1] + 0.71 * pupil_offset[1],
    )

    pygame.draw.circle(screen, WHITE, left_mini_pupil_pos, pupil_radius / 5)
    pygame.draw.circle(screen, WHITE, right_mini_pupil_pos, pupil_radius / 5)


def animate_gaze(coordinates):
    global looking_left, looking_right, looking_up, looking_down, looking_straight, is_blinking, blink_timer, blink_interval, saved_lid_height, lid_height

    looking_left = coordinates[0] < -0.1
    looking_right = coordinates[0] > 0.1
    looking_up = coordinates[1] < -0.3
    looking_down = coordinates[1] > 0.3

    lid_height = eye_radius if looking_down else 0

    pupil_offset[0] = coordinates[0] * max_pupil_offsets[0]
    pupil_offset[1] = coordinates[1] * max_pupil_offsets[1]

    screen.fill(BG)
    # Set up text
    text = f"{coordinates[0]}|{coordinates[1]}|{movements_index}"
    text_color = (255, 255, 255)  # White color
    text_surface = font.render(text, True, text_color)
    screen.blit(text_surface, (10, 10))

    # Zwinker-Logik Start
    if not is_blinking and current_time - blink_timer > blink_interval:
        is_blinking = True  # Zwinker-Sequenz beginnt
        saved_lid_height = lid_height  # Speichere aktuellen Augenlid-Zustand
        blink_timer = current_time

    # Zwinkern animieren
    if is_blinking:
        # Augen schliessen
        if current_time - blink_timer > blink_duration:  # Augen wieder oeffnen
            lid_height = (
                saved_lid_height  # Augenlider zum urspruenglichen Zustand zurueck
            )
            is_blinking = False  # Zwinker-Sequenz beendet
            blink_interval = np.random.normal(
                6000, 2500
            )  # Setze Blink-Interval auf Zufalls wert 6s +-3
    else:
        is_blinking = False
        draw_eyes()

    draw_brows()
    draw_mouth()


def run_flask():
    app.run(port=5000)


# ------------------------------

# ----- Start Flask in a thread -----
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()


# Main loop
base_interval = 3  # Mittelwert (in Sekunden)
std_dev = 1  # Standardabweichung (in Sekunden)
running = True
last_update_time = time.time()
next_update_interval = max(0, random.gauss(base_interval, std_dev))
running = True
while running:
    current_time = pygame.time.get_ticks()  # Zeit in Millisekunden
    curr_t = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    dt = pygame.time.Clock().tick(TICKS_PER_SECOND) / 1000.0  # dt in seconds

    program: GazeProgram | None = current_command["program"]
    if program:
        current_step = program.saccades[program.index]
        duration = current_step.duration

        if current_command["elapsed"] < duration:
            current_command["elapsed"] += dt

            if isinstance(current_step, Transition):
                t = min(current_command["elapsed"] / duration, 1.0)
                eased_t = current_step.ease_function(t)

                current_command["current_pos"][0] = (
                    program.start_pos[0]
                    + (current_step.x - program.start_pos[0]) * eased_t
                )
                current_command["current_pos"][1] = (
                    program.start_pos[1]
                    + (current_step.y - program.start_pos[1]) * eased_t
                )
        else:
            with animation_lock:
                current_command["elapsed"] = 0
                if program.index < len(program.saccades) - 1:
                    program.start_pos = current_command["current_pos"][:]
                    program.index += 1
                else:
                    current_command["program"] = None

    animate_gaze(current_command["current_pos"])

    pygame.display.flip()

# Quit Pygame
pygame.quit()
