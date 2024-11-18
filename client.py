# CR(misha): Why is there an empty line here?
import socket
import json
from socket_utils import receive_message, send_message

def initialize_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # CR(misha): get the host and port as arguments for this function
    client.connect(("localhost", 12345))
    print("Connected to server")
    return client

def send_action(client, action, params=None):
    message = {"action": action, "params": params or {}}
    send_message(client, json.dumps(message))
    response = receive_message(client)
    # CR(misha): Why here you dont deserialize twice?
    return json.loads(response)

# CR(misha): Add typehints or comments explaining what the function returns
def fetch_actions(client):
    # CR(misha): How can the server know that you communicate with the same version?
    #           what if the server for some reason is in a different major then you?
    #           consider adding a version, if you really want to make a fuss out of it you
    #           should pass the protocol version and the client version in the json
    #           this will let the server reject requests from clients with different versions instead of failing
    #           in the best case or doing something else in the worst case
    message = {"action": "get_actions", "params": {}}
    send_message(client, json.dumps(message))
    response = receive_message(client)
    response_data = json.loads(response)  # Parse the JSON response
    # CR(misha): Why is this twice serialized???? it seems like the protocol is not very solid
    #           consider using some kind of pythonic data structure that a message is represented by once finished parsing.
    #           a good idea would be to return a dataclass and before constructing it you would parse and validate
    #           then from that point on you could work with a pythonic data structure
    # The response_data object has nested data, so we also need to parse that before returning

    # CR(misha): Consider splitting the parse and get into two lines, in this case when you have an exception it will
    #           make it easy to understand what is going on and what failed and why
    #           anyway, as said above you should split the fetching to multiple stages
    #           1. get the message
    #           2. validate and parse it to the pythonic data structure
    #           3. do some logic, like in this case get the actions.
    return json.loads(response_data).get("actions", {})  # Now use .get() on the parsed JSON object


# CR(misha): Why the action is needed here?
# CR(misha): add typehinting or at least document what action_params should be, as this is really unclear
def get_interactive_params(action, action_params):
    params = {}
    for param_name in action_params:
        # CR(misha): What if one of the parameters are the content of a file?
        value = input(f"Enter value for {param_name}: ")
        params[param_name] = value
    return params

# CR(misha): This function is called interactive menu but it is doing much more than that.
#           this function should b split into at least 2 function, the UI one that lets the user select in an
#           "interactive" way and a function that handles it result.
#           actually splitting the UI and the Logic is a very good practice, not only splitting them but
#           also declaring a very strong interface between them.
#           if you are planning the interface in a good way this will allow you to switch the UI layer quickly in the future
def interactive_menu(client, actions):
    print("Available actions:")
    print(", ".join(actions.keys()))
    while True:
        action = input("Enter action ('exit' to quit): ").strip()
        if action.lower() == 'exit':
            break
        if action not in actions:
            # CR(misha): A good idea is to remind the user what are the available actions, this is just common UX
            print("Invalid action. Please choose a valid action from the list.")
            continue
        params = get_interactive_params(action, actions[action])
        response = send_action(client, action, params)
        # CR(misha): What if the response is a file?
        print("Response:", response)

if __name__ == "__main__":
    # CR(misha): Put this entire code in a main function.
    # CR(misha): Add argparse to pass different configurations
    client = initialize_client()
    actions = fetch_actions(client)
    interactive_menu(client, actions)
    client.close()
