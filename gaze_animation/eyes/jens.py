import pygame
import sys
import numpy as np
from math import pi as PI
import random
import time


pygame.init()

WIDTH = 1024
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Eye Tracking")

# Colors
RANDOM_MODE = False

# Farben definieren
BG = (35.7,70.2, 74.9)
MOUTH = (73.5,91.5,93.5)
LID = (14.5,47.1,54.1)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKIN = (240, 200, 170)
CYAN= (0,255,255)

bgcolor = BG#(0,76,152)#

WIDTH = 1024
HEIGHT = 600 

# Variablen fuer die Augenposition und Blickrichtung
eye_radius = 200
eye_radius_ = 350
pupil_radius = 50
eye_left_pos = ((1024*0.25)-eye_radius_*0.5, HEIGHT/2 -eye_radius/2 )
eye_right_pos = ((0.75*1024)-eye_radius_*0.5, HEIGHT/2 -eye_radius/2)
pupil_offset = [0,150] 
m_pupil_offset = [75,35]  # Ausweichpos der Pupillen

# Variablen fuer das Augenlid
lid_height = 0  # Hoehe des Augenlids (0 bedeutet offen)
saved_lid_height = 0  # Speichert den Zustand des Augenlids vor dem Zwinkern
lid_hor_delta=10
lid_vert_delta=5

