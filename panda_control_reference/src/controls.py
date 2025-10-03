from franka_gripper.msg import HomingGoal, MoveGoal


DEFAULT_ARM_SPEED = 0.1
MAX_ARM_SPEED = 0.8


def move_to_home(move_group) -> None:
    move_group.clear_pose_targets()
    move_group.set_named_target("ready")
    plan = move_group.go(wait=True)
    move_group.stop()
    move_group.clear_pose_targets()


def home_gripper(home_gripper_client) -> None:
    home_goal = HomingGoal()
    home_gripper_client.send_goal(home_goal)
    home_gripper_client.wait_for_result()


def move_to_pose(move_group, joint1, joint2, joint3, joint4, joint5, joint6, joint7, finger_1=None, finger_2=None, speed=DEFAULT_ARM_SPEED) -> None:
    move_group.clear_pose_targets()

    if speed > MAX_ARM_SPEED:
        return

    joint_goal = move_group.get_current_joint_values()
    joint_goal[0] = joint1
    joint_goal[1] = joint2
    joint_goal[2] = joint3
    joint_goal[3] = joint4
    joint_goal[4] = joint5
    joint_goal[5] = joint6
    joint_goal[6] = joint7

    move_group.set_max_velocity_scaling_factor(speed)
    move_group.set_max_acceleration_scaling_factor(speed)

    move_group.go(joint_goal, wait=True)
    move_group.stop()
    move_group.clear_pose_targets()

    move_group.set_max_velocity_scaling_factor(DEFAULT_ARM_SPEED)
    move_group.set_max_acceleration_scaling_factor(DEFAULT_ARM_SPEED)


def grasp(grasp_client, width_in_meters: float, speed: float = 0.05) -> None:
    grasp_goal = MoveGoal(width=width_in_meters, speed=speed)
    grasp_client.send_goal(grasp_goal)
    grasp_client.wait_for_result()
