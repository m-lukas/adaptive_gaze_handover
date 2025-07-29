import argparse
import sys
import requests
import pygame

SERVER_URL = ""

# States
READY_FOR_ARROW = 0
AWAITING_SPACE = 1

def send_signal(action: str):
    """POSTs the given action to the server."""
    print(action)
    # try:
    #     resp = requests.post(server_url, json={'action': action}, timeout=2.0)
    #     resp.raise_for_status()
    #     print(f"→ Sent '{action}'")
    # except Exception as e:
    #     print(f"‼️  Failed to send '{action}': {e}")

def main():
    print("Handover client started.")
    print("← = left_tray, → = right_tray, space = object_in_bowl, ESC = quit\n")

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
                    send_signal('left_tray')
                    state = AWAITING_SPACE

                elif event.key == pygame.K_RIGHT and state == READY_FOR_ARROW:
                    send_signal('right_tray')
                    state = AWAITING_SPACE

                elif event.key == pygame.K_SPACE and state == AWAITING_SPACE:
                    send_signal('object_in_bowl')
                    state = READY_FOR_ARROW

        # cap the loop to 30fps to reduce CPU usage
        clock.tick(30)

    pygame.quits()
    print("Exited.")

if __name__ == '__main__':
    main()
