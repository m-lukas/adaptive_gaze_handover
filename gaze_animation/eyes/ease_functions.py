import math
from enum import Enum


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_out_quint(t):
    return 1 - (1 - t) ** 5


def smoothstep(t):
    return t * t * (3 - 2 * t)


def hybrid_ease(t):
    return (1 - math.exp(-5 * t)) / (1 - math.exp(-5))


def ease_out_sine(t):
    return math.sin(t * math.pi / 2)


class EaseFunction(Enum):
    CUBIC = ease_out_cubic
    QUINT = ease_out_quint
    SMOOTHSTEP = smoothstep
    HYBRID = hybrid_ease
    SINE = ease_out_sine
