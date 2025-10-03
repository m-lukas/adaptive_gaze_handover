# Adaptive Gaze Handover - Master Thesis

# How to Run

### Prepare System
- Laptop
- Connection to Robot
- franka_ros from source
- libfranka from source
- panda_moveit
- poetry
- globally install rospy

### Starting the System
1. Plug in robot, display and laptop
2. Switch on robot server
   1. If fans are not audible, make sure emergency button is not pressed
3. Turn on laptop, wait until Login appears
   1. Error on Robot Connection: Restart system and make sure "Advanced Options for Ubuntu" > ... is selected
4. Login on the laptop with the provided credentials
5. As soon as the laptop is started, open the Chromium Web Browser
6. Open the URL http://172.16.0.2/desk or select it from the bookmarks
   1. Ignore any warnings about the site being unsecure > proceed
7. Unlock joints and confirm in popup
   1. Clicking is normal
8. Change robot state to "Ready" (blue) by rotating black/white physical button
9. Top-Right: Burger Menu > Activate FCI (leave popup open)
10. Open the Terminal
11. `roslaunch panda_moveit_config franka_control.launch robot_ip:=172.16.0.2`
    1.  RViz deprecation warning can be closed
    2.  RViz can be closed or left open in Background
    3.  Wait a few seconds until no new logs appear
12. Open another tab in the same Terminal
13. `rosrun panda_control src/main.py` (Robot Control code)
    1.  Wait until program is started
14. Open `controller.html` in Browser or open URL `file:///home/panda/adaptive_gaze_handover/controller.html` on experiment laptop.
15. Navigate to Program Controls tab
16. Execute "Prepare Experiement" robot program by pressing the button
    1.  As soon as the robot is in the idle position, insert the bowl into the gripper
    2.  Press 2x ENTER in Robot Control terminal tab to confirm
17. Turn on Bluetooth Keyboard and connect it via the Laptop's Settings
18. Turn on the Robot Face display
19. Open a new Terminal window (right click on terminal icon > New Window)
20. Start Gaze Animation
    1.  `cd adaptive_gaze_handover/gaze_animation/`
    2.  `poetry shell`
    3.  Optional on very first execution: `poetry install`
    4.  Type but don't press ENTER: `python server.py`
    5.  Drag window to Robot Face display (usually to the right)
    6.  While the mouse cursor is on the other display, press ENTER. This will start the gaze animation on the Robot Face display in fullscreen. You can also see it by the dino icon in the application bar on the left.
21. Open a new Terminal window
22. Type `cd adaptive_gaze_handover`
23. Open a new Terminal tab
24. In Terminal tab 1, start Gaze Tracking
    1.  `cd gaze_tracking`
    2.  `poetry shell`
    3.  Optional on very first execution: `poetry install`
    4.  `python fixation_tracking.py`
    5.  Do not proceed with the gaze calibration yet
25. In Terminal tab 2, prepare State Machine
    1.  `cd state_machine`
    2.  `poetry shell`
    3.  Optional on very first execution: `poetry install`
    4.  For every participant, open files `demo.env` (for demonstration trials) and `prod.env` (for experimental trials) in `~/adaptive_gaze_handover/state_machine` and update the state machine configuration (participant id, dynamic (adaptive) gaze: true/false).
    5.  Back in Terminal: `source demo.env` (for demo) OR `source prod.env` for real experiement.

--- welcome the participant ---

26.  Run gaze calibration
     1.   Switch to Gaze Tracking Terminal tab
     2.   Run through gaze calibration procedure:
          1.   Show participant fixation point (e.g. top of robot face, furthest box in packaging area, ball with number 7 for left-handover, ball with number 29 for right-handover)
          2.   Press ENTER in Terminal
          3.   Repeat
          4.   When all targets are done, press ENTER to start the gaze tracking
27.  Switch to State Machine tab
28.  Start state machine: `uvicorn main:app --port 1111`
        1. By starting the state machine, the gaze animation won't run in a loop anymore but will wait for signals.
        2. Check in the logs if participant id and condition are correct!
        3. State Machine calibration can be also done via `file:///home/panda/adaptive_gaze_handover/controller.html`
        4. !!! By starting the state machine, the data recording starts !!!
29. Select Gaze Animation window by pressing the pygame (dino) icon
    1.  !!! The Gaze Animation records the key presses, without focusing the window, handover initiations are not possible. Do not click anywhere else during the experiment. !!!

--- when demonstration is done

30. Stop State Machine by pressing STRG+C in respective Terminal tab
31. In Robot Control terminal, stop panda_control by pressing STRG+C
32. Do not stop the gaze animation, the gaze tracking or panda_moveit.
33. Restart Robot Control using: `rosrun panda_control src/main.py`
34. Return demonstration balls and change packaging instructions.
35. In State Machine tab, run `source prod.env` to load the experiment config.
36. Restart the State Machine: `uvicorn main:app --port 1111`
    1.  Check configuration in logs
    2.  Select Gaze Animation window by pressing the pygame (dino) icon
        1.  !!! The Gaze Animation records the key presses, without focusing the window, handover initiations are not possible. Do not click anywhere else during the experiment. !!!

--- after the experiment ---

37. As soon as the Robot Control logs 


activate FCI
> leave popup open

move_it
> end of life warning
.. close popup
.. RViz can be closed

nach moveit and panda_control -> Panda Experiment Controler in Browser

Prepare Experiment
confirm Bowl grasp in Terminal
2x continue
