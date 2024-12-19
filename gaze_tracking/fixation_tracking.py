import sys
import os

import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from pygaze import PyGaze, PyGazeRenderer
import cv2
import math


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


def calibration_loop(target: str):
	counter = 0
	while counter < 100:
		ret, frame = v.read()
		if ret:
			gaze_result = pg.predict(frame)
			if len(gaze_result) == 1:
				gaze_calibration_vectors[target].append(gaze_result[0].gaze_vector)

		counter += 1


def find_closest_fixation(current_gaze_vector: np.ndarray) -> str:
	distances = [np.linalg.norm(current_gaze_vector - vec) for vec in mean_fixation_vectors.values()]

	most_similar_index = np.argmin(distances)
	return list(mean_fixation_vectors.keys())[most_similar_index]


input("Press ENTER to capture Robot Face ...")
calibration_loop("robot_face")

input("Press ENTER to capture Pose1 ...")
calibration_loop("pose1")

input("Press ENTER to capture Pose2 ...")
calibration_loop("pose2")

input("Press ENTER to capture Own Items ...")
calibration_loop("own_items")

print("DONE ...")

mean_fixation_vectors["robot_face"] = np.mean(gaze_calibration_vectors["robot_face"], axis=0)
mean_fixation_vectors["pose1"] = np.mean(gaze_calibration_vectors["pose1"], axis=0)
mean_fixation_vectors["pose2"] = np.mean(gaze_calibration_vectors["pose2"], axis=0)
mean_fixation_vectors["own_items"] = np.mean(gaze_calibration_vectors["own_items"], axis=0)

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
				color = color
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

			cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)

		cv2.imshow('frame', frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

v.release()
cv2.destroyAllWindows()