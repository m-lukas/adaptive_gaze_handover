from typing import List

from ease_functions import EaseFunction


class Transition:
    def __init__(self, x: float, y: float, duration: float, ease_function: EaseFunction = EaseFunction.HYBRID):
      self.x = x
      self.y = y
      self.duration = duration
      self.ease_function = ease_function


class Delay:
    def __init__(self, duration: float):
      self.duration = duration


class GazeProgram:
    def __init__(self, saccades: List[Transition | Delay], start_pos: tuple):
      self.saccades = saccades
      self.start_pos = start_pos
      self.index = 0
