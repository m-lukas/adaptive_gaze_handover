import copy
import math
import os
import sys
import threading

import numpy as np
import pygame
from flask import Flask, jsonify, request, make_response

from notifier import notify_gaze_program_finished, notify_keyboard_event
from programs import GazeProgram, Transition, programs

WIDTH = 1024
HEIGHT = 768
TICKS_PER_SECOND = 60

BG = (135, 135, 135)
MOUTH = (53, 71, 73)
LID = (4.5, 37.1, 44.1)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

EYE_RADIUS = 200
EYE_RADIUS_ = 350
PUPIL_RADIUS = 50
MAX_PUPIL_OFFSETS = (75, 35)
LID_HOR_DELTA = 10
LID_VERT_DELTA = 5
BROW_DELTA = {
    "up": (0, -1 * LID_HOR_DELTA),
    "down": (0, 4 * LID_HOR_DELTA),
    "left": (-LID_VERT_DELTA, 0),
    "right": (LID_VERT_DELTA, 0),
}
BLINK_DURATION = 120

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify_actual_response(response, status_code=200):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, status_code

class GazeEngine:
    """Engine for gaze animation and state management."""

    def __init__(self, screen):
        self.screen = screen
        self.lock = threading.Lock()
        self.state = {
            "program": copy.copy(programs["idle"]),
            "elapsed": 0.0,
            "current_pos": [0.0, 0.0],
        }
        self.blink_timer = pygame.time.get_ticks()
        self.blink_interval = np.random.normal(6000, 2500)
        self.is_blinking = False
        self.saved_lid_height = 0.0
        self.lid_height = 0.0
        self.pupil_offset = [0.0, 150.0]
        self.eye_left_pos = (
            WIDTH * 0.25 - EYE_RADIUS_ * 0.5,
            HEIGHT * 0.5 - EYE_RADIUS * 0.5,
        )
        self.eye_right_pos = (
            0.75 * WIDTH - EYE_RADIUS_ * 0.5,
            HEIGHT * 0.5 - EYE_RADIUS * 0.5,
        )

    def draw_solid_arc(self, color, rect, start_angle, stop_angle, width, segments=40):
        cx, cy = rect.center
        rx, ry = rect.width / 2, rect.height / 2
        inner_rx = rx - width
        inner_ry = ry - width
        outer = []
        for i in range(segments + 1):
            theta = start_angle + (stop_angle - start_angle) * (i / segments)
            outer.append((cx + rx * math.cos(theta), cy + ry * math.sin(theta)))
        inner = []
        for i in range(segments + 1):
            theta = stop_angle - (stop_angle - start_angle) * (i / segments)
            inner.append((cx + inner_rx * math.cos(theta), cy + inner_ry * math.sin(theta)))
        pygame.draw.polygon(self.screen, color, outer + inner)

    def draw_brows(self):
        x, y = self.state["current_pos"]
        looking_up = y < -0.3
        looking_down = y > 0.3
        looking_left = x < -0.1
        looking_right = x > 0.1
        looking_straight = not any((looking_up, looking_down, looking_left, looking_right))
        
        brow_offset = [0, 0]
        if looking_up:
            brow_offset[1] = BROW_DELTA["up"][1]
        if looking_down or self.is_blinking:
            brow_offset[1] = BROW_DELTA["down"][1]
        if looking_left:
            brow_offset[0] = BROW_DELTA["left"][0]
        if looking_right:
            brow_offset[0] = BROW_DELTA["right"][0]

        # Brow
        if looking_straight and not self.is_blinking:
            brows = [
                pygame.Rect((self.eye_left_pos[0] - 50, 100), (EYE_RADIUS_ * 1.3, 200)),
                pygame.Rect((self.eye_right_pos[0] - 50, 100), (EYE_RADIUS_ * 1.3, 200)),
            ]
        elif looking_down or self.is_blinking:
            brows = [
                pygame.Rect((self.eye_left_pos[0] - 50 + brow_offset[0], 100 + brow_offset[1]), (EYE_RADIUS_ * 1.3, 50)),
                pygame.Rect((self.eye_right_pos[0] - 50 + brow_offset[0], 100 + brow_offset[1]), (EYE_RADIUS_ * 1.3, 50)),
            ]
        else:
            brows = [
                pygame.Rect((self.eye_left_pos[0] - 50 + brow_offset[0], 100 + brow_offset[1]), (EYE_RADIUS_ * 1.3, 200)),
                pygame.Rect((self.eye_right_pos[0] - 50 + brow_offset[0], 100 + brow_offset[1]), (EYE_RADIUS_ * 1.3, 200)),
            ]

        pygame.draw.arc(
            self.screen, LID, brows[0], start_angle=2 / 6 * math.pi, stop_angle=5.5 / 6 * math.pi, width=25
        )
        pygame.draw.arc(
            self.screen,
            LID,
            brows[1],
            start_angle=0.5 / 6 * math.pi,
            stop_angle=math.pi - 2 / 6 * math.pi,
            width=25,
        )

    def draw_mouth(self):
        rect = pygame.Rect((WIDTH/2 - 100, HEIGHT * 0.65), (200, 100))
        self.draw_solid_arc(MOUTH, rect, math.pi, 0, 15, segments=120)

    def draw_eyes(self):
        x, y = self.state["current_pos"]
        looking_up = y < -0.3
        looking_down = y > 0.3
        pygame.draw.ellipse(self.screen, WHITE, [*self.eye_left_pos, EYE_RADIUS_, EYE_RADIUS])
        pygame.draw.ellipse(self.screen, WHITE, [*self.eye_right_pos, EYE_RADIUS_, EYE_RADIUS])
        if looking_down:
            self.screen.fill(BG, (self.eye_left_pos[0], self.eye_left_pos[1] - 20, EYE_RADIUS_, EYE_RADIUS/2))
            self.screen.fill(BG, (self.eye_right_pos[0], self.eye_right_pos[1] - 20, EYE_RADIUS_, EYE_RADIUS/2))
            pygame.draw.ellipse(self.screen, WHITE, [self.eye_left_pos[0], self.eye_left_pos[1] + EYE_RADIUS/5, EYE_RADIUS_, EYE_RADIUS/2])
            pygame.draw.ellipse(self.screen, WHITE, [self.eye_right_pos[0], self.eye_right_pos[1] + EYE_RADIUS/5, EYE_RADIUS_, EYE_RADIUS/2])
        if looking_up:
            self.screen.fill(BG, (self.eye_left_pos[0], self.eye_left_pos[1] + EYE_RADIUS/2 + 20, EYE_RADIUS_, EYE_RADIUS/2))
            self.screen.fill(BG, (self.eye_right_pos[0], self.eye_right_pos[1] + EYE_RADIUS/2 + 20, EYE_RADIUS_, EYE_RADIUS/2))
            pygame.draw.ellipse(self.screen, WHITE, [self.eye_left_pos[0], self.eye_left_pos[1] + EYE_RADIUS/4.5, EYE_RADIUS_, EYE_RADIUS/1.5])
            pygame.draw.ellipse(self.screen, WHITE, [self.eye_right_pos[0], self.eye_right_pos[1] + EYE_RADIUS/4.5, EYE_RADIUS_, EYE_RADIUS/1.5])
        left_pupil = (self.eye_left_pos[0] + EYE_RADIUS_/2 + self.pupil_offset[0],
                      self.eye_left_pos[1] + EYE_RADIUS/2 + self.pupil_offset[1])
        right_pupil = (self.eye_right_pos[0] + EYE_RADIUS_/2 + self.pupil_offset[0],
                       self.eye_right_pos[1] + EYE_RADIUS/2 + self.pupil_offset[1])
        pygame.draw.circle(self.screen, BLACK, left_pupil, PUPIL_RADIUS)
        pygame.draw.circle(self.screen, BLACK, right_pupil, PUPIL_RADIUS)
        mini = (0.71*self.pupil_offset[0]/2, 0.71*self.pupil_offset[1])
        pygame.draw.circle(self.screen, WHITE, (left_pupil[0]+mini[0], left_pupil[1]+mini[1]), PUPIL_RADIUS/5)
        pygame.draw.circle(self.screen, WHITE, (right_pupil[0]+mini[0], right_pupil[1]+mini[1]), PUPIL_RADIUS/5)

    def animate_gaze(self, current_time):
        coordinates = self.state["current_pos"]
        looking_down = coordinates[1] > 0.3

        self.lid_height = EYE_RADIUS if looking_down else 0

        self.pupil_offset[0] = coordinates[0] * MAX_PUPIL_OFFSETS[0]
        self.pupil_offset[1] = coordinates[1] * MAX_PUPIL_OFFSETS[1]

        self.screen.fill(BG)

        # Initiate blinking
        if not self.is_blinking and current_time - self.blink_timer > self.blink_interval:
            self.is_blinking = True
            self.saved_lid_height = self.lid_height
            self.blink_timer = current_time

        # Animate blinking
        if self.is_blinking:
            # Eyes are closed
            if current_time - self.blink_timer > BLINK_DURATION:
                # Eyes will be open in next frame
                self.lid_height = self.saved_lid_height
                self.is_blinking = False
                self.blink_interval = np.random.normal(
                    6000, 2500
                )
        else:
            self.is_blinking = False
            self.draw_eyes()

        self.draw_brows()
        self.draw_mouth()

    # Main Loop
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_LEFT:
                        notify_keyboard_event("handover_start_detected_left")
                    elif event.key == pygame.K_RIGHT:
                        notify_keyboard_event("handover_start_detected_right")
                    elif event.key == pygame.K_SPACE:
                        notify_keyboard_event("object_in_bowl")
                    elif event.key == pygame.K_BACKSPACE:
                        notify_keyboard_event("error_during_handover")
            dt = clock.tick(TICKS_PER_SECOND) / 1000.0
            prog = self.state["program"]
            if prog:
                step = prog.saccades[prog.index]
                dur = step.duration
                if dur == 0:
                    self.state["current_pos"] = [step.x, step.y]
                if self.state["elapsed"] < dur:
                    self.state["elapsed"] += dt
                    if isinstance(step, Transition):
                        t = min(self.state["elapsed"] / dur, 1.0)
                        eased = step.ease_function(t)
                        sx, sy = prog.start_pos
                        self.state["current_pos"][0] = sx + (step.x - sx) * eased
                        self.state["current_pos"][1] = sy + (step.y - sy) * eased
                else:
                    with self.lock:
                        self.state["elapsed"] = 0
                        if prog.index < len(prog.saccades) - 1:
                            prog.start_pos = list(self.state["current_pos"])
                            prog.index += 1
                        else:
                            try:
                                notify_gaze_program_finished()
                                self.state["program"] = None
                            except Exception:
                                fallback = copy.copy(programs["idle"])
                                fallback.start_pos = list(self.state["current_pos"])
                                self.state.update({"program": fallback, "elapsed": 0})
            self.animate_gaze(current_time)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

