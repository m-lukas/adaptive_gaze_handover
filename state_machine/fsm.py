from datetime import datetime
from enum import Enum
from typing import Callable, List, Tuple

from util import is_time_difference_exceeded


GAZE_UPDATE_REFRESH_RATE_MS = 400


class GazeProgram(Enum):
    IDLE = "idle"
    MOVE_TO_PERSON_LEFT = "move_to_person_left"
    MOVE_TO_PERSON_RIGHT = "move_to_person_right"
    RECEIVING_LEFT = "receiving_left"
    RECEIVING_RIGHT = "receiving_right"
    EMPHASIZE_LEFT = "emphasize_left"
    EMPHASIZE_RIGHT = "emphasize_right"
    MOVE_TO_PACKAGING_LEFT = "move_to_packaging_left"
    MOVE_TO_PACKAGING_RIGHT = "move_to_packaging_right"
    PACKAGING_STATIC = "packaging_static"
    MOVE_TO_ERROR_LEFT = "move_to_error_left"
    MOVE_TO_ERROR_RIGHT = "move_to_error_right"
    ERROR_TO_PERSON_LEFT = "error_to_person_left"
    ERROR_TO_PERSON_RIGHT = "error_to_person_right"
    UNSURE = "unsure"
    MUTUAL = "mutual"
    LEFT_HANDOVER = "gaze_left_handover"
    RIGHT_HANDOVER = "gaze_right_handover"
    ENSURING_LEFT = "ensuring_left"
    ENSURING_RIGHT = "ensuring_right"
    MUTUAL_SHORT = "mutual_short"
    TRAYS = "trays"
    PACKAGING = "packaging"


class GazeTarget(Enum):
    ROBOT_FACE = "robot_face"
    PACKAGING_AREA = "packaging_area"
    LEFT_TRAY = "left_tray"
    RIGHT_TRAY = "right_tray"
    LEFT_HANDOVER_LOCATION = "left_handover_location"
    RIGHT_HANDOVER_LOCATION = "right_handover_location"
    UNDEFINED = "undefined"


class ArmLocation(Enum):
    HANDOVER_LOCATION = "handover_location"
    PACKAGING = "packaging"
    IDLE = "idle"


class ArmProgram(Enum):
    MOVE_TO_LEFT_HANDOVER = "move_to_left_tray"
    MOVE_TO_RIGHT_HANDOVER = "move_to_right_tray"
    MOVE_TO_ERROR_POSE = "move_to_error_pose"
    MOVE_TO_PACKAGING = "move_to_packaging"
    IDLE = "move_to_idle"


class HandoverState(Enum):
    NO_ACTIVE_HANDOVER = "no_active_handover"
    MOVING_TO_PERSON_LEFT = "moving_to_person_left"
    MOVING_TO_PERSON_RIGHT = "moving_to_person_right"
    WAITING_FOR_RECEIVAL_LEFT = "waiting_for_receival_left"
    WAITING_FOR_RECEIVAL_RIGHT = "waiting_for_receival_right"
    ERROR_LEFT = "error_left"
    ERROR_RIGHT = "error_right"
    MOVING_TO_PACKAGING_LEFT = "moving_to_packaging_left"
    MOVING_TO_PACKAGING_RIGHT = "moving_to_packaging_right"
    PACKAGING = "packaging"
    TASK_COMPLETED = "task_completed"


class HandoverInitiatedTray(Enum):
    LEFT = "left"
    RIGHT = "right"


class StateUpdate:
    def __init__(
        self,
        handover_start_detected: HandoverInitiatedTray | None = None,
        handover_finished: bool | None = None,
        object_in_bowl: bool | None = None,
        error_during_handover: bool | None = None,
        new_arm_location: ArmLocation | None = None,
        gaze_program_finished: bool | None = None,
        new_gaze_target: GazeTarget | None = None,
        task_completed: bool | None = None,
    ):
        self.handover_start_detected = handover_start_detected
        self.handover_finished = handover_finished
        self.object_in_bowl = object_in_bowl
        self.error_during_handover = error_during_handover
        self.gaze_program_finished = gaze_program_finished
        self.new_arm_location = new_arm_location
        self.new_gaze_target = new_gaze_target
        self.task_completed = task_completed


