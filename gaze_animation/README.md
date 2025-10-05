# Gaze Animation

## Requirements

- Python: 3.11 (please use exact version to prevent errors)
- Install [poetry](https://python-poetry.org/docs/)
- Install [poetry shell plugin](https://github.com/python-poetry/poetry-plugin-shell)

## How to Run

1. Open folder in Terminal
2. Execute `poetry shell` to open the Python Virtual Environment
3. On first execution, run `poetry install` to install all python dependencies
4. Run `python server.py` to run the gaze animation in full screen

> You can end the animation by pressing ESC
> Important: The program needs to be focused to record key inputs

A new, improved version of `server.py` is available (`server_new.py`) but was not used in the experiment yet.

## Programs

Programs can be added as Python functions in `programs.py`. Programs need to be added manually to `controller.html` if Web-Control is desired. Else programs can be executed via `curl`.