
import os
import socket
import threading
import json
from socket_utils import receive_message, send_message, PROTOCOL_VERSION
import slave
import hashlib
import traceback
from data.data_classes import Request, Response, Action, Param, ParamTypes

SLAVE_FILE_NAME = "slave.py"
update_lock = threading.Lock()

SERVER_MAJOR_VERSION = 1
SERVER_MINOR_VERSION = 0
SERVER_PATCH_VERSION = 0
SERVER_VERSION = f"{SERVER_MAJOR_VERSION}.{SERVER_MINOR_VERSION}.{SERVER_PATCH_VERSION}"

def check_slave(checksum):
    # Calculate checksum of the slave file
    hasher = hashlib.md5()
    with open(SLAVE_FILE_NAME, "rb") as f:
        hasher.update(f.read())
    current_checksum = hasher.hexdigest()
    print(f"Current checksum: {current_checksum}, Provided checksum: {checksum}")
    return current_checksum == checksum

def check_slave_action(params):
    checksum = params.get("checksum")
    if not checksum:
        return Response(success=False, message="No checksum provided")
    if check_slave(checksum):
        return Response(success=True, message="Slave checksum matches")
    else:
        return Response(success=False, message="Slave checksum mismatch")

def update_slave(params):
    update_content = params.get("file_data")
    updated_checksum = params.get("checksum")
    if not update_content:
        # return json.dumps({"success": False, "message": "No file data provided"})
        return Response(success=False, message="No file data provided")
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
                return Response(success=True, message="Slave updated successfully")
            else:
                raise Exception("Slave update check failed")
        except Exception as e:
            print(f"Slave update failed: {e}")
            with open(SLAVE_FILE_NAME, "w") as f:
                f.write(old_content)
            return json.dumps({"success": False, "message": f"Slave update failed: {e}"})

def perform_slave_action(request):
    """
    Perform an action defined in slave.py's ACTIONS.
    """
    action_name = request.action
    params = request.params or {}

    slave_action = next((action for action in slave.ACTIONS if action.name == action_name), None)

    if not slave_action:
        return Response(success=False, message=f"Invalid action: {action_name}")

    # Validate required parameters
    missing_params = [
        param.name for param in slave_action.params
        if param.name not in params or (param.type == ParamTypes.FILE and not params[param.name])
    ]
    if missing_params:
        return Response(success=False, message=f"Missing required parameters: {', '.join(missing_params)}")

    try:
        print(f"Performing slave action: {slave_action.name} with params: {params}")
        result = slave_action.function(params)  # Call the action's function
        return result
    except Exception as e:
        print(f"Error performing slave action {action_name}: {e}")
        traceback.print_exc()
        return Response(success=False, message=f"Error performing action: {e}")


def find_action(action_name):
    """
    Find an Action object by its name from the ACTIONS list.
    """
    for action in ACTIONS:
        if action.name == action_name:
            return action
    return None

def get_actions_with_params(_):
    """
    Provide a list of available actions and their parameter requirements to the client.
    """
    actions_details = [
        {
            "name": action.name,
            "params": [param.to_dict() for param in action.params],
            "response_type": action.response_type.value
        }
        for action in ACTIONS
    ]
    slave_actions = [
        {
            "name": action.name,
            "params": [param.to_dict() for param in action.params],
            "response_type": action.response_type.value
        }
        for action in slave.ACTIONS
    ]

    actions_details.extend(slave_actions)

    return Response(success=True, message=actions_details)


# ACTIONS = {
#     "update_slave": {
#         "function": update_slave,
#         "params": ["file_data", "checksum"]
#     },
#     "get_actions": {
#         "function": get_actions_with_params,
#         "params": []
#     },
#     "check_slave": {
#         "function": check_slave_action,
#         "params": ["checksum"]
#     }
# }

ACTIONS = [
    Action(name="update_slave", params=[
        Param(name="file_data", type=ParamTypes.FILE),
        Param(name="checksum", type=ParamTypes.STRING)
    ], function=lambda params: update_slave(params)),

    Action(name="get_actions", params=[], function=lambda params: get_actions_with_params(params)),

    Action(name="check_slave", params=[
        Param(name="checksum", type=ParamTypes.STRING)
    ], function=lambda params: check_slave_action(params))
]

def add_result_data(result):
    if not result.slave_version:
        result.slave_version = slave.SLAVE_VERSION
    if not result.protocol_version:
        result.protocol_version = PROTOCOL_VERSION
    if not result.server_version:
        result.server_version = SERVER_VERSION
    return result


def handle_client(client, address):
    try:
        while True:
            message = receive_message(client)
            request = Request.from_json(message)
            if not request:
                break

            client_version = request.client_version
            client_version_major = int(client_version.split(".")[0])
            if client_version_major != slave.SLAVE_MAJOR_VERSION:
                response = Response(success=False, message="Incompatible client version!")
                send_message(client, response.to_json())
                break

            action_name = request.action
            params = request.params or {}

            action = find_action(action_name)
            if action:
                print(f"Performing action: {action.name} with params: {params}")
                result = action.function(params)
            else:
                print(f"Action {action_name} not found. Checking slave actions.")
                result = perform_slave_action(request)
            
            result = add_result_data(result)

            send_message(client, result.to_json())
    except Exception as e:
        print(f"Client connection error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
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
