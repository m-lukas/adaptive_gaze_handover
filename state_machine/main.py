import os
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from fsm import (
    StateMachine, StateUpdate,
    GazeTarget, ArmLocation, HandoverInitiatedTray
)
from notifier import notify_arm_program, notify_gaze_program
from data_logger import DataLogger


PARTICIPANT_IDENTIFIER=os.getenv("PARTICIPANT_IDENTIFIER", str(uuid.uuid4())) 


app = FastAPI()
sm = StateMachine(dynamic_gaze=True)

logger = DataLogger(demonstration=True, file_name=PARTICIPANT_IDENTIFIER)

@app.on_event("shutdown")
def shutdown_event():
    logger.write_files()

class GazeTargetPayload(BaseModel):
    target: GazeTarget

class ArmLocationPayload(BaseModel):
    location: ArmLocation

class EventPayload(BaseModel):
    name: str  # must be "handover_start_detected" or "object_in_bowl"

@app.post("/gaze_target", status_code=202)
async def update_gaze_target(data: GazeTargetPayload, bg: BackgroundTasks):
    logger.log_gaze_target(data.target.value)
    upd = StateUpdate(new_gaze_target=data.target)
    bg.add_task(_process_update, upd)
    return {"status": "accepted"}

@app.post("/event", status_code=202)
async def trigger_event(data: EventPayload, bg: BackgroundTasks):
    if data.name == "handover_start_detected_left":
        logger.log_handover_initiation()
        upd = StateUpdate(handover_start_detected=HandoverInitiatedTray.LEFT)
    elif data.name == "handover_start_detected_right":
        logger.log_handover_initiation()
        upd = StateUpdate(handover_start_detected=HandoverInitiatedTray.RIGHT)
    elif data.name == "object_in_bowl":
        logger.log_object_in_bowl()
        upd = StateUpdate(object_in_bowl=True)
    elif data.name == "error_during_handover":
        logger.log_handover_error()
        upd = StateUpdate(error_during_handover=True)
    elif data.name == "gaze_program_finished":
        upd = StateUpdate(gaze_program_finished=True)
    elif data.name == "handover_finished":
        logger.log_handover_finished()
        upd = StateUpdate(handover_finished=True)
    else:
        raise HTTPException(status_code=400, detail="unknown event")
    bg.add_task(_process_update, upd)
    return {"status": "accepted"}

@app.post("/arm_location", status_code=202)
async def update_arm_location(data: ArmLocationPayload, bg: BackgroundTasks):
    upd = StateUpdate(new_arm_location=data.location)
    bg.add_task(_process_update, upd)
    return {"status": "accepted"}

def _process_update(update: StateUpdate):
    changes = sm.update_state(update)
    if changes.arm_program:
        notify_arm_program(changes.arm_program)
    if changes.gaze_program:
        notify_gaze_program(changes.gaze_program)
