import pygame
import math


pygame.init()

WIDTH = 530
HEIGHT = 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Eye Tracking")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BLUE = (100, 149, 237)  # Lighter blue for pupils
BROWN = (139, 69, 19)  # Brown for eyebrows

CENTER_X = 265
CENTER_Y = 200 

def update():
    pass

def draw():
    screen.fill(WHITE)

    def draw_eye(eye_x, eye_y):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        distance_x = mouse_x - CENTER_X
        distance_y = mouse_y - CENTER_Y
        distance = min(math.sqrt(distance_x**2 + distance_y**2), 30)
        angle = math.atan2(distance_y, distance_x)

        pupil_x = eye_x + (math.cos(angle) * distance)
        pupil_y = eye_y + (math.sin(angle) * distance)

        pygame.draw.circle(screen, BLACK, (eye_x, eye_y), 54)  # Black border
        pygame.draw.circle(screen, WHITE, (eye_x, eye_y), 50)  # White eye
        pygame.draw.circle(screen, LIGHT_BLUE, (int(pupil_x), int(pupil_y)), 17)  # Draw pupil

    def draw_eyebrow(eye_x, eye_y):
        eyebrow_width = 80
        eyebrow_height = 10
        eyebrow_x = eye_x - eyebrow_width // 2
        eyebrow_y = eye_y - 75  # Position above the eye
        pygame.draw.rect(screen, BROWN, (eyebrow_x, eyebrow_y, eyebrow_width, eyebrow_height))
    
    LEFT_EYE = (190, 200)
    RIGHT_EYE = (340, 200)

    draw_eyebrow(LEFT_EYE[0], LEFT_EYE[1])
    draw_eyebrow(RIGHT_EYE[0], RIGHT_EYE[1])

    draw_eye(LEFT_EYE[0], LEFT_EYE[1])
    draw_eye(RIGHT_EYE[0], RIGHT_EYE[1])

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw()
    pygame.display.flip()

# Quit Pygame
pygame.quit()