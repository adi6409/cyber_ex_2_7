import socket
import struct

CHUNK_SIZE = 4096  # Adjust this as needed for optimal performance

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
    return message.decode()

def send_message(client, message):
    """
    Send a large message in chunks.
    Protocol: <4 bytes for chunk length><chunk data>... <4 bytes '0' for end of message>
    """
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
