import os
import sys
from typing import List

import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import math

import cv2
from pygaze import PyGaze, PyGazeRenderer

pg = PyGaze(model_path="models/eth-xgaze_resnet18.pth")
pgren = PyGazeRenderer()
v = cv2.VideoCapture(0)


gaze_calibration_vectors = {
    "robot_face": [],
    "pose1": [],
    "pose2": [],
    "own_items": [],
}

mean_fixation_vectors = {
    "robot_face": None,
    "pose1": None,
    "pose2": None,
    "own_items": None,
}


def calibration_loop(target: str, num_frames: int = 100):
    counter = 0
    while counter < num_frames:
        ret, frame = v.read()
        if ret:
            gaze_result = pg.predict(frame)
            if len(gaze_result) == 1:
                gaze_calibration_vectors[target].append(gaze_result[0].gaze_vector)

        counter += 1


def find_closest_fixation(current_gaze_vector: np.ndarray) -> str:
    distances = [
        np.linalg.norm(current_gaze_vector - vec)
        for vec in mean_fixation_vectors.values()
    ]
    
    print({
        "robot_face": distances[0],
        "pose1": distances[1],
        "pose2": distances[2],
        "own_items": distances[3],
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


input("Press ENTER to capture Robot Face ...")
calibration_loop("robot_face")

input("Press ENTER to capture Pose1 ...")
calibration_loop("pose1")

input("Press ENTER to capture Pose2 ...")
calibration_loop("pose2")

input("Press ENTER to capture Own Items ...")
calibration_loop("own_items")

print("DONE ...")


calculate_mean_fixation_vectors()


print("[Robot Face] Mean Fixation Vector:", str(mean_fixation_vectors["robot_face"]))
print("[Pose1] Mean Fixation Vector:", str(mean_fixation_vectors["pose1"]))
print("[Pose2] Mean Fixation Vector:", str(mean_fixation_vectors["pose2"]))
print("[Own Items] Mean Fixation Vector:", str(mean_fixation_vectors["own_items"]))

print("\n\n")
input("Press ENTER to start recording ...")

while True:
    ret, frame = v.read()
    if ret:
        gaze_result = pg.predict(frame)
        for face in gaze_result:
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
            if fixation == "robot_face":
                text = "Robot Face"
            elif fixation == "pose1":
                text = "Pose 1"
            elif fixation == "pose2":
                text = "Pose 2"
            elif fixation == "own_items":
                text = "Own items"

            cv2.putText(
                frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2
            )

        cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

v.release()
cv2.destroyAllWindows()