# Create Flask app (web server)
def create_app(engine):
    """Create Flask app with injected engine state."""
    app = Flask(__name__)

    @app.route("/", methods=["GET", "OPTIONS"])
    def status():
        if request.method == "OPTIONS":
            return _build_cors_preflight_response()
        return _corsify_actual_response(jsonify({"status": "ok"}))

    @app.route("/trigger", methods=["POST", "OPTIONS"])
    def trigger():
        if request.method == "OPTIONS":
            return _build_cors_preflight_response()
        data = request.get_json(silent=True)
        name = data.get("program") if data else None
        if name in programs:
            prog = copy.copy(programs[name])
            with engine.lock:
                prog.start_pos = engine.state["current_pos"][:]
                engine.state.update({"program": prog, "elapsed": 0})
        return _corsify_actual_response(jsonify({"program": name}))

    @app.route("/move", methods=["POST"])
    def move():
        data = request.get_json(silent=True)
        try:
            x = float(data.get("x"))
            y = float(data.get("y"))
            duration = float(data.get("duration", 0.1))
        except Exception:
            return jsonify({"error": "Invalid input"}), 400
        with engine.lock:
            engine.state.update({
                "program": GazeProgram(saccades=[Transition(x, y, duration)],
                                       start_pos=engine.state["current_pos"][:]),
                "elapsed": 0
            })
        return jsonify({"target": [x, y], "duration": duration})

    return app

# Entry point of program
def main():
    os.environ["SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS"] = "0"
    pygame.init()
    screen = pygame.display.set_mode((0,0), pygame.NOFRAME)
    pygame.display.set_caption("LARO")

    engine = GazeEngine(screen)
    app = create_app(engine)
    flask_thread = threading.Thread(target=lambda: app.run(port=2222), daemon=True)
    flask_thread.start()

    engine.run()

if __name__ == "__main__":
    main()
