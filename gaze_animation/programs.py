from typing import List

from ease_functions import EaseFunction


class Target:
    def __init__(self, x: float, y: float):
      self.x = x
      self.y = y


class Transition:
    def __init__(
        self,
        x: float,
        y: float,
        duration: float,
        ease_function: EaseFunction = EaseFunction.HYBRID,
    ):
        self.x = x
        self.y = y
        self.duration = duration
        self.ease_function = ease_function


class TargetTransition(Transition):
    def __init__(
        self,
        target: Target,
        duration: float,
        ease_function: EaseFunction = EaseFunction.HYBRID,
    ) -> None:
        super().__init__(target.x, target.y, duration, ease_function)


class Delay:
    def __init__(self, duration: float):
        self.duration = duration


class GazeProgram:
    def __init__(self, saccades: List[Transition | Delay], start_pos: tuple = [0,0]):
        self.saccades = saccades
        self.start_pos = start_pos
        self.index = 0


packaging_common = Target(1, 0.7)
packaging_container = Target(1, 0.5)
left_handover = Target(-0.5, 1)
right_handover = Target(0.2, 1)
mutual = Target(0, 0.2)
center_handover = Target(0, 1)


programs = {
    "idle": GazeProgram(
        saccades=[
            Transition(-1, -1, 2.5),
            Delay(1.5),
            Transition(-1, 0, 2),
            Delay(1),
            Transition(0.2, -0.8, 2.5),
            Delay(2),
            Transition(0.4, 0.2, 2),
            Delay(1),
            Transition(0.7, -0.5, 1.5),
            Delay(3),
            Transition(0, 1, 2.5),
            Delay(1),
        ],
    ),
    "move_to_person_left": GazeProgram(
        saccades=[
            TargetTransition(packaging_common, 0.8),
            TargetTransition(left_handover, 2.5, EaseFunction.SMOOTHSTEP),
        ],
    ),
    "move_to_person_right": GazeProgram(
        saccades=[
            TargetTransition(packaging_common, 0.8),
            TargetTransition(right_handover, 1.5, EaseFunction.SMOOTHSTEP),
        ],
    ),
    "receiving_left": GazeProgram(
        saccades=[
            TargetTransition(left_handover, 0.5),
            Delay(1),
            TargetTransition(mutual, 1),
            Delay(0.5),
            TargetTransition(left_handover, 1),
            Delay(1.5),
            TargetTransition(mutual, 1),
            Delay(0.5),
            TargetTransition(left_handover, 1),
            Delay(1),
        ],
    ),
    "receiving_right": GazeProgram(
        saccades=[
            TargetTransition(right_handover, 0.5),
            Delay(1),
            TargetTransition(mutual, 1),
            Delay(0.5),
            TargetTransition(right_handover, 1),
            Delay(1.5),
            TargetTransition(mutual, 1),
            Delay(0.5),
            TargetTransition(right_handover, 1),
            Delay(1),
        ],
    ),
    "move_to_packaging_left": GazeProgram(
        saccades=[
            TargetTransition(left_handover, 0),
            TargetTransition(packaging_common, 3, EaseFunction.SMOOTHSTEP),
        ],
    ),
    "move_to_packaging_right": GazeProgram(
        saccades=[
            TargetTransition(right_handover, 0),
            TargetTransition(packaging_common, 2, EaseFunction.SMOOTHSTEP),
        ],
    ),
    "unsure": GazeProgram(
        saccades=[
            TargetTransition(mutual, 0.2),
            Delay(0.5),
            TargetTransition(center_handover, 0.5),
            Delay(0.5),
            TargetTransition(mutual, 0.5),
        ],
    ),
    "waiting": GazeProgram(
        saccades=[
            TargetTransition(mutual, 2),
            Delay(2)
        ],
    ),
    "mutual": GazeProgram(
        saccades=[
            TargetTransition(mutual, 0.5),
            Delay(0.8)
        ],
    ),
    "gaze_left_handover": GazeProgram(
        saccades=[
            TargetTransition(left_handover, 0.5),
            Delay(0.5)
        ],
    ),
    "gaze_right_handover": GazeProgram(
        saccades=[
            TargetTransition(right_handover, 0.5),
            Delay(0.5)
        ],
    ),
    "ensuring_left": GazeProgram(
        saccades=[
            TargetTransition(mutual, 0.2),
            Delay(0.4),
            TargetTransition(left_handover, 0.5),
            Delay(0.4),
            TargetTransition(packaging_common, 0.8),
            Delay(0.4),
            TargetTransition(mutual, 0.5),
        ],
    ),
    "ensuring_right": GazeProgram(
        saccades=[
            TargetTransition(mutual, 0.2),
            Delay(0.4),
            TargetTransition(right_handover, 0.5),
            Delay(0.4),
            TargetTransition(packaging_common, 0.8),
            Delay(0.4),
            TargetTransition(mutual, 0.5),
        ],
    ),
    "mutual_short": GazeProgram(
        saccades=[
            TargetTransition(mutual, 0.5),
            Delay(0.5),
        ],
    ),
    "trays": GazeProgram(
        saccades=[
            TargetTransition(center_handover, 0.5),
            Delay(0.3),
        ],
    ),
    "packaging": GazeProgram(
        saccades=[
            TargetTransition(packaging_common, 0.5),
            Delay(0.2),
            TargetTransition(packaging_container, 1),
            Delay(1.5),
            TargetTransition(packaging_common, 0.5),
        ],
    ),
}
