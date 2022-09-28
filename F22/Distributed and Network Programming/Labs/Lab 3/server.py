"""
    Created by Robert Chen, BS20-AI

    Server-side for Lab 3 Assignment
"""
from datetime import datetime
import signal
import sys
import zmq

# Console arguments for port binding
ci_port, co_port, wi_port, wo_port = map(int, sys.argv[1:])


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

    # Binding client input port (REQ-REP)
    print(f'[{current_time()}] Binding client input port...')
    ci_context = zmq.Context()
    client_inputs = ci_context.socket(zmq.REP)
    client_inputs.bind(f'tcp://127.0.0.1:{ci_port}')
    print(f'[{current_time()}] Client input port bind completed!')

    # Binding client input port (PUB-SUB)
    print(f'[{current_time()}] Binding client output port...')
    co_context = zmq.Context()
    client_outputs = co_context.socket(zmq.PUB)
    client_outputs.bind(f'tcp://127.0.0.1:{co_port}')
    print(f'[{current_time()}] Client output port bind completed!')

    # Binding worker input port (PUB-SUB)
    print(f'[{current_time()}] Binding worker input port...')
    wi_context = zmq.Context()
    worker_inputs = wi_context.socket(zmq.PUB)
    worker_inputs.bind(f'tcp://127.0.0.1:{wi_port}')
    print(f'[{current_time()}] Worker input port bind completed!')

    # Binding worker output socket (PUB-SUB), 300ms timeout
    print(f'[{current_time()}] Binding worker output port...')
    wo_context = zmq.Context()
    worker_outputs = wo_context.socket(zmq.SUB)
    worker_outputs.bind(f'tcp://127.0.0.1:{wo_port}')
    worker_outputs.setsockopt_string(zmq.SUBSCRIBE, '')
    worker_outputs.setsockopt(zmq.RCVTIMEO, 300)
    print(f'[{current_time()}] Worker output port bind completed!')

    # Main loop
    while True:
        # Thread is blocking until it receives something
        try:
            client_message = client_inputs.recv_string()
        # In case we lost connection to client input socket
        except zmq.ZMQError:
            print(f'[{current_time()}] ERROR: Client is unreachable')
            continue

        print(f'[{current_time()}] Client: "{client_message}"')
        client_inputs.send_string(f'ok "{client_message}"')  # Acknowledgement reply
        worker_inputs.send_string(client_message)  # Retransmitting message to workers
        client_outputs.send_string('Anonymous: ' + client_message)  # Posting it back to clients

        # Constantly polling worker output buffer
        while True:
            try:
                worker_message = worker_outputs.recv_string()
                print(f'[{current_time()}] Worker: "{worker_message}"')
                client_outputs.send_string(worker_message)
            # Handling timeout, worker output is either empty or worker is disconnected
            except zmq.Again:
                print(f'[{current_time()}] Worker: processing...')
                break
            # In case the connection between server and worker is lost
            except zmq.ZMQError:
                print(f'[{current_time()}] ERROR: Worker is unreachable')
                break


if __name__ == '__main__':
    main()
