import copy
import math
import os
import random
import sys
import threading
import time
from math import pi as PI

import numpy as np
from notifier import notify_gaze_program_finished, notify_keyboard_event
import pygame
from flask import Flask, jsonify, request, make_response

from programs import GazeProgram, Transition, programs

os.environ["SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS"] = "0"
pygame.init()

# Configure Window
WIDTH = 1024
HEIGHT = 768
TICKS_PER_SECOND = 60
screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
pygame.display.set_caption("LARO")

# Colors
BG = (135, 135, 135)
MOUTH = (53, 71, 73)
LID = (4.5, 37.1, 44.1)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Global Variables for Eyes
eye_radius = 200
eye_radius_ = 350
pupil_radius = 50
eye_left_pos = ((WIDTH * 0.25) - eye_radius_ * 0.5, HEIGHT / 2 - eye_radius / 2)
eye_right_pos = ((0.75 * WIDTH) - eye_radius_ * 0.5, HEIGHT / 2 - eye_radius / 2)
pupil_offset = [0, 150]  # current offset
max_pupil_offsets = [75, 35]  # Ausweichpos der Pupillen (x,y)

# Global Variables for Lid
lid_height = 0  # Hoehe des Augenlids (0 bedeutet offen)
saved_lid_height = 0  # Speichert den Zustand des Augenlids vor dem Zwinkern
lid_hor_delta = 10
lid_vert_delta = 5

# Global Variables for Brow
brow_delta = {
    "up": (0, -1 * lid_hor_delta),
    "down": (0, 4 * lid_hor_delta),
    "left": (-lid_vert_delta, 0),
    "right": (lid_vert_delta, 0),
}

# Global Variables for Blinking
blink_timer = 0
blink_duration = 100
blink_interval = np.random.normal(
    6000, 2500
)  # Interval: 6s +- 2.5s
is_blinking = False

looking_up = False
looking_down = False
looking_left = False
looking_right = False

# Index of current Gaze Program
movements_index = 0

app = Flask(__name__)

# Current Gaze Program
animation_lock = threading.Lock()
current_command = {
    "program": copy.copy(programs["idle"]),
    "elapsed": 0,
    "current_pos": [0, 0],
}

# CORS - important for Panda Experiment Controller
def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify_actual_response(response, status_code=200):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, status_code

# Health Route
@app.route("/", methods=["GET", "OPTIONS"])
def status():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    return _corsify_actual_response(jsonify({"status": "ok"}))

# Route for triggering Programs
@app.route("/trigger", methods=["POST", "OPTIONS"])
def trigger():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    elif request.method == "POST":
        global current_command
        data = request.get_json()
        try:
            name = data["program"]
        except (TypeError, ValueError):
            return _corsify_actual_response(jsonify({"error": "Invalid input"}), 400)

        if name in programs:
            program = copy.copy(programs[name])
            with animation_lock:
                program.start_pos = current_command["current_pos"]
                current_command.update({"program": program, "elapsed": 0})

        return _corsify_actual_response(jsonify({"program": name}))

# Route for triggering eye movement to specific coordinates
@app.route("/move", methods=["POST"])
def move():
    global current_command
    data = request.get_json()
    try:
        x = float(data.get("x"))
        y = float(data.get("y"))
        duration = float(data.get("duration", 0.1))
    except (TypeError, ValueError):
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


def looking_straight():
    return not any([looking_up, looking_down, looking_left, looking_right])


# Helper function for drawing mouth
def draw_solid_arc(surface, color, rect, start_angle, stop_angle, width, segments=40):
    cx, cy = rect.center
    rx, ry = rect.width / 2, rect.height / 2
    inner_rx = rx - width
    inner_ry = ry - width

    # Outer Arc
    outer = []
    for i in range(segments + 1):
        theta = start_angle + (stop_angle - start_angle) * (i / segments)
        x = cx + rx * math.cos(theta)
        y = cy + ry * math.sin(theta)
        outer.append((x, y))

    # Inner Arc
    inner = []
    for i in range(segments + 1):
        theta = stop_angle - (stop_angle - start_angle) * (i / segments)
        x = cx + inner_rx * math.cos(theta)
        y = cy + inner_ry * math.sin(theta)
        inner.append((x, y))

    pts = outer + inner
    pygame.draw.polygon(surface, color, pts)