class CurrentState:
    def __init__(
        self,
        current_handover_state: HandoverState,
        current_gaze_program: GazeProgram,
        last_arm_location: ArmLocation,
        last_gaze_update: datetime,
    ):
        self.current_handover_state = current_handover_state
        self.current_gaze_program = current_gaze_program
        self.last_arm_location = last_arm_location
        self.last_gaze_update = last_gaze_update


class UpdatedState:
    def __init__(
        self,
        gaze_program: GazeProgram | None = None,
        arm_program: ArmProgram | None = None,
        handover_state: HandoverState | None = None,
    ):
        self.gaze_program = gaze_program
        self.arm_program = arm_program
        self.handover_state = handover_state


HandoverTransition = Tuple[
    HandoverState,
    Callable[[StateUpdate, CurrentState], bool],
    HandoverState,
    ArmProgram | None,
    GazeProgram | None,
]
GazeTransition = Tuple[
    HandoverState, GazeProgram, Callable[[StateUpdate, CurrentState], bool], GazeProgram
]


class StateMachine:
    def __init__(self, dynamic_gaze: bool):
        self.dynamic_gaze = dynamic_gaze

        self.state = CurrentState(
            current_handover_state=HandoverState.NO_ACTIVE_HANDOVER,
            current_gaze_program=GazeProgram.IDLE,
            last_arm_location=ArmLocation.IDLE,
            last_gaze_update=datetime.now(),
        )

        self.handover_transitions: List[HandoverTransition] = [
            # HS_NO_ACTIVE_HANDOVER
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                lambda u, c: u.handover_start_detected == HandoverInitiatedTray.LEFT,
                HandoverState.MOVING_TO_PERSON_LEFT,
                ArmProgram.MOVE_TO_LEFT_HANDOVER,
                GazeProgram.MOVE_TO_PERSON_LEFT,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                lambda u, c: u.handover_start_detected == HandoverInitiatedTray.RIGHT,
                HandoverState.MOVING_TO_PERSON_RIGHT,
                ArmProgram.MOVE_TO_RIGHT_HANDOVER,
                GazeProgram.MOVE_TO_PERSON_RIGHT,
            ),
            # HS_MOVING_TO_PERSON_LEFT
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                lambda u, c: u.new_arm_location == ArmLocation.HANDOVER_LOCATION,
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                None,
                GazeProgram.RECEIVING_LEFT,
            ),
            # HS_MOVING_TO_PERSON_RIGHT
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                lambda u, c: u.new_arm_location == ArmLocation.HANDOVER_LOCATION,
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                None,
                GazeProgram.RECEIVING_RIGHT,
            ),
            # HS_WAITING_FOR_RECEIVAL_LEFT
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                lambda u, c: u.object_in_bowl == True,
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                ArmProgram.MOVE_TO_PACKAGING,
                GazeProgram.MOVE_TO_PACKAGING_LEFT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                lambda u, c: u.error_during_handover == True,
                HandoverState.ERROR_LEFT,
                ArmProgram.MOVE_TO_ERROR_POSE,
                GazeProgram.MOVE_TO_ERROR_LEFT,
            ),
            # HS_WAITING_FOR_RECEIVAL_RIGHT
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                lambda u, c: u.object_in_bowl == True,
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                ArmProgram.MOVE_TO_PACKAGING,
                GazeProgram.MOVE_TO_PACKAGING_RIGHT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                lambda u, c: u.error_during_handover == True,
                HandoverState.ERROR_RIGHT,
                ArmProgram.MOVE_TO_ERROR_POSE,
                GazeProgram.MOVE_TO_ERROR_RIGHT,
            ),
            # HS_ERROR_LEFT
            (
                HandoverState.ERROR_LEFT,
                lambda u, c: u.handover_start_detected == HandoverInitiatedTray.LEFT,
                HandoverState.MOVING_TO_PERSON_LEFT,
                ArmProgram.MOVE_TO_LEFT_HANDOVER,
                GazeProgram.ERROR_TO_PERSON_LEFT,
            ),
            (
                HandoverState.ERROR_LEFT,
                lambda u, c: u.handover_start_detected == HandoverInitiatedTray.RIGHT,
                HandoverState.MOVING_TO_PERSON_RIGHT,
                ArmProgram.MOVE_TO_RIGHT_HANDOVER,
                GazeProgram.ERROR_TO_PERSON_RIGHT,
            ),
            # HS_ERROR_RIGHT
            (
                HandoverState.ERROR_RIGHT,
                lambda u, c: u.handover_start_detected == HandoverInitiatedTray.LEFT,
                HandoverState.MOVING_TO_PERSON_LEFT,
                ArmProgram.MOVE_TO_LEFT_HANDOVER,
                GazeProgram.ERROR_TO_PERSON_LEFT,
            ),
            (
                HandoverState.ERROR_RIGHT,
                lambda u, c: u.handover_start_detected == HandoverInitiatedTray.RIGHT,
                HandoverState.MOVING_TO_PERSON_RIGHT,
                ArmProgram.MOVE_TO_RIGHT_HANDOVER,
                GazeProgram.ERROR_TO_PERSON_RIGHT,
            ),
            # HS_MOVING_TO_PACKAGING_LEFT
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                lambda u, c: u.new_arm_location == ArmLocation.PACKAGING,
                HandoverState.PACKAGING,
                None,
                GazeProgram.PACKAGING,
            ),
            # HS_MOVING_TO_PACKAGING_RIGHT
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                lambda u, c: u.new_arm_location == ArmLocation.PACKAGING,
                HandoverState.PACKAGING,
                None,
                GazeProgram.PACKAGING,
            ),
            # HS_PACKAGING
            (
                HandoverState.PACKAGING,
                lambda u, c: u.handover_finished == True,
                HandoverState.NO_ACTIVE_HANDOVER,
                None,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.PACKAGING,
                lambda u, c: u.task_completed == True,
                HandoverState.TASK_COMPLETED,
                ArmProgram.IDLE,
                GazeProgram.MUTUAL,
            )
        ]

        self.dynamic_gaze_transitions: List[GazeTransition] = [
            # HS_NO_ACTIVE_HANDOVER
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.UNSURE,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.IDLE,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.IDLE,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.IDLE,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.IDLE,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.IDLE,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            # HS_MOVING_TO_PERSON_LEFT
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                GazeProgram.MOVE_TO_PERSON_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.EMPHASIZE_LEFT,
            ),
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                GazeProgram.MOVE_TO_PERSON_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.EMPHASIZE_LEFT,
            ),
            # HS_MOVING_TO_PERSON_RIGHT
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                GazeProgram.MOVE_TO_PERSON_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.EMPHASIZE_RIGHT,
            ),
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                GazeProgram.MOVE_TO_PERSON_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.EMPHASIZE_RIGHT,
            ),
            # HS_WAITING_FOR_RECEIVAL_LEFT
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.RECEIVING_LEFT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.RECEIVING_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.ENSURING_LEFT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.ENSURING_LEFT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.ENSURING_LEFT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.RECEIVING_LEFT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.ENSURING_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.ENSURING_LEFT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.RECEIVING_LEFT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.ENSURING_LEFT,
            ),
            # HS_WAITING_FOR_RECEIVAL_RIGHT
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.RECEIVING_RIGHT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.RECEIVING_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.ENSURING_RIGHT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.ENSURING_RIGHT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.ENSURING_RIGHT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.RECEIVING_RIGHT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.ENSURING_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.ENSURING_RIGHT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.RECEIVING_RIGHT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.ENSURING_RIGHT,
            ),
            # HS_ERROR_LEFT
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.MOVE_TO_ERROR_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.MOVE_TO_ERROR_LEFT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.MOVE_TO_ERROR_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.UNSURE,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.UNSURE,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.UNSURE,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.ERROR_LEFT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            # HS_ERROR_RIGHT
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.MOVE_TO_ERROR_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.MOVE_TO_ERROR_RIGHT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.MOVE_TO_ERROR_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.UNSURE,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.UNSURE,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.UNSURE,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.ERROR_RIGHT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            # HS_MOVING_TO_PACKAGING_LEFT
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                GazeProgram.MOVE_TO_PACKAGING_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                GazeProgram.MOVE_TO_PACKAGING_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.TRAYS,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                GazeProgram.TRAYS,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                GazeProgram.TRAYS,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                GazeProgram.TRAYS,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            # HS_MOVING_TO_PACKAGING_RIGHT
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                GazeProgram.MOVE_TO_PACKAGING_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                GazeProgram.MOVE_TO_PACKAGING_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.TRAYS,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                GazeProgram.TRAYS,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                GazeProgram.TRAYS,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                GazeProgram.TRAYS,
                lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                GazeProgram.PACKAGING_STATIC,
            ),
            # HS_PACKAGING
            (
                HandoverState.PACKAGING,
                GazeProgram.PACKAGING,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.PACKAGING_STATIC,
            ),
            (
                HandoverState.PACKAGING,
                GazeProgram.PACKAGING_STATIC,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL_SHORT,
            ),
            (
                HandoverState.PACKAGING,
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.PACKAGING_STATIC,
            ),
            # HS_TASK_COMPLETED
            (
                HandoverState.TASK_COMPLETED,
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.IDLE,
            ),
            (
                HandoverState.TASK_COMPLETED,
                GazeProgram.IDLE,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.IDLE,
            ),
        ]

        # static gaze simply maps handover states to gaze program
        self.static_gaze_map = {
            HandoverState.NO_ACTIVE_HANDOVER: GazeProgram.MUTUAL,
            HandoverState.MOVING_TO_PERSON_LEFT: GazeProgram.MOVE_TO_PERSON_LEFT,
            HandoverState.MOVING_TO_PERSON_RIGHT: GazeProgram.MOVE_TO_PERSON_RIGHT,
            HandoverState.WAITING_FOR_RECEIVAL_LEFT: GazeProgram.RECEIVING_LEFT,
            HandoverState.WAITING_FOR_RECEIVAL_RIGHT: GazeProgram.RECEIVING_RIGHT,
            HandoverState.ERROR_LEFT: GazeProgram.MOVE_TO_ERROR_LEFT,
            HandoverState.ERROR_RIGHT: GazeProgram.MOVE_TO_ERROR_RIGHT,
            HandoverState.MOVING_TO_PACKAGING_LEFT: GazeProgram.MOVE_TO_PACKAGING_LEFT,
            HandoverState.MOVING_TO_PACKAGING_RIGHT: GazeProgram.MOVE_TO_PACKAGING_RIGHT,
            HandoverState.PACKAGING: GazeProgram.PACKAGING,
            HandoverState.TASK_COMPLETED: GazeProgram.IDLE,
        }

    def update_state(self, u: StateUpdate) -> UpdatedState:
        changes = UpdatedState()

        if any(
            [
                u.handover_start_detected,
                u.handover_finished,
                u.object_in_bowl,
                u.error_during_handover,
                u.new_arm_location,
            ]
        ):
            for (
                src,
                guard,
                dst,
                new_arm_prog,
                new_gaze_prog,
            ) in self.handover_transitions:
                if self.state.current_handover_state == src and guard(u, self.state):
                    self.state.current_handover_state = dst
                    changes.handover_state = dst
                    if new_arm_prog is not None:
                        changes.arm_program = new_arm_prog
                    if new_gaze_prog is not None:
                        self.state.current_gaze_program = new_gaze_prog
                        changes.gaze_program = new_gaze_prog
                    break

            if u.new_arm_location:
                self.state.last_arm_location = u.new_arm_location

            if not self.dynamic_gaze and changes.handover_state:
                self.state.current_gaze_program = self.static_gaze_map[
                    changes.handover_state
                ]
                changes.gaze_program = self.state.current_gaze_program

            if (
                u.handover_start_detected and
                changes.handover_state == None and
                self.state.current_handover_state == HandoverState.PACKAGING
            ):
                self.state.initiated_handover_waiting = u.handover_start_detected

            if (
                changes.handover_state in [HandoverState.MOVING_TO_PERSON_LEFT, HandoverState.MOVING_TO_PERSON_RIGHT, HandoverState.NO_ACTIVE_HANDOVER]
            ):
                self.state.initiated_handover_waiting = None

        if (
            self.dynamic_gaze
            and any([u.new_gaze_target, u.gaze_program_finished])
            and is_time_difference_exceeded(
                self.state.last_gaze_update, GAZE_UPDATE_REFRESH_RATE_MS
            )
        ):
            for (
                curr_hs,
                curr_gaze_prog,
                guard,
                gaze_dst,
            ) in self.dynamic_gaze_transitions:
                if (
                    self.state.current_handover_state == curr_hs
                    and self.state.current_gaze_program == curr_gaze_prog
                    and guard(u, self.state)
                ):
                    self.state.current_gaze_program = gaze_dst
                    changes.gaze_program = gaze_dst
                    break

            self.state.last_gaze_update = datetime.now()

        return changes
