
import socket
import json
from socket_utils import receive_message, send_message

def initialize_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 12345))
    print("Connected to server")
    return client

def send_action(client, action, params=None):
    message = {"action": action, "params": params or {}}
    send_message(client, json.dumps(message))
    response = receive_message(client)
    return json.loads(response)

def fetch_actions(client):
    message = {"action": "get_actions", "params": {}}
    send_message(client, json.dumps(message))
    response = receive_message(client)
    response_data = json.loads(response)  # Parse the JSON response
    # The response_data object has nested data, so we also need to parse that before returning
    
    return json.loads(response_data).get("actions", {})  # Now use .get() on the parsed JSON object


def get_interactive_params(action, action_params):
    params = {}
    for param_name in action_params:
        value = input(f"Enter value for {param_name}: ")
        params[param_name] = value
    return params

def interactive_menu(client, actions):
    print("Available actions:")
    print(", ".join(actions.keys()))
    while True:
        action = input("Enter action ('exit' to quit): ").strip()
        if action.lower() == 'exit':
            break
        if action not in actions:
            print("Invalid action. Please choose a valid action from the list.")
            continue
        params = get_interactive_params(action, actions[action])
        response = send_action(client, action, params)
        print("Response:", response)

if __name__ == "__main__":
    client = initialize_client()
    actions = fetch_actions(client)
    interactive_menu(client, actions)
    client.close()
