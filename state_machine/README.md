# State Machine

## Requirements

- Python: >=3.11
- Install [poetry](https://python-poetry.org/docs/)
- Install [poetry shell plugin](https://github.com/python-poetry/poetry-plugin-shell)

## How to Run

1. Open folder in Terminal
2. Execute `poetry shell` to open the Python Virtual Environment
3. On first execution, run `poetry install` to install all python dependencies
4. Edit `demo.env` (for demonstration trials) or `prod.env` (for experimental trials)
5. Run `source demo.env` or `source prod.env` every time you want to apply one of the configs
6. Run `uvicorn main:app --port 1111` to run the state machine web server
7. Make sure the logs show the right configuration at the start of the web server

> Hint: Use STRG+C to end the state machine
> Important: The data logger writes the experiment logs to the output/ directory as soon as the state machine is stopped. Only sessions with recorded handovers and/or gazes will be logged
