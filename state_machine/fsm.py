from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Tuple

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
    ERROR_POSE = "error_pose"
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
    ERROR_POSE = "error_pose"


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
    ERROR_WAITING_LEFT = "error_waiting_left"
    ERROR_WAITING_RIGHT = "error_waiting_right"
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
    Callable[[StateUpdate, CurrentState], bool],
    HandoverState,
    ArmProgram | None,
    GazeProgram | None,
]
GazeTransition = Tuple[
    Callable[[StateUpdate, CurrentState], bool], GazeProgram
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

        self.handover_state_transitions: Dict[HandoverState, List[HandoverTransition]] = {
            HandoverState.NO_ACTIVE_HANDOVER: [
                (
                    lambda u, c: u.handover_start_detected == HandoverInitiatedTray.LEFT,
                    HandoverState.MOVING_TO_PERSON_LEFT,
                    ArmProgram.MOVE_TO_LEFT_HANDOVER,
                    GazeProgram.MOVE_TO_PERSON_LEFT,
                ),
                (
                    lambda u, c: u.handover_start_detected == HandoverInitiatedTray.RIGHT,
                    HandoverState.MOVING_TO_PERSON_RIGHT,
                    ArmProgram.MOVE_TO_RIGHT_HANDOVER,
                    GazeProgram.MOVE_TO_PERSON_RIGHT,
                )
            ],
            HandoverState.MOVING_TO_PERSON_LEFT: [
                (
                    lambda u, c: u.new_arm_location == ArmLocation.HANDOVER_LOCATION,
                    HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                    None,
                    GazeProgram.RECEIVING_LEFT,
                )
            ],
            HandoverState.MOVING_TO_PERSON_RIGHT: [
                (
                    lambda u, c: u.new_arm_location == ArmLocation.HANDOVER_LOCATION,
                    HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                    None,
                    GazeProgram.RECEIVING_RIGHT,
                )
            ],
            HandoverState.WAITING_FOR_RECEIVAL_LEFT: [
                (
                    lambda u, c: u.object_in_bowl == True,
                    HandoverState.MOVING_TO_PACKAGING_LEFT,
                    ArmProgram.MOVE_TO_PACKAGING,
                    GazeProgram.MOVE_TO_PACKAGING_LEFT,
                ),
                    (
                    lambda u, c: u.error_during_handover == True,
                    HandoverState.ERROR_LEFT,
                    ArmProgram.MOVE_TO_ERROR_POSE,
                    GazeProgram.MOVE_TO_ERROR_LEFT,
                )
            ],
            HandoverState.WAITING_FOR_RECEIVAL_RIGHT: [
                (
                    lambda u, c: u.object_in_bowl == True,
                    HandoverState.MOVING_TO_PACKAGING_RIGHT,
                    ArmProgram.MOVE_TO_PACKAGING,
                    GazeProgram.MOVE_TO_PACKAGING_RIGHT,
                ),
                (
                    lambda u, c: u.error_during_handover == True,
                    HandoverState.ERROR_RIGHT,
                    ArmProgram.MOVE_TO_ERROR_POSE,
                    GazeProgram.MOVE_TO_ERROR_RIGHT,
                )
            ],
            HandoverState.ERROR_LEFT: [
                (
                    lambda u, c: u.new_arm_location == ArmLocation.ERROR_POSE,
                    HandoverState.ERROR_WAITING_LEFT,
                    None,
                    GazeProgram.UNSURE,
                )
            ],
            HandoverState.ERROR_RIGHT: [
                (
                    lambda u, c: u.new_arm_location == ArmLocation.ERROR_POSE,
                    HandoverState.ERROR_WAITING_RIGHT,
                    None,
                    GazeProgram.UNSURE,
                )
            ],
            HandoverState.ERROR_WAITING_LEFT: [
                (
                    lambda u, c: u.handover_start_detected == HandoverInitiatedTray.LEFT,
                    HandoverState.MOVING_TO_PERSON_LEFT,
                    ArmProgram.MOVE_TO_LEFT_HANDOVER,
                    GazeProgram.ERROR_TO_PERSON_LEFT,
                ),
                (
                    lambda u, c: u.handover_start_detected == HandoverInitiatedTray.RIGHT,
                    HandoverState.MOVING_TO_PERSON_RIGHT,
                    ArmProgram.MOVE_TO_RIGHT_HANDOVER,
                    GazeProgram.ERROR_TO_PERSON_RIGHT,
                )
            ],
            HandoverState.ERROR_WAITING_RIGHT: [
                (
                    lambda u, c: u.handover_start_detected == HandoverInitiatedTray.LEFT,
                    HandoverState.MOVING_TO_PERSON_LEFT,
                    ArmProgram.MOVE_TO_LEFT_HANDOVER,
                    GazeProgram.ERROR_TO_PERSON_LEFT,
                ),
                (
                    lambda u, c: u.handover_start_detected == HandoverInitiatedTray.RIGHT,
                    HandoverState.MOVING_TO_PERSON_RIGHT,
                    ArmProgram.MOVE_TO_RIGHT_HANDOVER,
                    GazeProgram.ERROR_TO_PERSON_RIGHT,
                )
            ],
            HandoverState.MOVING_TO_PACKAGING_LEFT: [
                (
                    lambda u, c: u.new_arm_location == ArmLocation.PACKAGING,
                    HandoverState.PACKAGING,
                    None,
                    GazeProgram.PACKAGING,
                )
            ],
            HandoverState.MOVING_TO_PACKAGING_RIGHT: [
                (
                    lambda u, c: u.new_arm_location == ArmLocation.PACKAGING,
                    HandoverState.PACKAGING,
                    None,
                    GazeProgram.PACKAGING,
                )
            ],
            HandoverState.PACKAGING: [
                (
                    lambda u, c: u.handover_finished == True,
                    HandoverState.NO_ACTIVE_HANDOVER,
                    None,
                    GazeProgram.MUTUAL,
                ),
                (
                    lambda u, c: u.task_completed == True,
                    HandoverState.TASK_COMPLETED,
                    ArmProgram.IDLE,
                    GazeProgram.MUTUAL,
                )
            ]
        }

        self.dynamic_gaze_transitions: Dict[HandoverState, Dict[GazeProgram, List[GazeTransition]]] = {
            HandoverState.NO_ACTIVE_HANDOVER: {
                GazeProgram.MUTUAL: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.UNSURE,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.UNSURE: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.LEFT_HANDOVER: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL,
                    ),
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.IDLE,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.RIGHT_HANDOVER: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL,
                    ),
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.IDLE,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.IDLE: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.IDLE,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.IDLE,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL,
                    )
                ]
            },
            HandoverState.MOVING_TO_PERSON_LEFT: {
                GazeProgram.MOVE_TO_PERSON_LEFT: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.EMPHASIZE_LEFT,
                    )
                ]
            },
            HandoverState.MOVING_TO_PERSON_RIGHT: {
                GazeProgram.MOVE_TO_PERSON_RIGHT: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.EMPHASIZE_RIGHT,
                    )
                ]
            },
            HandoverState.WAITING_FOR_RECEIVAL_LEFT: {
                GazeProgram.RECEIVING_LEFT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.MUTUAL: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ENSURING_LEFT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.ENSURING_LEFT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    )
                ],
                GazeProgram.ENSURING_LEFT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.RECEIVING_LEFT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.ENSURING_LEFT,
                    )
                ],
                GazeProgram.MUTUAL_SHORT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.RECEIVING_LEFT,
                    )
                ],
                GazeProgram.LEFT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ENSURING_LEFT,
                    )
                ]
            },
            HandoverState.WAITING_FOR_RECEIVAL_RIGHT: {
                GazeProgram.RECEIVING_RIGHT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.MUTUAL: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ENSURING_RIGHT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.ENSURING_RIGHT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    )
                ],
                GazeProgram.ENSURING_RIGHT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.RECEIVING_RIGHT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.ENSURING_RIGHT,
                    )
                ],
                GazeProgram.MUTUAL_SHORT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.RECEIVING_RIGHT,
                    )
                ],
                GazeProgram.RIGHT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ENSURING_RIGHT,
                    )
                ]
            },
            HandoverState.ERROR_LEFT: {
                GazeProgram.MOVE_TO_ERROR_LEFT: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    )
                ],
                GazeProgram.MUTUAL_SHORT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.ERROR_POSE: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.LEFT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    )
                ],
                GazeProgram.RIGHT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    )
                ]
            },
            HandoverState.ERROR_RIGHT: {
                GazeProgram.MOVE_TO_ERROR_RIGHT: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    )
                ],
                GazeProgram.MUTUAL_SHORT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.ERROR_POSE: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.LEFT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    )
                ],
                GazeProgram.RIGHT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.ERROR_POSE,
                    )
                ]
            },
            HandoverState.ERROR_WAITING_LEFT: {
                GazeProgram.MUTUAL_SHORT: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.UNSURE: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    )
                ],
                GazeProgram.LEFT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.RIGHT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ]
            },
            HandoverState.ERROR_WAITING_RIGHT: {
                GazeProgram.MUTUAL_SHORT: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.UNSURE: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    )
                ],
                GazeProgram.LEFT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.RIGHT_HANDOVER: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.LEFT_HANDOVER_LOCATION,
                        GazeProgram.LEFT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_HANDOVER_LOCATION,
                        GazeProgram.RIGHT_HANDOVER,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ]
            },
            HandoverState.MOVING_TO_PACKAGING_LEFT: {
                GazeProgram.MOVE_TO_PACKAGING_LEFT: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.MUTUAL_SHORT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.TRAYS,
                    )
                ],
                GazeProgram.TRAYS: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.PACKAGING_STATIC,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ]
            },
            HandoverState.MOVING_TO_PACKAGING_RIGHT: {
                GazeProgram.MOVE_TO_PACKAGING_RIGHT: [
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.MUTUAL_SHORT: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ],
                GazeProgram.PACKAGING_STATIC: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.TRAYS,
                    )
                ],
                GazeProgram.TRAYS: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.PACKAGING_STATIC,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                        GazeProgram.MUTUAL_SHORT,
                    ),
                    (
                        lambda u, c: u.new_gaze_target == GazeTarget.PACKAGING_AREA,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ]
            },
            HandoverState.PACKAGING: {
                GazeProgram.PACKAGING: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.PACKAGING_STATIC,
                    )
                ]
            },
            HandoverState.TASK_COMPLETED: {
                GazeProgram.MUTUAL: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.IDLE,
                    )
                ],
                GazeProgram.IDLE: [
                    (
                        lambda u, c: u.gaze_program_finished == True,
                        GazeProgram.IDLE,
                    )
                ]
            }
        }

        # static gaze simply maps handover states to gaze program
        self.static_gaze_map = {
            HandoverState.NO_ACTIVE_HANDOVER: GazeProgram.MUTUAL,
            HandoverState.MOVING_TO_PERSON_LEFT: GazeProgram.MOVE_TO_PERSON_LEFT,
            HandoverState.MOVING_TO_PERSON_RIGHT: GazeProgram.MOVE_TO_PERSON_RIGHT,
            HandoverState.WAITING_FOR_RECEIVAL_LEFT: GazeProgram.RECEIVING_LEFT,
            HandoverState.WAITING_FOR_RECEIVAL_RIGHT: GazeProgram.RECEIVING_RIGHT,
            HandoverState.ERROR_LEFT: GazeProgram.MOVE_TO_ERROR_LEFT,
            HandoverState.ERROR_RIGHT: GazeProgram.MOVE_TO_ERROR_RIGHT,
            HandoverState.ERROR_WAITING_LEFT: GazeProgram.UNSURE,
            HandoverState.ERROR_WAITING_RIGHT: GazeProgram.UNSURE,
            HandoverState.MOVING_TO_PACKAGING_LEFT: GazeProgram.MOVE_TO_PACKAGING_LEFT,
            HandoverState.MOVING_TO_PACKAGING_RIGHT: GazeProgram.MOVE_TO_PACKAGING_RIGHT,
            HandoverState.PACKAGING: GazeProgram.PACKAGING,
            HandoverState.TASK_COMPLETED: GazeProgram.IDLE,
        }

    def update_state(self, u: StateUpdate) -> UpdatedState:
        changes = UpdatedState()

        if not u.new_gaze_target and not u.gaze_program_finished:
            for guard, dst_hs, new_arm, new_gaze in self.handover_state_transitions.get(self.state.current_handover_state, []):
                if guard(u, self.state):
                    self.state.current_handover_state = dst_hs
                    changes.handover_state = dst_hs
                    if new_arm is not None:
                        changes.arm_program = new_arm
                    if new_gaze is not None:
                        self.state.current_gaze_program = new_gaze
                        changes.gaze_program = new_gaze
                    break

            if u.new_arm_location:
                self.state.last_arm_location = u.new_arm_location

        if not self.dynamic_gaze and changes.handover_state:
            self.state.current_gaze_program = self.static_gaze_map[
                changes.handover_state
            ]
            changes.gaze_program = self.state.current_gaze_program
            return changes

        if (
            self.dynamic_gaze
            and any([u.new_gaze_target, u.gaze_program_finished])
            and is_time_difference_exceeded(
                self.state.last_gaze_update, GAZE_UPDATE_REFRESH_RATE_MS
            )
        ):
            for guard, next_gp in self.dynamic_gaze_transitions.get(self.state.current_handover_state, {}).get(self.state.current_gaze_program, []):
                if guard(u, self.state):
                    self.state.current_gaze_program = next_gp
                    changes.gaze_program = next_gp
                    break        

            self.state.last_gaze_update = datetime.now()

        return changes
