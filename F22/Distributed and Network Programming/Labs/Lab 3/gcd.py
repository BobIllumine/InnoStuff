"""
    Created by Robert Chen, BS20-AI

    Script for GCD-worker for Lab 3 Assignment
"""
import signal
import zmq
import sys
import math
from datetime import datetime

# Console arguments
i_port, o_port = map(int, sys.argv[1:])


# Methods for getting current time in HH:MM:SS format
def current_time():
    return datetime.now().strftime("%H:%M:%S")


# Keyboard interrupt handler
def sigint_handler(sig, frame):
    print(f'[{current_time()}] Worker terminated, closing the connection')
    sys.exit(0)


def main():
    # Announcing interrupt handler
    signal.signal(signal.SIGINT, sigint_handler)

    # Connecting and subscribing to worker input socket
    print(f'[{current_time()}] Connecting to worker input port...')
    i_context = zmq.Context()
    i_socket = i_context.socket(zmq.SUB)
    i_socket.connect(f'tcp://127.0.0.1:{i_port}')
    i_socket.setsockopt_string(zmq.SUBSCRIBE, 'gcd ')  # Setting a prefix filter
    print(f'[{current_time()}] Connected to worker input port!')

    # Connecting to worker output socket
    print(f'[{current_time()}] Connecting to worker output port...')
    o_context = zmq.Context()
    o_socket = o_context.socket(zmq.PUB)
    o_socket.connect(f'tcp://127.0.0.1:{o_port}')
    print(f'[{current_time()}] Connected to worker output port!')

    # Main loop
    while True:
        # Thread is blocking until it receives something
        # No need in timeout, since it will sometimes
        # result in delays between request and response
        try:
            request = i_socket.recv_string()
            print(f'[{current_time()}] Request: "{request}"')

            # Checking request
            if len(request.split()) != 3:
                print(f'[{current_time()}] Format mismatch, moving on')
                continue

            # Since almighty Python can't provide a decent method for
            # checking if a string is an integer, we need to do some hacks
            a, b = map(lambda x: int(x) if x.lstrip('-').isdigit() else None, request.split()[1:])

            # Not a number, skipping it
            if a is None or b is None:
                print(f'[{current_time()}] Format mismatch, moving on')
                continue

            # Posting to server
            print(f'[{current_time()}] GCD: {math.gcd(a, b)}')
            o_socket.send_string(f'GCD: gcd for {a} {b} is {math.gcd(a, b)}')
        # In case the connection between server and worker is lost
        except zmq.ZMQError:
            print(f'[{current_time()}] ERROR: Server is unreachable')
            sys.exit(0)


if __name__ == '__main__':
    main()
