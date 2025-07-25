from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from state_machine import (
    StateMachine, StateUpdate,
    GazeTarget, ArmLocation, HandoverInitiatedTray
)
from notifier import notify_arm_program, notify_gaze_program

app = FastAPI()
sm = StateMachine(dynamic_gaze=True)

class GazeTargetPayload(BaseModel):
    target: GazeTarget

class ArmLocationPayload(BaseModel):
    location: ArmLocation

class EventPayload(BaseModel):
    name: str  # must be "handover_start_detected" or "object_in_bowl"

@app.post("/gaze_target", status_code=202)
async def update_gaze_target(data: GazeTargetPayload, bg: BackgroundTasks):
    upd = StateUpdate(new_gaze_target=data.target)
    bg.add_task(_process_update, upd)
    return {"status": "accepted"}

@app.post("/event", status_code=202)
async def trigger_event(data: EventPayload, bg: BackgroundTasks):
    if data.name == "handover_start_detected_left":
        upd = StateUpdate(handover_start_detected=HandoverInitiatedTray.LEFT)
    elif data.name == "handover_start_detected_left":
        upd = StateUpdate(handover_start_detected=HandoverInitiatedTray.RIGHT)
    elif data.name == "object_in_bowl":
        upd = StateUpdate(object_in_bowl=True)
    else:
        raise HTTPException(status_code=400, detail="unknown event")
    bg.add_task(_process_update, upd)
    return {"status": "accepted"}

@app.post("/arm_location", status_code=202)
async def update_arm_location(data: ArmLocationPayload, bg: BackgroundTasks):
    upd = StateUpdate(new_arm_location=data.location)
    bg.add_task(_process_update, upd)
    return {"status": "accepted"}

@app.post("/handover_finished", status_code=202)
async def update_handover_finished(bg: BackgroundTasks):
    upd = StateUpdate(handover_finished=True)
    bg.add_task(_process_update, upd)
    return {"status": "accepted"}

def _process_update(update: StateUpdate):
    changes = sm.update_state(update)
    if changes.arm_program:
        notify_arm_program(changes.arm_program)
    if changes.gaze_program:
        notify_gaze_program(changes.gaze_program)
