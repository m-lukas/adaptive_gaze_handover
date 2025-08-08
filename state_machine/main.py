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


participant_identifier=os.getenv("PARTICIPANT_IDENTIFIER", str(uuid.uuid4()))
dynamic_gaze=os.getenv("DYNAMIC_GAZE", "false").lower() == "true"
demonstration=os.getenv("DEMONSTRATION", "false").lower() == "true"

app = FastAPI()
sm = StateMachine(dynamic_gaze=dynamic_gaze)

logger = DataLogger(participant_identifier=participant_identifier, dynamic_gaze=dynamic_gaze, file_name=participant_identifier, demonstration=demonstration)

@app.on_event("startup")
async def startup_event():
    print("Starting State Machine ...\n")
    print(f"Identifier: {participant_identifier}")
    print(f"Dynamic Gaze: {dynamic_gaze}")
    print(f"Demonstration: {demonstration}")

@app.on_event("shutdown")
def shutdown_event():
    logger.write_files()

class ConfigPayload(BaseModel):
    participant_identifier: str | None
    dynamic_gaze: bool | None
    demonstration: bool | None

class GazeTargetPayload(BaseModel):
    target: GazeTarget

class ArmLocationPayload(BaseModel):
    location: ArmLocation

class EventPayload(BaseModel):
    name: str  # must be "handover_start_detected" or "object_in_bowl"

@app.post("/config", status_code=202)
async def change_config(data: ConfigPayload):
    if data.participant_identifier:
        participant_identifier = data.participant_identifier

    return {"status": "accepted"}

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
    elif data.name == "handover_finished":
        upd = StateUpdate(handover_finished=True)
    elif data.name == "gaze_program_finished":
        upd = StateUpdate(gaze_program_finished=True)
    elif data.name == "task_completed":
        logger.log_task_completed()
        upd = StateUpdate(task_completed=True)
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
