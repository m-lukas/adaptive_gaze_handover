import pygame
import sys
import numpy as np
from math import pi as PI
import random
import time


pygame.init()

WIDTH = 1024
HEIGHT = 600
TICKS_PER_SECOND = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LARO")

# Farben definieren
BG = (35.7,70.2, 74.9)
MOUTH = (73.5,91.5,93.5)
LID = (14.5,47.1,54.1)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKIN = (240, 200, 170)
CYAN= (0,255,255)

# Variablen fuer die Augenposition und Blickrichtung
eye_radius = 200
eye_radius_ = 350
pupil_radius = 50
eye_left_pos = ((WIDTH*0.25)-eye_radius_*0.5, HEIGHT/2 -eye_radius/2 )
eye_right_pos = ((0.75*WIDTH)-eye_radius_*0.5, HEIGHT/2 -eye_radius/2)
pupil_offset = [0,150] # current offset
max_pupil_offsets = [75,35]  # Ausweichpos der Pupillen (x,y)

lid_height = 0  # Hoehe des Augenlids (0 bedeutet offen)
saved_lid_height = 0

# Variablen fuer das Augenlid
lid_height = 0  # Hoehe des Augenlids (0 bedeutet offen)
saved_lid_height = 0  # Speichert den Zustand des Augenlids vor dem Zwinkern
lid_hor_delta=10
lid_vert_delta=5

# Definierte Richtungen (x, y) fuer die Pupillenbewegung
directions = {
    'up': (0, -1*max_pupil_offsets[1]),
    'down': (0, max_pupil_offsets[1]),
    'left': (-1*max_pupil_offsets[0], 0),
    'right': (max_pupil_offsets[0], 0)
}
brow_delta = {
    'up': (0, -1*lid_hor_delta),
    'down': (0, 4*lid_hor_delta),
    'left': (-lid_vert_delta, 0),
    'right': (lid_vert_delta, 0)
}

# Zwinker-Variablen
blink_timer = 0
blink_duration = 100
blink_interval = np.random.normal(6000, 2500) #Setze Blink-Interval auf Zufalls wert 6s +-3
is_blinking = False

# Bewegungskontrolle
looking_up = False
looking_down = False
looking_left = False
looking_right = False

movements_index = 0

font = pygame.font.SysFont(None, 32)  # You can specify font name instead of None

def draw_brows():
    brow_offset=[0,0]
    if looking_up:
        brow_offset[1] = brow_delta['up'][1]
    if looking_down or is_blinking:
        brow_offset[1] = brow_delta['down'][1]
    # Brows horizontal movement
    if looking_left:
        brow_offset[0] = brow_delta['left'][0]
    if looking_right:
        brow_offset[0] = brow_delta['right'][0]

    BROW1 = None
    BROW2 = None

    #Brow
    if not looking_down and not looking_up and not looking_right and not looking_left and not is_blinking:
        BROW1  = pygame.Rect((eye_left_pos[0]-50, 100), (eye_radius_*1.3, 200))
        BROW2  = pygame.Rect((eye_right_pos[0]-50, 100), (eye_radius_*1.3, 200))
    elif looking_down or is_blinking:
        BROW1  = pygame.Rect((eye_left_pos[0]-50+brow_offset[0], 100+brow_offset[1]), (eye_radius_*1.3, 50))
        BROW2  = pygame.Rect((eye_right_pos[0]-50+brow_offset[0], 100+brow_offset[1]), (eye_radius_*1.3, 50))
    else:
        BROW1  = pygame.Rect((eye_left_pos[0]-50+brow_offset[0], 100+brow_offset[1]), (eye_radius_*1.3, 200))
        BROW2  = pygame.Rect((eye_right_pos[0]-50+brow_offset[0], 100+brow_offset[1]), (eye_radius_*1.3, 200))

    pygame.draw.arc(screen, LID, BROW1, start_angle=2/6*PI , stop_angle =5.5/6*PI, width=25)
    pygame.draw.arc(screen, LID, BROW2, start_angle=0.5/6*PI , stop_angle =PI-2/6 * PI, width=25)

def draw_mouth():
    MOUTH_RECT = pygame.Rect((WIDTH/2-100, HEIGHT*0.65), (200, 100))
    start_angle = PI
    stop_angle = 0
    width = 15
    radius = width // 2
    
    pygame.draw.arc(screen, MOUTH, MOUTH_RECT, start_angle, stop_angle, width)
   
    # round corners
    start_pos = (MOUTH_RECT.left+radius, MOUTH_RECT.centery)
    end_pos = (MOUTH_RECT.right-radius, MOUTH_RECT.centery)
    pygame.draw.circle(screen, MOUTH, start_pos, radius)
    pygame.draw.circle(screen, MOUTH, end_pos, radius)

