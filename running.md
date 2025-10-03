Panda must be in Ready state
Move back to "normal" position - else roslaunch might fail
Activate FCI

roslaunch panda_moveit_config franka_control.launch robot_ip:=172.16.0.2

rosrun panda_control src/main.py






----

For new script:

chmod +x <filename>

Not necessary: catkin build panda_control
