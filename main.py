# CR(misha): Why is there a new line here?
# CR(misha): Please dont name the file main.py it should indicate what is the purpose of the file and not "main"
#           This is because you have multiple "main"s
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
    # CR(misha): Dont import inside a function this might cause an unexpected side effects that you dont want to happend dynamicly
    import hashlib
    hasher = hashlib.md5()
    with open(SLAVE_FILE_NAME, "rb") as f:
        # CR(misha): Instead of reading all the file at once read it in chunks to save memory
        hasher.update(f.read())
    current_checksum = hasher.hexdigest()
    # CR(misha): Instead of returning bool return the digest this will let you do more checks at home.
    #           maybe if you save all the checksums of all the versions you could compare them and discover which one is installed
    return current_checksum == checksum

def check_slave_action(params):
    # CR(misha): What if one of them is None? you should check this and handle it!
    checksum = params.get("checksum")
    if not checksum:
        return json.dumps({"success": False, "message": "No checksum provided"})
    if check_slave(checksum):
        return json.dumps({"success": True, "message": "Slave checksum matches"})
    else:
        return json.dumps({"success": False, "message": "Slave checksum mismatch"})

# CR(misha): This function is not working, fix it so it will work
def update_slave(params):
    update_content = params.get("file_data")
    # CR(misha): What if one of them is None? you should check this and handle it!
    updated_checksum = params.get("checksum")
    if not update_content:
        return json.dumps({"success": False, "message": "No file data provided"})
    # CR(misha): Not really part of the code but add the .bak to the .gitignore
    backup_file = f"{SLAVE_FILE_NAME}.bak"
    # CR(misha): you are single threaded, why are you using a lock? locks are expensive and prone to deadlocks
    with update_lock:
        try:
            # CR(misha): This try block is too big, split it into smaller functions. it is hard to read!
            if os.path.exists(backup_file):
                os.remove(backup_file)
            # CR(misha): Use shutil instead of reading all the file into memory and then writing it.
            #           but if you need to read then write do it in chunks to save memory
            # CR(misha): Why are you reading and decoding here?
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
            # CR(misha): use logging module
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
        # CR(misha): Add log for that case
        return json.dumps({"success": False, "message": "Invalid action"})



def get_actions_with_params(_):
    # CR(misha): You dont need to declare global in this function, on the same note, dont ever use global keywords
    #           mutable objects are considered a very bad practice and should never ever be used!!!!!
    #           they are the cause of so many bugs you cant even imagine!!!!
    #           if you want a lecture on why globals are bad, talk to me IRL
    global ACTIONS
    # Provide ACTIONS with parameter requirements from slave.py to the client

    actions = {action: details["params"] for action, details in slave.ACTIONS.items()}
    # Add ACTIONS and params for actions in this file
    main_file_actions = {action: details["params"] for action, details in ACTIONS.items()}
    actions.update(main_file_actions)
    return json.dumps({"success": True, "actions": actions})

# CR(misha): ACTIONS are not a good name, everything is "actions" those are special, address that!
ACTIONS = { # CR(misha): Add a type explaining what this should be
    "update_slave": {
        "function": update_slave,
        # CR(misha): A cool feature would be to have the function declare the params like it needs them and then you
        #           could deduce them dynamicly and pass them as **kwargs. this is a very helpful devex feature
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

# CR(misha): It seems address is not used, why?
def handle_client(client, address):
    # CR(misha): putting a large amount of code (more then a few lines) between try makes it harder to understand what happnes
    #           split the internal logic into one or few helper functions just to help with readability.
    #           in the future when you will make the logic inside bigger you wont need to worry about this
    try:
        while True:
            # CR(misha): This entire while body should have only 3 function calls: recv, dispatch, send. 3 lines that is it!
            #           that makes the main loop much more readable and will be easier to maintain
            # CR(misha): action is not the correct name here, this is the message or raw_action but action it is deffinatly not!
            action = receive_message(client)
            if not action:
                # CR(misha): Why are you breaking here? if this is intended add a comment explaining why, because it is not clear
                break
            action = json.loads(action)
            action_name = action.get("action")
            if action_name in ACTIONS:
                # CR(misha): This if body is its own function
                # CR(misha): it seems like this code and the code in perform action are pretty much the same
                action_info = ACTIONS[action_name]
                function = action_info["function"]
                params = {k: action.get(k) for k in action_info["params"]}
                # CR(misha): See the kwargs message above.
                result = function(params)                        
                result = json.dumps(result)

            else:
                result = perform_action(action)
            send_message(client, result)
    except Exception as e:
        # CR(misha): Consider using logging module
        #           1. this is a built-in module of python
        #           2. it gives you much more context on where the log is coming from
        #           3. it lets you control the output (format, stream, logging level, ...) better
        print(f"Client connection error: {e}")
    finally:
        client.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # CR(misha): Using argparser or some other configuration tool lets you in the future the ability to run this code \
    #           differently without having to change the code. Use argparse at least!
    #           In any case dont put "magic" numbers and consts in the middle of a code, at leaset put them at the top of the file as a const
    server.bind(("0.0.0.0", 12345))
    server.listen(5)
    print("Server started")
    while True:
        client, address = server.accept()
        handle_client(client, address)
        # CR(misha): A general rule of thumb is that you need to handle closing of a client connection. where you created it.
        #           This is a good practice because it helps you to handle resources better.
        #           Saying that ...in python, especially in the newer version it is not that critical

if __name__ == "__main__":
    main()
