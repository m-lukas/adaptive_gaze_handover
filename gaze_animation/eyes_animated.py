import math

import pygame

pygame.init()

WIDTH = 530
HEIGHT = 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Panda")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BLUE = (100, 149, 237)  # Lighter blue for pupils
BROWN = (139, 69, 19)  # Brown for eyebrows
DARK_RED = (139, 0, 0)  # Red for the mouth

CENTER_X = 265
CENTER_Y = 200

# Predefined positions for pupil animation
pupil_positions = [
    (220, 180),
    (240, 220),
    (380, 240),
    (330, 300),
    (200, 120),
    (180, 220),
    (265, 200),
    (400, 200),
    (350, 220),
    (380, 180),
    (265, 300),
]
position_index = 0  # Start with the first position
current_pupil_x, current_pupil_y = pupil_positions[0]  # Initial position

# Transition speed
transition_speed = 0.03  # Speed of transition (smaller is slower)


def update():
    pass


def draw(pupil_target):
    screen.fill(WHITE)

    def draw_eye(eye_x, eye_y):
        target_x, target_y = pupil_target

        distance_x = target_x - CENTER_X
        distance_y = target_y - CENTER_Y
        distance = min(math.sqrt(distance_x**2 + distance_y**2), 30)
        angle = math.atan2(distance_y, distance_x)

        pupil_x = eye_x + (math.cos(angle) * distance)
        pupil_y = eye_y + (math.sin(angle) * distance)

        pygame.draw.circle(screen, BLACK, (eye_x, eye_y), 54)  # Black border
        pygame.draw.circle(screen, WHITE, (eye_x, eye_y), 50)  # White eye
        pygame.draw.circle(
            screen, LIGHT_BLUE, (int(pupil_x), int(pupil_y)), 17
        )  # Draw pupil

    def draw_eyebrow(eye_x, eye_y):
        eyebrow_width = 80
        eyebrow_height = 10
        eyebrow_x = eye_x - eyebrow_width // 2
        eyebrow_y = eye_y - 75  # Position above the eye
        pygame.draw.rect(
            screen, BROWN, (eyebrow_x, eyebrow_y, eyebrow_width, eyebrow_height)
        )

    def draw_mouth():
        mouth_center_x = CENTER_X
        mouth_center_y = CENTER_Y + 90
        mouth_radius = 20
        thickness = 7

        # Draw the hollow red circle for the mouth
        pygame.draw.circle(
            screen, DARK_RED, (mouth_center_x, mouth_center_y), mouth_radius, thickness
        )

    LEFT_EYE = (190, 200)
    RIGHT_EYE = (340, 200)

    draw_eyebrow(LEFT_EYE[0], LEFT_EYE[1])
    draw_eyebrow(RIGHT_EYE[0], RIGHT_EYE[1])

    draw_eye(LEFT_EYE[0], LEFT_EYE[1])
    draw_eye(RIGHT_EYE[0], RIGHT_EYE[1])

    draw_mouth()


# Main loop
running = True
clock = pygame.time.Clock()
fps = 60  # Frames per second

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get the next target position
    target_x, target_y = pupil_positions[position_index]

    # Smoothly interpolate towards the target position
    current_pupil_x += (target_x - current_pupil_x) * transition_speed
    current_pupil_y += (target_y - current_pupil_y) * transition_speed

    # Check if the current position is close enough to the target
    if abs(current_pupil_x - target_x) < 1 and abs(current_pupil_y - target_y) < 1:
        position_index = (position_index + 1) % len(
            pupil_positions
        )  # Move to the next target

    # Draw the scene with the updated pupil position
    draw((current_pupil_x, current_pupil_y))
    pygame.display.flip()

    # Wait for the next frame
    clock.tick(fps)

# Quit Pygame
pygame.quit()
