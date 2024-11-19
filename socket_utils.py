import socket
import json
import struct

CHUNK_SIZE = 4096  # Adjust this as needed for optimal performance
PROTOCOL_MAJOR_VERSION = 1
PROTOCOL_MINOR_VERSION = 0
PROTOCOL_PATCH_VERSION = 0
PROTOCOL_VERSION = f"{PROTOCOL_MAJOR_VERSION}.{PROTOCOL_MINOR_VERSION}.{PROTOCOL_PATCH_VERSION}"

def receive_message(client):
    """
    Receive a large message in chunks.
    Protocol: <4 bytes for chunk length><chunk data>... <4 bytes '0' for end of message>
    """
    print("Receiving message")
    message = b""

    while True:
        length_prefix = client.recv(4)
        if not length_prefix:
            raise ConnectionError("Connection closed by sender")
        chunk_length = struct.unpack('>I', length_prefix)[0]
        if chunk_length == 0:
            break
        chunk = b""
        while len(chunk) < chunk_length:
            part = client.recv(min(chunk_length - len(chunk), CHUNK_SIZE))
            if not part:
                raise ConnectionError("Connection closed while receiving data")
            chunk += part

        message += chunk

    print("Message received")
    decoded_message = message.decode()
    message_json = json.loads(decoded_message)
    try:
        protocol_version = message_json.get("protocol_version")
        # parse the protocol version and compare the major version
        major_version = int(protocol_version.split(".")[0])
        if major_version != PROTOCOL_MAJOR_VERSION:
            return {"success": False, "message": "Incompatible protocol version"}
        return message_json
    except json.JSONDecodeError:
        return {"success": False, "message": "Invalid JSON received! possible version mismatch"}
    except ValueError:
        return {"success": False, "message": "Invalid protocol version received!"}



def send_message(client, message):
    """
    Send a large message in chunks.
    Protocol: <4 bytes for chunk length><chunk data>... <4 bytes '0' for end of message>
    """
    print(f"Sending message {message}")
    message_dict = json.loads(message)
    if "protocol_version" not in message_dict or not message_dict["protocol_version"]:
        message_dict["protocol_version"] = PROTOCOL_VERSION
        message = json.dumps(message_dict)
    print(f"Sending message: {message[:100]}...")
    message_bytes = message.encode()
    
    # Send the message in chunks
    for i in range(0, len(message_bytes), CHUNK_SIZE):
        chunk = message_bytes[i:i + CHUNK_SIZE]
        chunk_length = struct.pack('>I', len(chunk))
        client.sendall(chunk_length + chunk)

    # Send the end-of-message indicator
    client.sendall(struct.pack('>I', 0))
    print("Message sent")
