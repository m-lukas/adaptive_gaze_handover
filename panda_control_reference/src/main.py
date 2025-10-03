#!/usr/bin/env python3

import sys
import threading

import rospy
import moveit_commander
import actionlib
from flask import Flask, request, jsonify, Response, make_response
from franka_gripper.msg import HomingAction, MoveAction

from programs import PROGRAMS

def control():
    # MoveIt + ROS initialization
    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node('panda_move_arm_node', anonymous=True)

    home_gripper_client = actionlib.SimpleActionClient('/franka_gripper/homing', HomingAction)
    home_gripper_client.wait_for_server()
    grasp_client = actionlib.SimpleActionClient('/franka_gripper/move', MoveAction)
    grasp_client.wait_for_server()

    robot = moveit_commander.RobotCommander()
    scene = moveit_commander.PlanningSceneInterface()
    move_group = moveit_commander.MoveGroupCommander("panda_arm")

    rospy.loginfo("Planning frame: %s" % move_group.get_planning_frame())
    rospy.loginfo("End effector link: %s" % move_group.get_end_effector_link())
    rospy.loginfo("Available Planning Groups: %s" % robot.get_group_names())

    # Setup webserver
    app = Flask(__name__)
    program_lock = threading.Lock()  # ensures only one program runs at a time

    def _run_program(name):
        try:
            rospy.loginfo(f"Starting program '{name}'")
            PROGRAMS[name](move_group, home_gripper_client, grasp_client)
            rospy.loginfo(f"Program '{name}' completed")
        except Exception as e:
            rospy.logerr(f"Error in program '{name}': {e}")
        finally:
            program_lock.release()

    def _build_cors_preflight_response():
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

    def _corsify_actual_response(response, status_code=200):
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, status_code
    
    @app.route("/", methods=["GET", "OPTIONS"])
    def status():
        if request.method == "OPTIONS":
            return _build_cors_preflight_response()

        return _corsify_actual_response(jsonify({"status": "ok"}))

    @app.route('/start', methods=["POST", "OPTIONS"])
    def start_program():
        if request.method == "OPTIONS": # CORS preflight
            return _build_cors_preflight_response()
        elif request.method == "POST":
            data = request.get_json()
            try:
                program_name = data["program"]
            except (TypeError, ValueError, Exception):
                return _corsify_actual_response(jsonify({"error": "Invalid input"}), 400)

            rospy.loginfo(f"Program '{program_name}' requested")
            if program_name not in PROGRAMS:
                rospy.loginfo(f"Program '{program_name}' does not exist")
                return _corsify_actual_response(jsonify({'error': 'Unknown program'}), 400)

            # # try to grab lock, if already held => someone else is running
            if not program_lock.acquire(blocking=False):
                return _corsify_actual_response(jsonify({'error': 'Another program is already running'}), 409)

            # launch the program in its own thread so we return immediately
            t = threading.Thread(
                target=_run_program,
                args=(program_name,),
                daemon=True
            )
            t.start()
            return _corsify_actual_response(jsonify({'status': 'Program started'}), 200)

    # Flask in background thread
    server = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=3333),
        daemon=True
    )
    server.start()

    # keep ROS alive
    rospy.spin()

    # clean up
    moveit_commander.roscpp_shutdown()

if __name__ == '__main__':
    try:
        control()
    except rospy.ROSInterruptException:
        pass