# Animate brows
def draw_brows():
    brow_offset = [0, 0]
    if looking_up:
        brow_offset[1] = brow_delta["up"][1]
    if looking_down or is_blinking:
        brow_offset[1] = brow_delta["down"][1]
    
    # Horizontal movement of brows
    if looking_left:
        brow_offset[0] = brow_delta["left"][0]
    if looking_right:
        brow_offset[0] = brow_delta["right"][0]

    BROW1 = None
    BROW2 = None

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


# Animate mouth
def draw_mouth():
    MOUTH_RECT = pygame.Rect((WIDTH / 2 - 100, HEIGHT * 0.65), (200, 100))
    draw_solid_arc(screen, MOUTH, MOUTH_RECT, math.pi, 0, 15, segments=120)


# Animate eyes
def draw_eyes():

    # Draw white background 
    pygame.draw.ellipse(
        screen, WHITE, [eye_left_pos[0], eye_left_pos[1], eye_radius_, eye_radius]
    )
    pygame.draw.ellipse(
        screen, WHITE, [eye_right_pos[0], eye_right_pos[1], eye_radius_, eye_radius]
    )

    # Lids
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

    # Calculate position and draw pupils
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


# Animate robot face for this frame
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

    # Blinking Initiation
    if not is_blinking and current_time - blink_timer > blink_interval:
        is_blinking = True
        saved_lid_height = lid_height
        blink_timer = current_time

    # Blinking animation
    if is_blinking:
        if current_time - blink_timer > blink_duration:
            # Eyes are closed in this frame but will be open in the next frame
            lid_height = (
                saved_lid_height
            )
            is_blinking = False
            blink_interval = np.random.normal(
                6000, 2500
            )
    else:
        # Open Eyes
        is_blinking = False
        draw_eyes()

    draw_brows()
    draw_mouth()


# Run web server
def run_flask():
    app.run(port=2222)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()


# --- Animation Loop ---
base_interval = 3
std_dev = 1
running = True
last_update_time = time.time()
next_update_interval = max(0, random.gauss(base_interval, std_dev))
running = True
while running:
    current_time = pygame.time.get_ticks()
    curr_t = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # Check for keyboard inputs and trigger events
            elif event.key == pygame.K_LEFT:
                notify_keyboard_event("handover_start_detected_left")

            elif event.key == pygame.K_RIGHT:
                notify_keyboard_event("handover_start_detected_right")

            elif event.key == pygame.K_SPACE:
                notify_keyboard_event("object_in_bowl")

            elif event.key == pygame.K_BACKSPACE:
                notify_keyboard_event("error_during_handover")

    dt = pygame.time.Clock().tick(TICKS_PER_SECOND) / 1000.0

    # Animate frame for current program + Logic to transition between / end programs
    program: GazeProgram | None = current_command["program"]
    if program:
        current_step = program.saccades[program.index]
        duration = current_step.duration

        if duration == 0:
            current_command["current_pos"][0] = current_step.x
            current_command["current_pos"][1] = current_step.y

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
            # Duration of saccade / gaze transition is exceeded
            with animation_lock:
                current_command["elapsed"] = 0
                if program.index < len(program.saccades) - 1:
                    # Go to next saccade
                    program.start_pos = current_command["current_pos"][:]
                    program.index += 1
                else:
                    # Finish gaze program
                    try:
                        notify_gaze_program_finished()
                        current_command["program"] = None
                    except Exception:
                        program = copy.copy(programs["idle"])
                        program.start_pos = current_command["current_pos"]
                        current_command.update({"program": program, "elapsed": 0})

    animate_gaze(current_command["current_pos"])

    pygame.display.flip()

# Quit Pygame
pygame.quit()
