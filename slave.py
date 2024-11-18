# CR(misha): Why is there an empty line here?
import os
import json
import subprocess
import argparse

def format_message_response(is_success, message):
    # CR(misha): consider adding version of the protocol or the "slave"
    return {"success": is_success, "message": message}

def take_screen_shot(_):
    if os.name == 'nt':  # Windows
        import pyautogui
        screenshot = pyautogui.screenshot()
        # CR(misha): Why save to storage and then reading it again? this is a waste of IO and time. send it from memory
        screenshot.save("screenshot.png")
    else:  # macOS and Linux
        # CR(misha): Huh??? WTF is this? this should be installed, where is it installed???
        subprocess.run(["screencapture", "screenshot.png"] if os.name == 'posix' and os.uname().sysname == 'Darwin' else ["import", "-window", "root", "screenshot.png"])
    with open("screenshot.png", "rb") as f:
        image = f.read()
    # CR(misha): Why are you decoding this message?????? this is a binary image not a string.
    #           pass it as is or encode it yourself in some other way
    return format_message_response(True, image.decode("latin-1"))

def heartbeat():
    # CR(misha): this is not formatted as the message response. any way why you need a heartbeat in this case?
    #           and if so why isn't it a basic action instead of part of a slave
    return True

def upload_file(params):
    # CR(misha): What if the file is really huge? how would you handle this?
    file_data = params.get("file_data")
    destination_path = params.get("destination_path")
    # CR(misha): What if the file data is empty an buffer, how would you handle this? `file_data is None`
    if not file_data or not destination_path:
        # CR(misha): Add log here or something
        return format_message_response(False, "Invalid parameters")
    with open(destination_path, "wb") as f:
        # CR(misha): Why why why why why is this a latin-1 encoding?!?!
        f.write(file_data.encode("latin-1"))
    return format_message_response(True, f"File uploaded to {destination_path}")

def download_file(params):
    file_name = params.get("file_path")
    if not file_name or not os.path.exists(file_name):
        # CR(misha): Add log here or something
        # CR(misha): `not file_name` is not File not found
        return format_message_response(False, "File not found")
    with open(file_name, "rb") as f:
        file_data = f.read()
    # CR(misha): Still I dont get it, why is this a latin-1 encoding?
    return format_message_response(True, file_data.decode("latin-1"))

def set_clipboard(params):
    text = params.get("text")
    if not text:
        # CR(misha): Add log here or something
        return format_message_response(False, "Invalid parameters")
    # CR(misha): Is this works out of the box? you need to install something? what if the os is different?
    process = subprocess.Popen("pbcopy", env={"LANG": "en_US.UTF-8"}, stdin=subprocess.PIPE)
    # CR(misha): Why is this a utf-8 encoding?
    process.communicate(text.encode("utf-8"))
    # CR(misha): What if the process never terminates?
    return format_message_response(True, "Clipboard set")

def get_clipboard(_):
    process = subprocess.Popen("pbpaste", stdout=subprocess.PIPE)
    output, _ = process.communicate()
    # CR(misha): close the process
    # CR(misha): Why utf-8?
    return format_message_response(True, output.decode("utf-8"))

def list_directory(params):
    directory = params.get("directory")
    # CR(misha): Make sure this is a valid directory
    if not directory or not os.path.exists(directory):
        # CR(misha): Add log here or something
        # CR(misha): `not directory` is not an invalid directory
        return format_message_response(False, "Invalid directory")
    # CR(misha): How can you differentiate between files and directories?
    files = os.listdir(directory)
    return format_message_response(True, files)

def rm_file(params):
    file = params.get("file")
    if not file or not os.path.exists(file):
        # CR(misha): Add log here or something
        # CR(misha): `not file` is not an invalid file
        return format_message_response(False, "Invalid file")
    # CR(misha): What if this is a directory and not a file?
    os.remove(file)
    return format_message_response(True, "File removed")

def copy_file(params):
    source = params.get("source")
    destination = params.get("destination")
    # CR(misha): What if destination exists or if source is a directory?
    if not source or not destination or not os.path.exists(source):
        # CR(misha): Add log here or something
        # CR(misha): split the response messages if the dest is invalida or the source is invalid
        return format_message_response(False, "Invalid source or destination")
    # CR(misha): cp is not a valid command in windows, use shutil!
    os.system(f"cp {source} {destination}")
    return format_message_response(True, "File copied")

def run_command(params):
    command = params.get("command")
    if not command:
        return format_message_response(False, "Invalid command")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    # CR(misha): what about the exit code? what if the process never terminates?
    return format_message_response(True, output.decode("utf-8") + error.decode("utf-8"))


# CR(misha): A cool feature would be to have the function declare the params like it needs them and then you
#           could deduce them dynamicly and pass them as **kwargs. this is a very helpful devex feature
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
