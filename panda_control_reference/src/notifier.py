import requests

STATE_MACHINE_URL   = "http://0.0.0.0:1111"

def notify_arm_location(arm_location: str):
    try:
        requests.post(f"{STATE_MACHINE_URL}/arm_location", json={"location": arm_location}, timeout=0.5)
        print("Sending to state machine:", arm_location)
    except Exception as e:
        print("ERROR while sending data to state machine: ", str(e))
        pass


def notify_handover_finished():
    try:
        requests.post(f"{STATE_MACHINE_URL}/event", json={"name": "handover_finished"}, timeout=0.5)
        print("Sending event to state machine: handover_finished")
    except Exception as e:
        print("ERROR while sending data to state machine: ", str(e))
        pass


def notify_task_completed():
    try:
        requests.post(f"{STATE_MACHINE_URL}/event", json={"name": "task_completed"}, timeout=0.5)
        print("Sending event to state machine: task_completed")
    except Exception as e:
        print("ERROR while sending data to state machine: ", str(e))
        pass
