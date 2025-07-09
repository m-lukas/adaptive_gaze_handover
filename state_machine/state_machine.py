from datetime import datetime
from enum import Enum
from typing import Callable, List, Tuple

from util import is_time_difference_exceeded


GAZE_UPDATE_REFRESH_RATE_MS = 1000


class GazeProgram(Enum):
    IDLE = "idle"
    MOVE_TO_PERSON_LEFT = "move_to_person_left"
    MOVE_TO_PERSON_RIGHT = "move_to_person_left"
    RECEIVING_LEFT = "receiving_left"
    RECEIVING_RIGHT = "receiving_right"
    MOVE_TO_PACKAGING_LEFT = "move_to_packaging_left"
    MOVE_TO_PACKAGING_RIGHT = "move_to_packaging_right"
    UNSURE = "unsure"
    WAITING = "waiting"
    ENSURING = "ensuring"
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
    MOVING_TO_PERSON = "moving_to_person"
    HANDOVER_LOCATION = "handover_location"
    MOVING_TO_PACKAGING = "moving_to_packaging"
    PACKAGING = "packaging"
    IDLE = "idle"


class ArmProgram(Enum):
    MOVE_TO_LEFT_HANDOVER = "move_to_left_tray"
    MOVE_TO_RIGHT_HANDOVER = "move_to_right_tray"
    MOVE_TO_PACKAGING = "move_to_packaging"
    IDLE = "idle"


class HandoverState(Enum):
    NO_ACTIVE_HANDOVER = "no_active_handover"
    MOVING_TO_PERSON_LEFT = "moving_to_person_left"
    MOVING_TO_PERSON_RIGHT = "moving_to_person_right"
    WAITING_FOR_RECEIVAL_LEFT = "waiting_for_receival_left"
    WAITING_FOR_RECEIVAL_RIGHT = "waiting_for_receival_right"
    MOVING_TO_PACKAGING_LEFT = "moving_to_packaging_left"
    MOVING_TO_PACKAGING_RIGHT = "moving_to_packaging_right"
    PACKAGING = "packaging"


class HandoverInitiatedTray(Enum):
    LEFT = "left"
    RIGHT = "right"


class StateUpdate:
    def __init__(
        self,
        handover_start_detected: HandoverInitiatedTray | None = None,
        handover_finished: bool | None = None,
        object_in_bowl: bool | None = None,
        new_arm_location: ArmLocation | None = None,
        gaze_program_finished: bool | None = None,
        new_gaze_target: GazeTarget | None = None,
    ):
        self.handover_start_detected = handover_start_detected
        self.handover_finished = handover_finished
        self.object_in_bowl = object_in_bowl
        self.gaze_program_finished = gaze_program_finished
        self.new_arm_location = new_arm_location
        self.new_gaze_target = new_gaze_target


class CurrentState:
    def __init__(
        self,
        current_handover_state: HandoverState,
        current_gaze_program: GazeProgram,
        last_arm_location: ArmLocation,
        last_gaze_update: datetime,
        initiated_handover_waiting: HandoverInitiatedTray | None,
    ):
        self.current_handover_state = current_handover_state
        self.current_gaze_program = current_gaze_program
        self.last_arm_location = last_arm_location
        self.last_gaze_update = last_gaze_update
        self.initiated_handover_waiting = initiated_handover_waiting


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
    HandoverState, Callable[[StateUpdate, CurrentState], bool], HandoverState, ArmProgram | None, GazeProgram | None
]
GazeTransition = Tuple[
    HandoverState, GazeProgram, Callable[[StateUpdate, CurrentState], bool], GazeProgram
]


