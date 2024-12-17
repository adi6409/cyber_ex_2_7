import os
import socket
import threading
import json
import hashlib
import traceback
from socket_utils import PROTOCOL_VERSION
import socket_utils as protocol
import slave
from data.data_classes import Request, Response, Action, Param, ParamTypes

SLAVE_FILE_NAME = "slave.py"
update_lock = threading.Lock()

SERVER_MAJOR_VERSION = 1
SERVER_MINOR_VERSION = 0
SERVER_PATCH_VERSION = 0
SERVER_VERSION = f"{SERVER_MAJOR_VERSION}.{SERVER_MINOR_VERSION}.{SERVER_PATCH_VERSION}"

def calculate_checksum(file_name):
    """Calculate and return MD5 checksum of a file."""
    hasher = hashlib.md5()
    with open(file_name, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def check_slave_provided(checksum):
    """Verify slave file checksum with the provided one."""
    current_checksum = calculate_checksum(SLAVE_FILE_NAME)
    print(f"Current checksum: {current_checksum}, Provided checksum: {checksum}")
    return current_checksum == checksum

def check_slave_action(params):
    """Validate checksum for slave file."""
    checksum = params.get("checksum")
    if not checksum:
        return Response(success=False, message="No checksum provided")
    return (Response(success=True, message="Slave checksum matches")
            if check_slave_provided(checksum)
            else Response(success=False, message="Slave checksum mismatch"))

def create_backup():
    """Create a backup of the current slave file."""
    backup_file = f"{SLAVE_FILE_NAME}.bak"
    if os.path.exists(backup_file):
        os.remove(backup_file)
    with open(SLAVE_FILE_NAME, "r") as f:
        with open(backup_file, "w") as backup:
            backup.write(f.read())

def update_slave_file(content):
    """Overwrite slave file with new content."""
    with open(SLAVE_FILE_NAME, "w") as f:
        f.write(content)

def restore_backup():
    """Restore the backup to the slave file."""
    with open(f"{SLAVE_FILE_NAME}.bak", "r") as f:
        update_slave_file(f.read())

def update_slave(params):
    """Update the slave file and validate its checksum."""
    file_data = params.get("file_data")
    updated_checksum = params.get("checksum")
    if not file_data:
        return Response(success=False, message="No file data provided")
    with update_lock:
        try:
            create_backup()
            update_slave_file(file_data)
            if check_slave_provided(updated_checksum):
                return Response(success=True, message="Slave updated successfully")
            raise Exception("Slave update check failed")
        except Exception as e:
            restore_backup()
            return Response(success=False, message=f"Slave update failed: {e}")

def get_action_details():
    """Return a list of actions with parameters."""
    all_actions = ACTIONS + slave.ACTIONS
    return [
        {
            "name": action.name,
            "params": [param.to_dict() for param in action.params],
            "response_type": action.response_type.value
        } for action in all_actions
    ]

def get_actions_with_params(_):
    """Respond with a list of available actions and their parameters."""
    return Response(success=True, message=get_action_details())

def handle_request_with_slave(request):
    """Handle an action request using the slave module."""
    slave_action = find_slave_action(request.action)
    if not slave_action:
        return Response(success=False, message=f"Invalid action: {request.action}")
    missing_params = find_missing_params(slave_action, request.params)
    if missing_params:
        return Response(success=False, message=f"Missing parameters: {', '.join(missing_params)}")
    return execute_slave_action(slave_action, request.params)

def find_slave_action(action_name):
    """Find an action in slave.ACTIONS."""
    return next((action for action in slave.ACTIONS if action.name == action_name), None)

def find_missing_params(action, params):
    """Identify missing required parameters."""
    return [
        param.name for param in action.params
        if param.name not in params or (param.type == ParamTypes.FILE and not params[param.name])
    ]

def execute_slave_action(action, params):
    """Execute a slave action and handle exceptions."""
    try:
        print(f"Performing slave action: {action.name} with params: {params}")
        return action.function(params)
    except Exception as e:
        print(f"Error performing slave action {action.name}: {e}")
        traceback.print_exc()
        return Response(success=False, message=f"Error performing action: {e}")

def validate_client_version(request):
    """Ensure client version compatibility."""
    client_version_major = int(request.client_version.split(".")[0])
    if client_version_major != slave.SLAVE_MAJOR_VERSION:
        return Response(success=False, message="Incompatible client version!")
    return request

def get_client_request(client):
    """Receive and parse client request."""
    message = protocol.receive_message(client)
    request = Request.from_json(message)
    if not request:
        return None
    request = validate_client_version(request)
    return request

def process_request(request):
    """Process the client's action request."""
    action = find_action(request.action)
    if action:
        return action.function(request.params or {})
    return handle_request_with_slave(request)

def send_response(client, response):
    """Send response back to the client."""
    protocol.send_message(client, response.to_json())

def handle_client(client, address):
    """Handle communication with a connected client."""
    try:
        while True:
            request = get_client_request(client)
            if not request or request.action == "exit":
                break
            response = process_request(request)
            send_response(client, add_result_data(response))
    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        client.close()

def add_result_data(result):
    """Add protocol and server version information to response."""
    result.protocol_version = result._ret_set(result.protocol_version, PROTOCOL_VERSION)
    result.server_version = result._ret_set(result.server_version, SERVER_VERSION)
    result.slave_version = result._ret_set(result.slave_version, slave.SLAVE_VERSION)
    return result

def find_action(action_name):
    """Find an Action object by name."""
    return next((action for action in ACTIONS if action.name == action_name), None)

def main():
    """Start the server to accept incoming connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 12345))
    server.listen(5)
    print("Server started")
    while True:
        client, address = server.accept()
        threading.Thread(target=handle_client, args=(client, address)).start()

ACTIONS = [
    Action(name="update_slave", params=[
        Param(name="file_data", type=ParamTypes.FILE),
        Param(name="checksum", type=ParamTypes.STRING)
    ], function=update_slave),
    Action(name="get_actions", params=[], function=get_actions_with_params),
    Action(name="check_slave", params=[
        Param(name="checksum", type=ParamTypes.STRING)
    ], function=check_slave_action)
]

if __name__ == "__main__":
    main()