def draw_eyes():
    # Augen zeichnen
    pygame.draw.ellipse(screen, WHITE, [eye_left_pos[0],eye_left_pos[1],eye_radius_,eye_radius])
    pygame.draw.ellipse(screen, WHITE, [eye_right_pos[0],eye_right_pos[1],eye_radius_,eye_radius])
    
    # Verdeckungsbox
    if looking_down:
        pygame.draw.rect(screen, BG, (eye_left_pos[0] , eye_left_pos[1] -20, eye_radius_ , eye_radius/2))
        pygame.draw.rect(screen, BG, (eye_right_pos[0] , eye_right_pos[1] -20, eye_radius_ , eye_radius/2))
        
        pygame.draw.ellipse(screen, WHITE, [eye_left_pos[0],eye_left_pos[1]+eye_radius/5,eye_radius_,eye_radius/2])
        pygame.draw.ellipse(screen, WHITE, [eye_right_pos[0],eye_right_pos[1]+eye_radius/5,eye_radius_,eye_radius/2])
        
    if looking_up:
        pygame.draw.rect(screen, BG, (eye_left_pos[0] , eye_left_pos[1] +eye_radius/2+20, eye_radius_ , eye_radius/2))
        pygame.draw.rect(screen, BG, (eye_right_pos[0] , eye_right_pos[1] +eye_radius/2+20, eye_radius_ , eye_radius/2))
        
        pygame.draw.ellipse(screen, WHITE, [eye_left_pos[0],eye_left_pos[1]+eye_radius/4.5,eye_radius_,eye_radius/1.5])
        pygame.draw.ellipse(screen, WHITE, [eye_right_pos[0],eye_right_pos[1]+eye_radius/4.5,eye_radius_,eye_radius/1.5])
            
    # Pupillenposition basierend auf der Blickrichtung
    left_pupil_pos = (eye_left_pos[0] +  eye_radius_ /2 + pupil_offset[0], eye_left_pos[1]+ eye_radius / 2+ pupil_offset[1])
    right_pupil_pos = (eye_right_pos[0] +   eye_radius_ /2 + pupil_offset[0], eye_right_pos[1] +  eye_radius / 2 + pupil_offset[1])
    pygame.draw.circle(screen, BLACK, left_pupil_pos, pupil_radius)
    pygame.draw.circle(screen, BLACK, right_pupil_pos, pupil_radius)
    
    #Mini-Pupille
    left_mini_pupil_pos = (left_pupil_pos[0]+ pupil_offset[0]/2 ,left_pupil_pos[1]+ pupil_offset[1])
    right_mini_pupil_pos = (right_pupil_pos[0]+ pupil_offset[0]/2,right_pupil_pos[1]+ pupil_offset[1])
    
    if (looking_down or looking_up) and (looking_left or looking_right):
        left_mini_pupil_pos = (left_pupil_pos[0]+ 0.71*pupil_offset[0]/2 ,left_pupil_pos[1]+ 0.71*pupil_offset[1])
        right_mini_pupil_pos = (right_pupil_pos[0]+ 0.71*pupil_offset[0]/2,right_pupil_pos[1]+ 0.71*pupil_offset[1])
    # Randomize Richtung von Mini-Pupille wenn augen geradeaus
    if not looking_down and not looking_up and not looking_left and not looking_right:
        left_mini_pupil_pos = (left_pupil_pos[0]+ max_pupil_offsets[1] ,left_pupil_pos[1])
        right_mini_pupil_pos = (right_pupil_pos[0]+ max_pupil_offsets[1],right_pupil_pos[1])
    
    pygame.draw.circle(screen, WHITE, left_mini_pupil_pos, pupil_radius/5)
    pygame.draw.circle(screen, WHITE, right_mini_pupil_pos, pupil_radius/5)


def animate_gaze(coordinates):
    global looking_left, looking_right, looking_up, looking_down, is_blinking, blink_timer, blink_interval, saved_lid_height, lid_height

    looking_left = (coordinates[0] < 0)
    looking_right = (coordinates[0] > 0)
    looking_up = (coordinates[1] < 0)
    looking_down = (coordinates[1] > 0)

    lid_height = (eye_radius if looking_down else 0)

    pupil_offset[0] = coordinates[0]*max_pupil_offsets[0]
    pupil_offset[1] = coordinates[1]*max_pupil_offsets[1]

    screen.fill(BG)
    # Set up text
    text = f"{coordinates[0]}|{coordinates[1]}|{movements_index}"
    text_color = (255, 255, 255)  # White color
    text_surface = font.render(text, True, text_color)
    screen.blit(text_surface, (10,10))

    # Zwinker-Logik Start
    if not is_blinking and current_time - blink_timer > blink_interval:
        is_blinking = True  # Zwinker-Sequenz beginnt
        saved_lid_height = lid_height  # Speichere aktuellen Augenlid-Zustand
        blink_timer = current_time

    # Zwinkern animieren
    if is_blinking:
        # Augen schliessen
        if current_time - blink_timer > blink_duration:  # Augen wieder oeffnen
            lid_height = saved_lid_height  # Augenlider zum urspruenglichen Zustand zurueck
            is_blinking = False  # Zwinker-Sequenz beendet
            blink_interval = np.random.normal(6000, 2500)#Setze Blink-Interval auf Zufalls wert 6s +-3
    else:
        is_blinking = False
        draw_eyes()

    draw_brows()
    draw_mouth()

movements = [
    (random.uniform(-1, 1), random.uniform(-1, 1), 2),
    (random.uniform(-1, 1), random.uniform(-1, 1), 2),
    (random.uniform(-1, 1), random.uniform(-1, 1), 2),
    (random.uniform(-1, 1), random.uniform(-1, 1), 2),
    (random.uniform(-1, 1), random.uniform(-1, 1), 2),
]

current_target = movements[0]
current_pos = [0,0]

# Main loop
base_interval = 3  # Mittelwert (in Sekunden)
std_dev = 1        # Standardabweichung (in Sekunden)
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

    # Smoothly interpolate towards the target position
    current_pos[0] += (current_target[0] - current_pos[0]) * current_target[2]/60
    current_pos[1] += (current_target[1] - current_pos[1]) * current_target[2]/60

    animate_gaze(current_pos)

    # Check if the current position is close enough to the target
    if abs(current_target[0] - current_pos[0]) < 0.01 and abs(current_target[1] - current_pos[1]) < 0.01:
        movements_index = (movements_index + 1) % len(movements)  # Move to the next target
        current_target = movements[movements_index]
    
    pygame.display.flip()
    pygame.time.Clock().tick(TICKS_PER_SECOND)

# Quit Pygame
pygame.quit()