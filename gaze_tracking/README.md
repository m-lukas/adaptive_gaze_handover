# Gaze Tracking

## Requirements

- Python: 3.10 (please use exact version to prevent errors)
- Install [poetry](https://python-poetry.org/docs/)
- Install [poetry shell plugin](https://github.com/python-poetry/poetry-plugin-shell)

## How to Run

1. Open folder in Terminal
2. Run `poetry env use 3.10` on first execution
3. Execute `poetry shell` to open the Python Virtual Environment
4. On first execution, run `poetry install` to install all python dependencies
5. Run `python fixation_tracking.py` to run the gaze tracking

> Gaze Tracking will take several seconds to start
> You can stop the gaze tracking by pressing STRG+C in the Terminal or `q` in the shown window if `SHOW_IMAGE = True`

# Debugging

- If `poetry install` fails, make sure that you use Python version 3.10!
- You can set the camera input index via `v = cv2.VideoCapture(<index>)` in `fixation_tracking.py`
- If you are unsure about the camera perspective, use `SHOW_IMAGE = True` in `fixation_tracking.py` to display the recorded image
- To experiment with the gaze tracking, you can run `test_pygaze.py`
