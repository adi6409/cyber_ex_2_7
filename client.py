import socket
from socket_utils import receive_message, send_message
import json

# message = '{"action": "take_screen_shot","params": ""}'
# message = '{"action": "get_actions","params": ""}'


# message = {
#     "action": "upload_file",
#     "params": {
#         "file_data": open("/Users/astroianu/Downloads/manufacturers.json", "rb").read().decode("latin-1"),
#         "destination_path": "/home/adi/cybertest/manufacturers.json"
#     }
# }

# message = {
#     "action": "download_file",
#     "params": {
#         "file_path": "/Users/astroianu/Downloads/MOB2411IL001.png"
#     }
# }

message_to_check_actions = {
    "action": "get_actions",
    "params": ""
}


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("localhost", 12345))
print("Connected to server")


def get_actions():
    send_message(client, json.dumps(message_to_check_actions))
    response = receive_message(client)
    print("Got response")
    parsed_response = json.loads(response)["message"]
    print(f"Available actions: {parsed_response}")
    return parsed_response


# This file will be an interactive shell that will allow us to interact with the server.
# It will display the available actions and allow us to choose the action we want to perform.
# After choosing an action, it will prompt us for any required parameters and send the action to the server.

def main():
    while True:
        actions = get_actions()
        print("Available actions:")
        for i, action in enumerate(actions):
            print(f"{i + 1}. {action}")
        choice = int(input("Choose an action: ")) - 1
        action_name = actions[choice]
        print(f"Chose action: {action_name}")
        params = {}
        for param in actions[action_name]:
            params[param] = input(f"Enter value for {param}: ")
        message = {
            "action": action_name,
            "params": params
        }
        send_message(client, json.dumps(message))
        response = receive_message(client)
        print(response)

if __name__ == "__main__":
    main()


