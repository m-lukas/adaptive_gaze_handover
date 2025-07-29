import threading
import requests
import keyboard


SERVER_URL = "http://10.0.0.5:5000/handover"

state = 'ready_for_arrow'
state_lock = threading.Lock()

def send_signal(action: str):
    """POSTs the given action to the server."""
    try:
        resp = requests.post(SERVER_URL, json={'action': action}, timeout=2.0)
        resp.raise_for_status()
        print(f"→ Sent '{action}'")
    except Exception as e:
        print(f"‼️  Failed to send '{action}': {e}")

def on_left(e):
    global state
    with state_lock:
        if state != 'ready_for_arrow':
            return
        state = 'awaiting_space'
    print("left_tray")
    #send_signal('left_tray', args.server)

def on_right(e):
    global state
    with state_lock:
        if state != 'ready_for_arrow':
            return
        state = 'awaiting_space'
    print("right_tray")
    #send_signal('right_tray', args.server)

def on_space(e):
    global state
    with state_lock:
        if state != 'awaiting_space':
            return
        state = 'ready_for_arrow'
    print("object_in_bowl")
    #send_signal('object_in_bowl', args.server)

def main():
    print("Handover client started.")
    print(" ← = left_tray, → = right_tray, space = object_in_bowl")
    print("Press ESC to quit.\n")

    # Install hotkeys
    keyboard.on_press_key('left', on_left, suppress=False)
    keyboard.on_press_key('right', on_right, suppress=False)
    keyboard.on_press_key('space', on_space, suppress=False)

    # Block until ESC
    keyboard.wait('esc')
    print("\nExiting...")

if __name__ == '__main__':
    main()