class StateMachine:
    def __init__(self, dynamic_gaze: bool):
        self.dynamic_gaze = dynamic_gaze

        self.state = CurrentState(
            current_handover_state = HandoverState.NO_ACTIVE_HANDOVER,
            current_gaze_program = GazeProgram.IDLE,
            last_arm_location = ArmLocation.IDLE,
            last_gaze_update = datetime.now(),
            initiated_handover_waiting=None
        )

        self.handover_transitions: List[HandoverTransition] = [
            # HS_NO_ACTIVE_HANDOVER
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                lambda u, c: u.handover_start_detected == HandoverInitiatedTray.LEFT,
                HandoverState.MOVING_TO_PERSON_LEFT,
                ArmProgram.MOVE_TO_LEFT_HANDOVER,
                GazeProgram.MOVE_TO_PERSON_LEFT
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                lambda u, c: u.handover_start_detected == HandoverInitiatedTray.RIGHT,
                HandoverState.MOVING_TO_PERSON_RIGHT,
                ArmProgram.MOVE_TO_RIGHT_HANDOVER,
                GazeProgram.MOVE_TO_PERSON_RIGHT
            ),
            # HS_MOVING_TO_PERSON_LEFT
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                lambda u, c: u.new_arm_location == ArmLocation.HANDOVER_LOCATION,
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                None,
                GazeProgram.RECEIVING_LEFT
            ),
            # HS_MOVING_TO_PERSON_RIGHT
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                lambda u, c: u.new_arm_location == ArmLocation.HANDOVER_LOCATION,
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                None,
                GazeProgram.RECEIVING_RIGHT
            ),
            # HS_WAITING_FOR_RECEIVAL_LEFT
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                lambda u, c: u.object_in_bowl == True,
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                ArmProgram.MOVE_TO_PACKAGING,
                GazeProgram.MOVE_TO_PACKAGING_LEFT
            ),
            # HS_WAITING_FOR_RECEIVAL_RIGHT
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                lambda u, c: u.object_in_bowl == True,
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                ArmProgram.MOVE_TO_PACKAGING,
                GazeProgram.MOVE_TO_PACKAGING_RIGHT
            ),
            # HS_MOVING_TO_PACKAGING_LEFT
            (
                HandoverState.MOVING_TO_PACKAGING_LEFT,
                lambda u, c: u.new_arm_location == ArmLocation.PACKAGING,
                HandoverState.PACKAGING,
                None,
                None
            ),
            # HS_MOVING_TO_PACKAGING_RIGHT
            (
                HandoverState.MOVING_TO_PACKAGING_RIGHT,
                lambda u, c: u.new_arm_location == ArmLocation.PACKAGING,
                HandoverState.PACKAGING,
                None,
                None
            ),
            # HS_PACKAGING
            (
                HandoverState.PACKAGING,
                lambda u, c: u.handover_finished == True and c.initiated_handover_waiting == None,
                HandoverState.NO_ACTIVE_HANDOVER,
                ArmProgram.IDLE,
                GazeProgram.MUTUAL
            ),
            (
                HandoverState.PACKAGING,
                lambda u, c: u.handover_finished == True and c.initiated_handover_waiting == HandoverInitiatedTray.LEFT,
                HandoverState.MOVING_TO_PERSON_LEFT,
                ArmProgram.MOVE_TO_LEFT_HANDOVER,
                GazeProgram.MOVE_TO_PERSON_LEFT
            ),
            (
                HandoverState.PACKAGING,
                lambda u, c: u.handover_finished == True and c.initiated_handover_waiting == HandoverInitiatedTray.RIGHT,
                HandoverState.MOVING_TO_PERSON_RIGHT,
                ArmProgram.MOVE_TO_RIGHT_HANDOVER,
                GazeProgram.MOVE_TO_PERSON_RIGHT
            ), 
        ]

        self.dynamic_gaze_transitions: List[GazeTransition] = [
            # HS_NO_ACTIVE_HANDOVER
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.IDLE,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.UNSURE,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.WAITING,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.WAITING,
                lambda u, c: u.new_gaze_target == GazeTarget.UNDEFINED,
                GazeProgram.IDLE,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.UNSURE,
            ),
            (
                HandoverState.NO_ACTIVE_HANDOVER,
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.IDLE,
            ),
            # HS_MOVING_TO_PERSON_LEFT
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                GazeProgram.MOVE_TO_PERSON_LEFT,
                lambda u, c: u.new_gaze_target in [GazeTarget.RIGHT_TRAY,GazeTarget.RIGHT_HANDOVER_LOCATION],
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                GazeProgram.MOVE_TO_PERSON_LEFT,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.LEFT_HANDOVER,
            ),
            (
                HandoverState.MOVING_TO_PERSON_LEFT,
                GazeProgram.LEFT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL,
            ),
            # HS_MOVING_TO_PERSON_RIGHT
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                GazeProgram.MOVE_TO_PERSON_RIGHT,
                lambda u, c: u.new_gaze_target in [GazeTarget.LEFT_TRAY,GazeTarget.LEFT_HANDOVER_LOCATION],
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                GazeProgram.MOVE_TO_PERSON_RIGHT,
                lambda u, c: u.new_gaze_target == GazeTarget.ROBOT_FACE,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.RIGHT_HANDOVER,
            ),
            (
                HandoverState.MOVING_TO_PERSON_RIGHT,
                GazeProgram.RIGHT_HANDOVER,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL,
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
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.ENSURING_LEFT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.RIGHT_TRAY,
                GazeProgram.ENSURING_LEFT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_LEFT,
                GazeProgram.ENSURING_LEFT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.RECEIVING_LEFT,
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
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.ENSURING_RIGHT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.MUTUAL,
                lambda u, c: u.new_gaze_target == GazeTarget.LEFT_TRAY,
                GazeProgram.ENSURING_RIGHT,
            ),
            (
                HandoverState.WAITING_FOR_RECEIVAL_RIGHT,
                GazeProgram.ENSURING_RIGHT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.RECEIVING_RIGHT,
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
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.PACKAGING,
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
                GazeProgram.MUTUAL_SHORT,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.PACKAGING,
            ),
            # HS_PACKAGING
            (
                HandoverState.PACKAGING,
                GazeProgram.PACKAGING,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.TRAYS,
            ),
            (
                HandoverState.PACKAGING,
                GazeProgram.TRAYS,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.MUTUAL,
            ),
            (
                HandoverState.PACKAGING,
                GazeProgram.MUTUAL,
                lambda u, c: u.gaze_program_finished == True,
                GazeProgram.IDLE,
            ),
        ]

        # static gaze simply maps handover states → gaze program
        self.static_gaze_map = {
            HandoverState.NO_ACTIVE_HANDOVER: GazeProgram.IDLE,
            HandoverState.MOVING_TO_PERSON: GazeProgram.MOVE_TO_PERSON,
            HandoverState.WAITING_FOR_RECEIVAL: GazeProgram.RECEIVING,
            HandoverState.MOVING_TO_PACKAGING: GazeProgram.MOVE_TO_PACKAGING,
            HandoverState.PACKAGING: GazeProgram.ENSURING,
        }

    def update_state(self, u: StateUpdate) -> UpdatedState:
        changes = UpdatedState()

        if any([u.handover_start_detected,u.handover_finished,u.object_in_bowl,u.new_arm_location]):
            for src, guard, dst, new_arm_prog, new_gaze_prog in self.handover_transitions:
                if self.state.current_handover_state == src and guard(u,self.state):
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
                self.state.current_gaze_program = self.static_gaze_map[changes.handover_state]
                changes.gaze_program = self.state.current_gaze_program
            if u.handover_start_detected and changes.handover_state == None:
                self.state.initiated_handover_waiting = u.handover_start_detected

        if self.dynamic_gaze and any([u.new_gaze_target,u.gaze_program_finished]) and is_time_difference_exceeded(self.state.last_gaze_update, GAZE_UPDATE_REFRESH_RATE_MS):
            for curr_hs, curr_gaze_prog, guard, gaze_dst in self.dynamic_gaze_transitions:
                if (
                    self.state.current_handover_state == curr_hs and 
                    self.state.current_gaze_program == curr_gaze_prog
                    and guard(u,self.state)
                ):
                    self.state.current_gaze_program = gaze_dst
                    changes.gaze_program = gaze_dst
                    break

            self.state.last_gaze_update = datetime.now()

        return changes
