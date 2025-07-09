from datetime import datetime


def is_time_difference_exceeded(provided_time: datetime, threshold_ms: int) -> bool:
    now = datetime.now()
    difference = abs((now - provided_time).total_seconds() * 1000)
    return difference > threshold_ms
