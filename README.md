# Adaptive Gaze Handover - Master Thesis

# How to Run


STRG + SHIFT + C/V

### Prepare System
- Laptop
- Connection to Robot
- franka_ros from source
- libfranka from source
- panda_moveit
- poetry
- globally install rospy

### Starting the System
1. Plug in robot, display and laptop.
2. Turn on robot server (below the table) using the switch on the side. You should hear a click and noise from the fans. If the fans are not audible, make sure emergency button is not locked.
3. Turn on laptop and wait until Login appears.
   1. If there is an error on Robot Connection later: Restart the entire system and make sure "Advanced Options for Ubuntu" > ... is selected.
4. Login on the laptop with the provided credentials.
5. As soon as the laptop is started, open the Chromium Web Browser.
6. Open the URL http://172.16.0.2/desk or select it from the bookmarks.
   1. Ignore any warnings about the site being unsecure, just proceed (or use the advanced options).
7. Unlock the joints of the robot by clicking on the icon in the sidebar and confirm it in the popup.
   1. Clicking sounds are normal and indicate the breaks being opened.
8. Change the robot state to "Ready" (blue) by rotating the physical, black/white button.
9. Back in the Desk-Interface, in the top-right corner, click on the burger menu icon and subsequently select "Activate FCI". A popup will appear indicating that FCI is active - leave this popup open for the entire time.
10. Open a new Terminal window on the laptop.
11. Paste and press ENTER: `roslaunch panda_moveit_config franka_control.launch robot_ip:=172.16.0.2`
    1.  You should see many logs in the Terminal.
    2.  RViz (visualization software) will open.
    3.  The ROS deprecation warning can be closed.
    4.  RViz can be closed or left open in background.
    5.  Wait a few seconds until no new logs appear.
12. Open another tab in the same Terminal window.
13. Paste and press ENTER: `rosrun panda_control src/main.py`
    1.  This will start the Robot Control application. Wait until the program is started.
14. Open `controller.html` (Panda Experiment Controller) in the Chromium Web Browser or open the URL `file:///home/panda/adaptive_gaze_handover/controller.html` on the experiment laptop.
15. Navigate to the "Program Controls" tab.
16. Execute "Prepare Experiement" robot program by pressing the button.
    1.  As soon as the robot is in the idle position, insert the bowl into the gripper.
    2.  Press 2x ENTER in Robot Control terminal tab to confirm.
17. Turn on Bluetooth Keyboard and connect it via the Laptop's Settings.
18. Turn on the Robot Face display.
19. Open a new Terminal window (right click on Terminal icon > New Window).
20. Start Gaze Animation
    1.  Paste and ENTER: `cd adaptive_gaze_handover/gaze_animation/`
    2.  Paste and ENTER: `poetry shell`
    3.  Optional on very first execution: Run `poetry install`
    4.  Type but don't press ENTER: `python server.py`
    5.  Drag Terminal window to Robot Face display (usually to the right off-screen).
    6.  While the mouse cursor is on the other display, press ENTER. This will start the gaze animation on the Robot Face display in fullscreen. You can also see it by the dino icon in the application bar on the left.
21. Open a new Terminal window (right click on Terminal icon > New Window).
22. Type and ENTER `cd adaptive_gaze_handover`
23. Open a new Terminal tab in the newly opened window.
24. In Terminal tab 1, start Gaze Tracking:
    1.  Paste and ENTER: `cd gaze_tracking`
    2.  Paste and ENTER: `poetry shell`
    3.  Optional on very first execution: Run `poetry install`
    4.  Paste and ENTER: `python fixation_tracking.py`
    5.  Do not proceed with the gaze calibration yet.
25. In Terminal tab 2, prepare State Machine
    1.  Paste and ENTER: `cd state_machine`
    2.  Paste and ENTER: `poetry shell`
    3.  Optional on very first execution: `poetry install`
    4.  For every participant, open the files `demo.env` (for demonstration trials) and `prod.env` (for experimental trials) in `~/adaptive_gaze_handover/state_machine` and update the state machine configuration (participant id, dynamic (adaptive) gaze: true/false). Alternatively, this can be also done after starting the State Machine using the Panda Experiment Controller 
    5.  Back in Terminal: Paste and ENTER `source demo.env` (for demo) OR `source prod.env` for real experiement.

Now welcome the participant to the lab.
After they finish the consent, proceed:

