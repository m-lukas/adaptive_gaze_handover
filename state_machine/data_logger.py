import csv
from datetime import datetime
from typing import List


OUTPUT_DIRECTORY = "output"


class HandoverTimings:
   def __init__(self):
      self.initiation_timestamp: datetime | None = None
      self.object_in_bowl_timestamp: datetime | None = None
      self.error_occured: bool | None = None


class GazeTargetTiming:
   def __init__(self, gaze_target: str):
      self.gaze_target: str = gaze_target
      self.start_timestamp: datetime = datetime.now()


class DataLogger:
    def __init__(self, demonstration: bool, file_name: str):
        self.file_name = (file_name if not demonstration else f"{file_name}_demo")

        self.gaze_target_timings: List[GazeTargetTiming] = []

        self.handover_timings: List[HandoverTimings] = []

        self.handover_finished_timestamp: datetime | None = None

    def log_gaze_target(self, gaze_target: str) -> None:
        self.gaze_target_timings.append(GazeTargetTiming(gaze_target))

    def log_handover_initiation(self) -> None:
        self.handover_timings.append(HandoverTimings())
        self.handover_timings[len(self.handover_timings)-1].initiation_timestamp = datetime.now()

    def log_object_in_bowl(self) -> None:
        self.handover_timings[len(self.handover_timings)-1].object_in_bowl_timestamp = datetime.now()

    def log_handover_error(self) -> None:
        self.handover_timings[len(self.handover_timings)-1].error_occured = True

    def log_handover_finished(self) -> None:
        self.handover_finished_timestamp = datetime.now()

    def __get_handover_data(self) -> List[tuple]:
        data = [["identifier", "initiation", "object_in_bowl", "init_to_bowl_duration", "error", "bowl_to_bowl_duration", "full_duration"]]
        for index, handover in enumerate(self.handover_timings):
            name = f"handover_{index+1}"

            init_to_bowl_duration = None
            if handover.object_in_bowl_timestamp:
                init_to_bowl_duration = (handover.object_in_bowl_timestamp-handover.initiation_timestamp).total_seconds() * 1000

            bowl_to_bowl_duration = None
            if index > 0 and handover.object_in_bowl_timestamp:
                previous_object_in_bowl_timestamp = self.handover_timings[index-1].object_in_bowl_timestamp
                if previous_object_in_bowl_timestamp:
                    bowl_to_bowl_duration = (handover.object_in_bowl_timestamp-previous_object_in_bowl_timestamp).total_seconds() * 1000

            next_initiation_timestamp = self.handover_finished_timestamp
            if index < len(self.handover_timings)-1:
                next_initiation_timestamp = self.handover_timings[index+1].initiation_timestamp

            full_duration = (next_initiation_timestamp-handover.initiation_timestamp).total_seconds() * 1000
            
            data.append(
                [
                    name,
                    handover.initiation_timestamp.isoformat(),
                    (handover.object_in_bowl_timestamp.isoformat() if handover.object_in_bowl_timestamp else None),
                    init_to_bowl_duration,
                    handover.error_occured,
                    bowl_to_bowl_duration,
                    full_duration
                ]
            )

        return data

    def __get_gaze_data(self) -> List[tuple]:
        data = [["target", "start_time", "duration"]]
        for index, gaze_target in enumerate(self.gaze_target_timings):
            duration = None
            if index < len(self.gaze_target_timings)-1:
                next_start_time = self.gaze_target_timings[index+1].start_timestamp
                duration = (next_start_time-gaze_target.start_timestamp).total_seconds() * 1000

            data.append(
                [
                    gaze_target.gaze_target,
                    gaze_target.start_timestamp,
                    duration
                ]
            )

        return data

    # def __get_analysis_data(self) -> List[tuple]:
    #     pass

    def __write_file(self, data: List[tuple], file_name_suffix: str | None = None) -> None:
        file_name = f"{self.file_name}_{file_name_suffix}" if file_name_suffix else self.file_name
        with open(f"{OUTPUT_DIRECTORY}/{file_name}.csv", "w") as csv_file:  
            writer = csv.writer(csv_file, delimiter=',')
            for line in data:
                writer.writerow(line)

    def write_files(self) -> None:
        print("DataLogger: Logging Data")
        if self.handover_timings:
            self.__write_file(self.__get_handover_data(), "handover")
            print("DataLogger: Logged Handover Data")
        if self.gaze_target_timings:
            self.__write_file(self.__get_gaze_data(), "gaze")
            print("DataLogger: Logged Gaze Data")
        #self.__write_file(self.__get_analysis_data(), "analysis")
        
