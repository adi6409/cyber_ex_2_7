import sys
import os
import socket
import time
import threading
import requests
import json
from socket_utils import receive_message, send_message
import slave
import importlib

SLAVE_FILE_NAME = "slave.py"

def check_slave():
    """
    Check if the slave can run without crashes by calling its internal functions.
    """
    try:
        slave.heartbeat()  # Call a heartbeat function in slave if it exists
        return True
    except Exception as e:
        print(f"Slave check failed: {e}")
        return False

def update_slave(params):
    """
    Update the slave file by replacing it with the new content provided in the params.
    Backup the old file before updating and restore if the update fails.
    """
    update_content = params.get("file_data")
    if not update_content:
        return json.dumps({"success": False, "message": "No file data provided"})

    try:
        # Backup the old slave file
        with open(SLAVE_FILE_NAME, "r") as f:
            old_content = f.read()
        with open(f"{SLAVE_FILE_NAME}.bak", "w") as f:
            f.write(old_content)

        # Update the slave file
        with open(SLAVE_FILE_NAME, "w") as f:
            f.write(update_content)
            
        # Check if the updated slave can run without crashes
        if check_slave():
            return json.dumps({"success": True, "message": "Slave updated successfully"})
        else:
            raise Exception("Slave update check failed")
    except Exception as e:
        print(f"Slave update failed: {e}")
        # Restore the old slave file
        with open(SLAVE_FILE_NAME, "w") as f:
            f.write(old_content)
        return json.dumps({"success": False, "message": "Failed to update slave"})

def perform_action(action):
    """
    Perform the specified action by calling functions from the slave module.
    """
    action_name = action.get("action")
    params = action.get("params", {})

    if action_name in slave.ACTIONS:
        result = slave.ACTIONS[action_name](params)
        return json.dumps(result)
    else:
        return json.dumps({"success": False, "message": "Invalid action"})

def get_slave_actions(_):
    """
    Get the list of actions available in the slave module.
    """
    importlib.reload(slave)
    return json.dumps({"success": True, "message": list(slave.ACTIONS.keys())})

ACTIONS = {
    "update_slave": update_slave,
    "check_slave": check_slave,
    "get_actions": get_slave_actions
}

def handle_client(client):
    """
    Handle incoming client connections, receive actions, and respond with results.
    """
    try:
        while True:
            importlib.reload(slave)
            action = receive_message(client)
            if not action:  # Exit loop if no data is received (client disconnected)
                break
            action = json.loads(action)
            if action.get("action") in ACTIONS:
                print(f"Performing action {action['action']}")
                result = ACTIONS[action["action"]](action.get("params"))
            else:
                print("Invalid action, performing through slave")
                result = perform_action(action)

            send_message(client, result)
    except Exception as e:
        print(f"Client connection error: {e}")
    finally:
        client.close()

def main():
    """
    Start the socket server to handle client requests.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 12345))
    server.listen(5)
    print("Server started")
    while True:
        importlib.reload(slave)
        client, address = server.accept()
        # Handle multiple clients, without using threading.
        # Concurrently!!!
        handle_client(client)

if __name__ == "__main__":
    main()