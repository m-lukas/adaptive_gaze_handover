#!/usr/bin/env python3

import rospy
import moveit_commander
import geometry_msgs.msg
from math import pi
import sys
import actionlib
from franka_gripper.msg import HomingAction, HomingGoal, MoveAction, MoveGoal
from controls import home_gripper, grasp, move_to_home, move_to_pose
from programs import prepare_experiment, end_experiment

def control():
    # Initialize moveit_commander and rospy node
    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node('panda_move_arm_node', anonymous=True)

    home_gripper_client = actionlib.SimpleActionClient('/franka_gripper/homing', HomingAction)
    home_gripper_client.wait_for_server()

    grasp_client = actionlib.SimpleActionClient('/franka_gripper/move', MoveAction)
    grasp_client.wait_for_server()

    # Instantiate a RobotCommander object (interface to the robot)
    robot = moveit_commander.RobotCommander()

    # Instantiate a PlanningSceneInterface object (interface to the world)
    scene = moveit_commander.PlanningSceneInterface()

    # Instantiate MoveGroupCommander for the arm
    group_name = "panda_arm"
    move_group = moveit_commander.MoveGroupCommander(group_name)

    # Print robot info
    rospy.loginfo("Planning frame: %s" % move_group.get_planning_frame())
    rospy.loginfo("End effector link: %s" % move_group.get_end_effector_link())
    rospy.loginfo("Available Planning Groups: %s" % robot.get_group_names())

    # ---- !!! Movement Code Here !!! ----

    rospy.loginfo("Motion completed.")

    # Shutdown
    moveit_commander.roscpp_shutdown()

if __name__ == '__main__':
    try:
        control()
    except rospy.ROSInterruptException:
        pass
