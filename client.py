import socket
import json
from socket_utils import receive_message, send_message, PROTOCOL_VERSION
from data.data_classes import Request, Response, ParamTypes, Action, Param

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 12345
CLIENT_VERSION = "1.0.0"

def initialize_client(host, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print("Connected to server")
    return client

def send_action(client, action, params=None):
    message = Request(client_version=CLIENT_VERSION, protocol_version=PROTOCOL_VERSION, action=action, params=params or {})
    send_message(client, message.to_json())
    response = receive_message(client)
    response = Response.from_json(response)
    return response

def fetch_actions(client):
    """
    Fetch the list of actions from the server and parse them into Action objects.
    """
    response = send_action(client, "get_actions")
    if not response.success:
        print("Failed to fetch actions from server")
        return []

    actions_data = response.message  # List of action dictionaries
    actions = [Action.from_dict(action) for action in actions_data]
    return actions


def get_interactive_params(action):
    """
    Prompt the user for parameters required by an action.
    """
    params = {}
    for param in action.params:
        if param.type == ParamTypes.FILE:
            # For file input, read the file's content
            file_path = input(f"Enter file path for {param.name}: ").strip()
            try:
                with open(file_path, "rb") as file:
                    params[param.name] = file.read().decode("latin-1")
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue
        else:
            value = input(f"Enter value for {param.name}: ").strip()
            params[param.name] = value
    return params


def handle_response_file(response_message):
    """
    Handle file-type response by saving it to a user-specified path.
    """
    destination_path = input("Enter destination path to save the file: ").strip()
    try:
        with open(destination_path, "wb") as file:
            file.write(response_message.encode("latin-1"))
        print(f"File saved successfully to {destination_path}")
    except Exception as e:
        print(f"Error saving file to {destination_path}: {e}")

def interactive_menu(client, actions):
    """
    Display an interactive menu for the user to perform actions.
    """
    print("Available actions:")
    for action in actions:
        print(f" - {action.name}, params: {[param.name for param in action.params]}")

    while True:
        action_name = input("Enter action ('exit' to quit): ").strip()
        # if action_name.lower() == 'exit':
        #     break

        # Implement graceful exit
        if action_name.lower() == 'exit':
            response = send_action(client, "exit")
            print(f"Success: {response.success}")
            print(f"Message: {response.message}")
            if client.is_connected():
                client.close()

        action = next((a for a in actions if a.name == action_name), None)
        if not action:
            print("Invalid action. Please choose a valid action from the list.")
            continue

        params = get_interactive_params(action)
        response = send_action(client, action.name, params)

        print(f"Success: {response.success}")
        if response.success:
            if action.response_type == ParamTypes.FILE:
                handle_response_file(response.message)
            else:
                print(f"Message: {response.message}")
        else:
            print(f"Error: {response.message}")
        print(f"Slave version: {response.slave_version}")
        print(f"Server version: {response.server_version}")



if __name__ == "__main__":
    host = input(f"Enter host (default: {DEFAULT_HOST}): ").strip() or DEFAULT_HOST
    port = int(input(f"Enter port (default: {DEFAULT_PORT}): ").strip() or DEFAULT_PORT)
    client = initialize_client(host, port)
    actions = fetch_actions(client)
    interactive_menu(client, actions)
    client.close()
