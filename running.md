Panda must be in Ready state
Move back to "normal" position - else roslaunch might fail
Activate FCI

roslaunch franka_control franka_control.launch robot_ip:=172.16.0.2

roslaunch franka_gripper franka_gripper.launch robot_ip:=172.16.0.2

(Often fails on first execution - just retry)
roslaunch panda_moveit_config franka_control.launch robot_ip:=172.16.0.2

rosrun panda_control src/main.py






----

For new script:

chmod +x <filename>

Not necessary: catkin build panda_control