# Definierte Richtungen (x, y) fuer die Pupillenbewegung
directions = {
    'up': (0, -1*m_pupil_offset[1]),
    'down': (0, m_pupil_offset[1]),
    'left': (-1*m_pupil_offset[0], 0),
    'right': (m_pupil_offset[0], 0)
}
lid_delta = {
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

moving_up = False
moving_down = False
moving_left = False
moving_right = False

external_mode= True

def draw_eyes():
    # Augen zeichnen
    #pygame.draw.circle(screen, BLACK, eye_left_pos, eye_radius, 3)
    if not is_blinking:
        pygame.draw.ellipse(screen, WHITE, [eye_left_pos[0],eye_left_pos[1],eye_radius_,eye_radius])
        #pygame.draw.circle(screen, BLACK, eye_right_pos, eye_radius, 3)
        pygame.draw.ellipse(screen, WHITE, [eye_right_pos[0],eye_right_pos[1],eye_radius_,eye_radius])
        
        # Verdeckungsbox
        if  moving_down:
            pygame.draw.rect(screen, bgcolor, (eye_left_pos[0] , eye_left_pos[1] -20, eye_radius_ , eye_radius/2))
            pygame.draw.rect(screen, bgcolor, (eye_right_pos[0] , eye_right_pos[1] -20, eye_radius_ , eye_radius/2))
            
            pygame.draw.ellipse(screen, WHITE, [eye_left_pos[0],eye_left_pos[1]+eye_radius/5,eye_radius_,eye_radius/2])
            pygame.draw.ellipse(screen, WHITE, [eye_right_pos[0],eye_right_pos[1]+eye_radius/5,eye_radius_,eye_radius/2])
            
        if  moving_up:
            pygame.draw.rect(screen, bgcolor, (eye_left_pos[0] , eye_left_pos[1] +eye_radius/2+20, eye_radius_ , eye_radius/2))
            pygame.draw.rect(screen, bgcolor, (eye_right_pos[0] , eye_right_pos[1] +eye_radius/2+20, eye_radius_ , eye_radius/2))
            
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
        
        if (moving_down or moving_up) and (moving_left or moving_right):
            left_mini_pupil_pos = (left_pupil_pos[0]+ 0.71*pupil_offset[0]/2 ,left_pupil_pos[1]+ 0.71*pupil_offset[1])
            right_mini_pupil_pos = (right_pupil_pos[0]+ 0.71*pupil_offset[0]/2,right_pupil_pos[1]+ 0.71*pupil_offset[1])
        # Randomize Richtung von Mini-Pupille wenn augen geradeaus
        if not moving_down and not moving_up and not moving_left and not moving_right:
            left_mini_pupil_pos = (left_pupil_pos[0]+ m_pupil_offset[1] ,left_pupil_pos[1])
            right_mini_pupil_pos = (right_pupil_pos[0]+ m_pupil_offset[1],right_pupil_pos[1])
        
        pygame.draw.circle(screen, WHITE, left_mini_pupil_pos, pupil_radius/5)
        pygame.draw.circle(screen, WHITE, right_mini_pupil_pos, pupil_radius/5)
     
     
    #else: 
        #pygame.draw.ellipse(screen, WHITE, [eye_left_pos[0],eye_left_pos[1],eye_radius_,0])
        #pygame.draw.ellipse(screen, WHITE, [eye_right_pos[0],eye_right_pos[1],eye_radius_,0])
        
             
    #Brow / Lid
    if not moving_down and not moving_up and not moving_right and not moving_left and not is_blinking:
        if moving_down:
            RECT1  = pygame.Rect((eye_left_pos[0]-50, 0), (eye_radius_*1.5, 50))    
            RECT2  = pygame.Rect((eye_right_pos[0]-125, 100), (eye_radius_*1.5, 50))  
        else :             
            RECT1  = pygame.Rect((eye_left_pos[0]-50, 100), (eye_radius_*1.3, 200))    
            RECT2  = pygame.Rect((eye_right_pos[0]-50, 100), (eye_radius_*1.3, 200))  
        #Draw lids    
        pygame.draw.arc(screen, LID, RECT1, start_angle=2/6*PI , stop_angle =5.5/6*PI, width=25)              
        pygame.draw.arc(screen, LID, RECT2, start_angle=0.5/6*PI , stop_angle =PI-2/6 * PI, width=25) 
    
    lid_offset=[0,0]
    if moving_up:
        lid_offset[1] = lid_delta['up'][1]
    if moving_down or is_blinking:
        lid_offset[1] = lid_delta['down'][1]
    if moving_left:
        lid_offset[0] = lid_delta['left'][0]
    if moving_right:
        lid_offset[0] = lid_delta['right'][0]
        
    #Draw lids   
      
    
    RECT1  = pygame.Rect((eye_left_pos[0]-50+lid_offset[0], 100+lid_offset[1]), (eye_radius_*1.3, 200))    
    RECT2  = pygame.Rect((eye_right_pos[0]-50+lid_offset[0], 100+lid_offset[1]), (eye_radius_*1.3, 200))   
    
    if moving_down or is_blinking:
        RECT1  = pygame.Rect((eye_left_pos[0]-50+lid_offset[0], 100+lid_offset[1]), (eye_radius_*1.3, 50))    
        RECT2  = pygame.Rect((eye_right_pos[0]-50+lid_offset[0], 100+lid_offset[1]), (eye_radius_*1.3, 50))  
    
    pygame.draw.arc(screen, LID, RECT1, start_angle=2/6*PI , stop_angle =5.5/6*PI, width=25) 
    pygame.draw.arc(screen, LID, RECT2, start_angle=0.5/6*PI , stop_angle =PI-2/6 * PI, width=25) 
    
   
    #Draw Mouth
    RECT = pygame.Rect((415, 400), (200, 100))
    start_angle = PI
    stop_angle = 0
    width = 15
    radius = width // 2
    
    pygame.draw.arc(screen, MOUTH, RECT, start_angle, stop_angle, width)
    # Ecken abrunden
    start_pos = (RECT.left+radius, RECT.centery)  # Startpunkt des Arcs
    end_pos = (RECT.right-radius, RECT.centery)  # Endpunkt des Arcs

    # Runde Enden zeichnen
    pygame.draw.circle(screen, MOUTH, start_pos, radius)
    pygame.draw.circle(screen, MOUTH, end_pos, radius)

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

    if RANDOM_MODE == True :
        
        if curr_t - last_update_time >= next_update_interval:
            moving_down = random.choice([True, False])
            moving_up = random.choice([True, False])
            moving_left = random.choice([True, False])
            moving_right = random.choice([True, False])
            
            if moving_up & moving_down:
                moving_up = False
                moving_down = False
            if moving_left & moving_right:
                moving_left = False
                moving_right = False    
            
            
            
            last_update_time = curr_t
            next_update_interval = max(0, random.gauss(base_interval, std_dev))
    
    else:    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Tastensteuerung fuer die Blickrichtung
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    moving_up = True
                    moving_down = False
                    lid_height = 0  # Augen voll offen
                elif event.key == pygame.K_DOWN:
                    moving_down = True
                    moving_up = False
                    lid_height = eye_radius  # Augen halb geschlossen
                elif event.key == pygame.K_LEFT:
                    moving_left = True
                    moving_right = False
                elif event.key == pygame.K_RIGHT:
                    moving_right = True
                    moving_left = False

            # Steuerung, wenn die Taste losgelassen wird (zur Mitte zurueckfuehren)
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    moving_up = False
                if event.key == pygame.K_DOWN:
                    moving_down = False
                if event.key == pygame.K_LEFT:
                    moving_left = False
                if event.key == pygame.K_RIGHT:
                    moving_right = False

    # Bewegung der Pupillen
    if moving_up:
        pupil_offset[1] = directions['up'][1]
    elif moving_down:
        pupil_offset[1] = directions['down'][1]
    else:
        pupil_offset[1] = 0  # Zur Mitte zurueckkehren (vertikal)
        if not moving_down:  # Wenn der Blick nicht nach unten geht
            lid_height = 0  # Augen oeffnen beim Zurueckkehren in die Mitte

    if moving_left:
        pupil_offset[0] = directions['left'][0]
    elif moving_right:
        pupil_offset[0] = directions['right'][0]
    else:
        pupil_offset[0] = 0  # Zur Mitte zurueckkehren (horizontal)

    # Zwinker-Logik Start
    if not is_blinking and current_time - blink_timer > blink_interval:
        is_blinking = True  # Zwinker-Sequenz beginnt
        saved_lid_height = lid_height  # Speichere aktuellen Augenlid-Zustand
        blink_timer = current_time

    # Zwinkern animieren
    if is_blinking:
        # Augen schliessen
        #if current_time - blink_timer < 100:  # Erstes Zwinkern (100 ms)
        #    lid_height = eye_radius * 2  # Augen komplett schliessen
        if current_time - blink_timer > blink_duration:  # Augen wieder oeffnen
            lid_height = saved_lid_height  # Augenlider zum urspruenglichen Zustand zurueck
            is_blinking = False  # Zwinker-Sequenz beendet
            blink_interval = np.random.normal(6000, 2500)#Setze Blink-Interval auf Zufalls wert 6s +-3


    screen.fill(bgcolor)
    # Augen und Pupillen zeichnen
    draw_eyes()
    pygame.display.flip()
    pygame.time.Clock().tick(60)

# Quit Pygame
pygame.quit()