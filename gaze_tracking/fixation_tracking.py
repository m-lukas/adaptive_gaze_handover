import os
import sys
import time
from typing import List

import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import math
import requests

import cv2
from pygaze import PyGaze, PyGazeRenderer


FIXATION_TIME_THRESHOLD = 0.5


pg = PyGaze(model_path="models/eth-xgaze_resnet18.pth")
pgren = PyGazeRenderer()
v = cv2.VideoCapture(0)


gaze_calibration_vectors = {
    "robot_face": [],
    "packaging_area": [],
    "left_handover_location": [],
    "right_handover_location": [],
}

mean_fixation_vectors = {
    "robot_face": None,
    "packaging_area": None,
    "left_handover_location": None,
    "right_handover_location": None,
}


class GazeDetectionFilter:
    def __init__(self):
        self.current_fixation = None
        self.fixation_start_time = None
        self.last_triggered_fixation = None

    def update_gaze(self, fixation: str):
        now = time.time()

        if fixation != self.current_fixation:
            self.current_fixation = fixation
            self.fixation_start_time = now
            return None

        duration = now - self.fixation_start_time
        if duration >= FIXATION_TIME_THRESHOLD and fixation != self.last_triggered_fixation:
            self.last_triggered_fixation = fixation
            return fixation

        return None


def calibration_loop(target: str, num_frames: int = 100):
    counter = 0
    while counter < num_frames:
        ret, frame = v.read()
        if ret:
            gaze_result = pg.predict(frame)
            if len(gaze_result) == 1:
                gaze_calibration_vectors[target].append(
                    [gaze_result[0].gaze_vector[0], gaze_result[0].gaze_vector[1]]
                )

        counter += 1


def find_closest_fixation(current_gaze_vector: np.ndarray) -> str:
    reduced_vector = [current_gaze_vector[0], current_gaze_vector[1]]
    distances = [
        np.linalg.norm(reduced_vector - vec)
        for vec in mean_fixation_vectors.values()
    ]
    
    print({
        "robot_face": distances[0],
        "packaging_area": distances[1],
        "left_handover_location": distances[2],
        "right_handover_location": distances[3],
    })

    most_similar_index = np.argmin(distances)
    return list(mean_fixation_vectors.keys())[most_similar_index]


def remove_outliers(vector_list: List[np.ndarray], sd_threshold=3) -> List[np.ndarray]:
    vector_list_array = np.stack(vector_list)  # Shape: (n_samples, n_features)
    mean = np.mean(vector_list_array, axis=0)
    std_dev = np.std(vector_list_array, axis=0)
    distances = np.linalg.norm(vector_list_array - mean, axis=1)
    mask = distances < sd_threshold * np.linalg.norm(std_dev)
    filtered_vectors = vector_list_array[mask]
    return [np.array(vec) for vec in filtered_vectors]


def calculate_mean_fixation_vectors() -> None:
    for target in mean_fixation_vectors.keys():
        print("Before", len(gaze_calibration_vectors[target]))
        gaze_calibration_vectors[target] = remove_outliers(gaze_calibration_vectors[target])
        print("After", len(gaze_calibration_vectors[target]))
        mean_fixation_vectors[target] = np.mean(gaze_calibration_vectors[target], axis=0)


def send_gaze_target(fixation: str):
    url = "http://127.0.0.1:5000/move"
    payload = {"fixation": fixation}
    headers = {
    'Content-Type': 'application/json'
    }

    requests.request("POST", url, headers=headers, json=payload)
    print("Triggered gaze change.")


input("Press ENTER to capture Robot Face ...")
calibration_loop("robot_face")

input("Press ENTER to capture Packaging Area ...")
calibration_loop("packaging_area")

input("Press ENTER to capture Left Handover Location ...")
calibration_loop("left_handover_location")

input("Press ENTER to capture Right Handover Location ...")
calibration_loop( "right_handover_location")

print("DONE ...")


calculate_mean_fixation_vectors()


print("[Robot Face] Mean Fixation Vector:", str(mean_fixation_vectors["robot_face"]))
print("[Packaging Area] Mean Fixation Vector:", str(mean_fixation_vectors["packaging_area"]))
print("[Left Handover Location] Mean Fixation Vector:", str(mean_fixation_vectors["left_handover_location"]))
print("[Right Handover Location] Mean Fixation Vector:", str(mean_fixation_vectors["right_handover_location"]))

print("\n\n")
input("Press ENTER to start recording ...")

filter = GazeDetectionFilter()
while v.isOpened():
    ret, frame = v.read()
    if ret:
        gaze_result = pg.predict(frame)
        if gaze_result:
            face = gaze_result[0]
            color = (0, 255, 0)
            if pg.look_at_camera(face):
                color = (255, 0, 0)
            pgren.render(
                frame,
                face,
                draw_face_bbox=True,
                draw_face_landmarks=False,
                draw_3dface_model=False,
                draw_head_pose=False,
                draw_gaze_vector=True,
                color=color,
            )

            fixation = find_closest_fixation(face.gaze_vector)

            cv2.putText(
                frame, fixation, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2
            )

            stable_fixation = filter.update_gaze(fixation)
            if stable_fixation:
                send_gaze_target(fixation)

        cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

v.release()
cv2.destroyAllWindows()
