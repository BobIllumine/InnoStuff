"""
    Created by Robert Chen, BS20-AI

    Client-side script for Lab 4 Assignment
"""
import signal
import grpc
import service_pb2 as pb2
import service_pb2_grpc as pb2_grpc
import sys

# Getting address from command line
addr = sys.argv[1]


# Keyboard interrupt handler
def sig_handler(sig, frame):
    print('Client terminated by keyboard interrupt')
    sys.exit(0)


# Method for parsing input commands
def input_parser(stub, prefix, args):
    # Handling "exit" command
    if prefix == 'exit':
        print('Shutting down')
        sys.exit(0)
    # No args provided -- just echo
    elif len(args) == 0:
        print(prefix)
    # Reverse request
    elif prefix == 'reverse':
        msg = pb2.ReverseRequest(message=args)
        reply = stub.reverse(msg)
        print(f'message: "{reply.message}"')
    # Split request
    elif prefix == 'split':
        msg = pb2.SplitRequest(message=args, delim=' ')
        reply = stub.split(msg)
        print(f'length: {reply.length}')
        for i in reply.parts:
            print(f'part: "{i}"')
    # Primality request
    elif prefix == 'isprime':
        msg = iter([pb2.IsPrimeRequest(message=int(x)) for x in args.split(' ')])
        reply = stub.isprime(msg)
        for i in reply:
            print(f'{i.message}')
    # Any other input
    else:
        print(prefix, args)


# Main method
def main():
    # Announcing interrupt handler
    signal.signal(signal.SIGINT, sig_handler)
    # To make sure the connection will be closed
    with grpc.insecure_channel(addr) as channel:
        stub = pb2_grpc.ServerStub(channel)
        # Main loop
        while True:
            s = input('> ')
            # Parsing no args input
            if s.count(' ') == 0:
                input_parser(stub, s, [])
                continue
            prefix, args = s.split(' ', 1)
            input_parser(stub, prefix, args)


if __name__ == '__main__':
    main()
