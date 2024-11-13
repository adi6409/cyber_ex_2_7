
import os
import socket
import threading
import json
from socket_utils import receive_message, send_message
import slave

SLAVE_FILE_NAME = "slave.py"
update_lock = threading.Lock()

def check_slave(checksum):
    # Calculate checksum of the slave file
    import hashlib
    hasher = hashlib.md5()
    with open(SLAVE_FILE_NAME, "rb") as f:
        hasher.update(f.read())
    current_checksum = hasher.hexdigest()
    return current_checksum == checksum

def check_slave_action(params):
    checksum = params.get("checksum")
    if not checksum:
        return json.dumps({"success": False, "message": "No checksum provided"})
    if check_slave(checksum):
        return json.dumps({"success": True, "message": "Slave checksum matches"})
    else:
        return json.dumps({"success": False, "message": "Slave checksum mismatch"})

def update_slave(params):
    update_content = params.get("file_data")
    updated_checksum = params.get("checksum")
    if not update_content:
        return json.dumps({"success": False, "message": "No file data provided"})
    backup_file = f"{SLAVE_FILE_NAME}.bak"
    with update_lock:
        try:
            if os.path.exists(backup_file):
                os.remove(backup_file)
            with open(SLAVE_FILE_NAME, "r") as f:
                old_content = f.read()
            with open(backup_file, "w") as f:
                f.write(old_content)

            with open(SLAVE_FILE_NAME, "w") as f:
                f.write(update_content)

            if check_slave(checksum=updated_checksum):
                return json.dumps({"success": True, "message": "Slave updated successfully"})
            else:
                raise Exception("Slave update check failed")
        except Exception as e:
            print(f"Slave update failed: {e}")
            with open(SLAVE_FILE_NAME, "w") as f:
                f.write(old_content)
            return json.dumps({"success": False, "message": "Failed to update slave"})

def perform_action(action):
    action_name = action.get("action")
    params = action.get("params", {})
    if action_name in slave.ACTIONS:
        result = slave.ACTIONS[action_name]["function"](params)
        return json.dumps(result)
    else:
        return json.dumps({"success": False, "message": "Invalid action"})


def get_actions_with_params(_):
    global ACTIONS
    # Provide ACTIONS with parameter requirements from slave.py to the client
    actions = {action: details["params"] for action, details in slave.ACTIONS.items()}
    # Add ACTIONS and params for actions in this file
    main_file_actions = {action: details["params"] for action, details in ACTIONS.items()}
    actions.update(main_file_actions)
    return json.dumps({"success": True, "actions": actions})

ACTIONS = {
    "update_slave": {
        "function": update_slave,
        "params": ["file_data", "checksum"]
    },
    "get_actions": {
        "function": get_actions_with_params,
        "params": []
    },  # Send actions and params to the client
    "check_slave": {
        "function": check_slave,
        "params": ["checksum"]
    }
}

def handle_client(client, address):
    try:
        while True:
            action = receive_message(client)
            if not action:
                break
            action = json.loads(action)
            action_name = action.get("action")
            if action_name in ACTIONS:
                action_info = ACTIONS[action_name]
                function = action_info["function"]
                params = {k: action.get(k) for k in action_info["params"]}
                result = function(params)                        
                result = json.dumps(result)

            else:
                result = perform_action(action)
            send_message(client, result)
    except Exception as e:
        print(f"Client connection error: {e}")
    finally:
        client.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 12345))
    server.listen(5)
    print("Server started")
    while True:
        client, address = server.accept()
        handle_client(client, address)

if __name__ == "__main__":
    main()
