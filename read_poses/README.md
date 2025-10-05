# Read Poses Script

## Requirements

- Bash Terminal
- Make file executable: `chmod +x read_poses.sh`
- FCI activated
- Robot in `Ready` state
- Start `panda_moveit` controller

## How to Run

1. Open folder in Terminal
2. Run `./read_poses`
3. To end the script, write any letter to the Terminal and press ENTER

> Hint: The Python script is directly copied to clipboard
> Important: All 7 joints + 2 finger joints are recorded. However, panda_control ignores the finger joint values. For changing the speed in panda_control, you can add the speed value as float as an additional parameter to move_to_pose().