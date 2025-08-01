import argparse
import sys
import requests
import pygame

SERVER_URL = "http://0.0.0.0:1111/event"

# States
READY_FOR_ARROW = 0
AWAITING_SPACE = 1

def send_signal(event: str):
    """Sends the triggered event to the server."""
    print("Triggered:", event)
    try:
        resp = requests.post(SERVER_URL, json={"name": event}, timeout=0.5)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to send '{event}' to server - Error: {e}")

def main():
    print("left arrow = left_tray, right arrow = right_tray, space = object_in_bowl, ESC = quit\n")

    # pygame in headless mode
    pygame.init()
    pygame.display.init()
    # create a window just to capture input
    pygame.display.set_mode((1, 1))#, pygame.HIDDEN)

    state = READY_FOR_ARROW
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_LEFT and state == READY_FOR_ARROW:
                    send_signal("handover_start_detected_left")
                    state = AWAITING_SPACE

                elif event.key == pygame.K_RIGHT and state == READY_FOR_ARROW:
                    send_signal("handover_start_detected_right")
                    state = AWAITING_SPACE

                elif event.key == pygame.K_SPACE and state == AWAITING_SPACE:
                    send_signal("object_in_bowl")
                    state = READY_FOR_ARROW

        clock.tick(30)

    pygame.quits()

if __name__ == '__main__':
    main()
