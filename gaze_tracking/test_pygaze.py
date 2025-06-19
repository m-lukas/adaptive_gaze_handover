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

while v.isOpened():
    ret, frame = v.read()
    if ret:
        gaze_result = pg.predict(frame)
        if gaze_result:
            face = gaze_result[0]
            color = (0, 255, 0)
            # if pg.look_at_camera(face):
            #     color = (255, 0, 0)
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

            pitch, yaw, roll = face.get_head_angles()
            g_pitch, g_yaw = face.get_gaze_angles()
            print(f"Face angles: pitch={pitch}, yaw={yaw}, roll={roll}.")
            print(f"Distance to camera: {face.distance}")
            print(f"Gaze angles: pitch={g_pitch}, yaw={g_yaw}")
            print(f"Gaze vector: {face.gaze_vector}")
            print(f"Looking at camera: {pg.look_at_camera(face)}")

            text = f"Face: p={pitch},y={yaw},r={roll}, G-Angs: p={pitch},y={yaw}, Vec: {face.gaze_vector}, {pg.look_at_camera}"

            cv2.putText(
                frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 0.8, (147, 58, 31), 2
            )

        cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

v.release()
out.release()
cv2.destroyAllWindows()
