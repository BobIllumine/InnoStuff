"""
    Created by Robert Chen, BS20-AI

    Client-side for Lab 3 Assignment

    Both worker scripts are almost identical,
    the only two parts that are different are parsing and computing the answer
"""
import signal
import sys
import zmq
from datetime import datetime

# Console arguments for ports
i_port, o_port = map(int, sys.argv[1:])


# Methods for getting current time in HH:MM:SS format
def current_time():
    return datetime.now().strftime("%H:%M:%S")


# Keyboard interrupt handler
def sigint_handler(sig, frame):
    print(f'[{current_time()}] Server terminated, closing the connection')
    sys.exit(0)


def main():
    # Announcing interrupt handler
    signal.signal(signal.SIGINT, sigint_handler)

    # Connecting to client input socket, 5s timeout
    i_context = zmq.Context()
    i_socket = i_context.socket(zmq.REQ)
    i_socket.connect(f'tcp://127.0.0.1:{i_port}')
    i_socket.setsockopt(zmq.RCVTIMEO, 5000)

    # Connecting and subscribing to client output socket, 300ms timeout
    o_context = zmq.Context()
    o_socket = o_context.socket(zmq.SUB)
    o_socket.connect(f'tcp://127.0.0.1:{o_port}')
    o_socket.setsockopt_string(zmq.SUBSCRIBE, '')
    o_socket.setsockopt(zmq.RCVTIMEO, 300)

    # Main loop
    while True:
        message = input(f'[{current_time()}] > ')

        # In case nothing is sent, we just update incoming messages
        if len(message) != 0:
            i_socket.send_string(message)
            try:
                reply = i_socket.recv_string()
                # print(f'DEBUG: server reply - {reply}')
            # Handling timeout on server acknowledgement
            except zmq.Again:
                print(f'[{current_time()}] ERROR: Server timed out')
                sys.exit(0)

        # Constantly polling client output socket
        while True:
            try:
                output = o_socket.recv_string()
                print(f'[{current_time()}] {output}')
            # Buffer is empty, start over
            except zmq.Again:
                break


if __name__ == '__main__':
    main()
