import requests
from state_machine import ArmProgram, GazeProgram

ROBOT_CONTROLLER_URL = "http://0.0.0.0:3333/start"
GAZE_ANIMATION_URL   = "http://0.0.0.0:2222/trigger"

def notify_arm_program(prog: ArmProgram):
    try:
        requests.post(ROBOT_CONTROLLER_URL, json={"program": prog.value}, timeout=0.5)
        print("To Robot Controller:", "{'program':", prog.value, "}")
    except Exception as e:
        print("ERROR while sending data to robot controller: ", str(e))
        pass  # log or retry as you wish

def notify_gaze_program(prog: GazeProgram):
    try:
        requests.post(GAZE_ANIMATION_URL, json={"program": prog.value}, timeout=0.5)
        print("To Gaze Animation:", "{'program':", prog.value, "}")
    except Exception as e:
        print("ERROR while sending data to gaze animation: ", str(e))
        pass
