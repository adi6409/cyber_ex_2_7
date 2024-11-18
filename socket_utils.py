# CR(misha): I dont know if socket_utils is the best name here.
#           those are not socket utils but a specific communication implementation,
#           better name would be protocol, communication ....
# CR(misha): socket is not used, remove!
import socket
import struct

CHUNK_SIZE = 4096  # Adjust this as needed for optimal performance

def receive_message(client):
    # CR(misha): Dont put implementation details into the docstring, if someone is going to use this function
    #           and they care about the implementation details, they should read the code (they are programmers)
    # CR(misha): from the docstring it seems like the function could return a partial result but the function name
    #           tells a different story, I would stick with the function name and not the docstring
    """
    Receive a large message in chunks.
    Protocol: <4 bytes for chunk length><chunk data>... <4 bytes '0' for end of message>
    """
    # CR(misha): Using logging you could put this as a debug level as you dont need this log in production.
    print("Receiving message")
    message = b""

    while True:
        # CR(misha): What happnes if you get less than 4 in this case? the documentation tells us that
        #           recv is a best effort function, you should address this issue. I can tell that you kinda addressed this issue
        #           below, put this logic into a helper function and use it across the code.
        length_prefix = client.recv(4)
        # CR(misha): It seems like you do this check and throw a similar error if the connection is closed below.
        #           this is another strong indication this should be put into a helper function
        if not length_prefix:
            raise ConnectionError("Connection closed by sender")
        # CR(misha): If your chunks are 4096 why are you using 4 bytes? it is an over kill.
        chunk_length = struct.unpack('>I', length_prefix)[0]
        if chunk_length == 0:
            break
        chunk = b""
        while len(chunk) < chunk_length:
            # CR(misha): why are you getting the minimum of both? what is the purpose of this?
            #           if you have a real purpose for this consider adding a comment explaining this, as this is not
            #           standard code.
            part = client.recv(min(chunk_length - len(chunk), CHUNK_SIZE))
            if not part:
                raise ConnectionError("Connection closed while receiving data")
            chunk += part

        message += chunk

    # CR(misha): Consider adding more information of the message to the log (eg. length, chunk amount, etc)
    print("Message received")
    # CR(misha): Why are you decoding this message? it is a binary message, how can you tell it should be a string.
    return message.decode()

# CR(misha): consider adding type hinting, eg. def send_message(client: socket.socket, message: bytes):
def send_message(client, message):
    # CR(misha): Same as the comment for the above function.
    """
    Send a large message in chunks.
    Protocol: <4 bytes for chunk length><chunk data>... <4 bytes '0' for end of message>
    """
    # CR(misha): This is clearly a debug print and should not be in production ready code.
    #           anyway, why are you truncating the message? what is the purpose of this?
    print(f"Sending message: {message[:100]}...")
    # CR(misha): Why are you encoding this message? is the message has to be a string?
    message_bytes = message.encode()
    
    # Send the message in chunks
    for i in range(0, len(message_bytes), CHUNK_SIZE):
        # CR(misha): Just a cool trick `chunk = message_bytes[i:][:CHUNK_SIZE]`
        chunk = message_bytes[i:i + CHUNK_SIZE]
        chunk_length = struct.pack('>I', len(chunk))
        client.sendall(chunk_length + chunk)

    # Send the end-of-message indicator
    client.sendall(struct.pack('>I', 0))
    # CR(misha): Consider adding more information of the message to the log (eg. length, chunk amount, etc)
    print("Message sent")