26.  Run gaze calibration:
     1.   Let participant sit down at the workspace.
     2.   Switch to Gaze Tracking Terminal tab.
     3.   Run through gaze calibration procedure:
          1.   Show participant fixation point (e.g. top of robot face, furthest box in packaging area, ball with number 7 for left-handover, ball with number 29 for right-handover)
          2.   Press ENTER in Terminal.
          3.   Repeat
          4.   When all targets are done, press ENTER to start the gaze tracking.
27.  Switch to State Machine tab.
28.  Start state machine: Paste and ENTER `uvicorn main:app --port 1111`
        1. By starting the state machine, the gaze animation won't run in a loop anymore but will wait for signals.
        2. Check in the logs if participant id and condition are correct!
        3. State Machine calibration can be also done via the Panda Experiment Controller: `file:///home/panda/adaptive_gaze_handover/controller.html`
        4. !!! By starting the state machine, the data recording starts !!!
29. Select Gaze Animation window by pressing the pygame (dino) icon.
    1.  !!! The Gaze Animation records the key presses, without focusing the window, handover initiations are not possible. Do not click anywhere else during the experiment. !!!

When the demonstration is done:

30. Stop State Machine by pressing STRG+C in the respective Terminal tab.
31. In Robot Control terminal, stop panda_control by pressing STRG+C.
32. Do not stop the gaze animation, the gaze tracking or panda_moveit.
33. Restart Robot Control using: `rosrun panda_control src/main.py`. Restarting panda_control is required to reset the ball counter.
34. Return demonstration balls and change packaging instructions.
35. In State Machine tab, run `source prod.env` to load the experiment config.
36. Restart the State Machine using: `uvicorn main:app --port 1111`
    1.  Check configuration in logs
    2.  Select Gaze Animation window by pressing the pygame (dino) icon
        1.  !!! The Gaze Animation records the key presses, without focusing the window, handover initiations are not possible. Do not click anywhere else during the experiment. !!!

After the experiment:

37.  As soon as the Robot Control logs show that the robot returns to the idle pose and the handover is finished, stop the State Machine by pressing STRG+C in the respective Terminal tab.
    1.  You should see now in the State Machine logs that the Data Logger logged handover and gaze data.
38. While the participant is completing the subjective measures, find the logged data in `~/adaptive_gaze_handover/state_machine/output` and make sure that the data is complete.
39. Stop the Gaze Tracking by pressing STRG+C in the respective Terminal tab.

Restarting for a new participant:

39. Navigate to Panda Experiment Controller in the Browser and run "Move to Idle" in the "Program Controls" tab.
40. After the robot finishes moving, go to the Robot Control terminal and stop panda_control by pressing STRG+C. Do not stop panda_moveit.
41. Restart Robot Control using: `rosrun panda_control src/main.py` .
42. Continue with the tutorial from step 24.

Shutting of the system:

42. Navigate to Panda Experiment Controller in the Browser and run the program "End Experiment" in the "Program Controls" tab.
    1.  In the panda_control Terminal tab, press ENTER to confirm the release of the bowl.
    2.  Remove the bowl from the robot arm.
    3.  Press ENTER in the Terminal to continue.
43. Stop the State Machine by pressing STRG+C in the respective Terminal tab.
44. Stop the Gaze Tracking by pressing STRG+C in the respective Terminal tab.
45. Stop the Gaze Animation by clicking on the dino item to focus the window and subsequently pressing ESC.
46. After the robot finished the program and is in the standby pose, stop panda_control by pressing STRG+C in the Terminal tab.
47. Stop panda_moveit by pressing STRG+C in the Terminal tab.
48. After all robot applications are stopped, go to the Desk-Interface and deactivate FCI.
49. Stop the robot by pressing the physical, black/white button.
    1.  The light on the robot should change to white.
50. In the Desk-Interface, lock the breaks by clicking on the icon on the right.
    1.  There should be one click accompanied by the stopping of the robot arm cooling.
51. Via the burger menu in the top-right corner, shut down the robot.
    1.  Shutting off the robot takes several minutes.
52. Make sure to turn off the display and the keyboard in the meantime.
53. As soon as the Desk-Interface confirms the shutdown, you can shut down the laptop too.
54. Please wait a few more minutes until cutting the power of the robot server using the switch on the side. There will be still some sounds from the server but as long as the front fans are stopped, it is fine.
    1.  DO NOT TURN ON THE ROBOT AGAIN WITHIN 5 MINUTES.
55. Plug-Off the robot server.
