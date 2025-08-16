import requests

STATE_MACHINE_URL = "http://0.0.0.0:1111/event"

def notify_gaze_program_finished():
    try:
        requests.post(STATE_MACHINE_URL, json={"name": "gaze_program_finished"}, timeout=0.5)
        print("Sent to state machine: gaze_program_finished")
    except Exception as e:
        print("ERROR while sending data to state_machine: ", str(e))
        raise


def notify_keyboard_event(event_name: str):
    try:
        resp = requests.post(STATE_MACHINE_URL, json={"name": event_name}, timeout=0.5)
        resp.raise_for_status()
        print(f"Sent to state machine: {event_name}")
    except Exception as e:
        print("ERROR while sending data to state_machine: ", str(e))
        pass
