"""
    Created by Robert Chen, BS20-AI

    Script for Primer-worker for Lab 3 Assignment

    Both worker scripts are almost identical,
    the only two parts that are different are parsing and computing the answer
"""
import signal
import zmq
import sys
import math
from datetime import datetime

# Console arguments for ports
i_port, o_port = map(int, sys.argv[1:])


# Class for block-wise Sieve of Eratosthenes algorithm
# Allows to calculate prime numbers up to SQRT_MAX^2 + BLOCK_SIZE
# Time complexity: O(SQRT_MAX * log(log(SQRT_MAX)) pre-processing,
#                  O(BLOCK_SIZE) per query
# Space complexity: O(SQRT_MAX + BLOCK_SIZE)
class Eratosthenes:
    def __init__(self):
        # First, we need to calculate primes up to SQRT_MAX
        self.SQRT_MAX = 100000
        self.BLOCK_SIZE = 10000
        self.non_primes = [False for i in range(self.SQRT_MAX)]
        self.primes = []

        # Usual sieve algorithm, square-root heuristic
        for i in range(2, self.SQRT_MAX):
            if not self.non_primes[i]:
                self.primes.append(i)
                if i * i <= self.SQRT_MAX:
                    for j in range(i * i, self.SQRT_MAX, i):
                        self.non_primes[j] = True

    # Method for checking particular number
    def is_prime(self, n):
        # Binary search to find correct block
        left, right = -1, n // self.BLOCK_SIZE + 1
        while right - left > 1:
            mid = (left + right) // 2
            if n <= mid * self.BLOCK_SIZE:
                right = mid
            else:
                left = mid

        # Needed block number
        k = left
        current_block = [False for i in range(self.BLOCK_SIZE + 1)]

        # Special case for the first block
        if k == 0:
            current_block[0] = current_block[1] = True

        # Going through pre-calculated primes
        for num in self.primes:
            start_idx = (k * self.BLOCK_SIZE + num - 1) // num
            # Filtering out composite numbers
            for j in range(max(start_idx, 2) * num - k * self.BLOCK_SIZE, self.BLOCK_SIZE + 1, num):
                current_block[j] = True

        # Since we found every composite number in the block, we just address the needed one
        return not current_block[n - k * self.BLOCK_SIZE]


# Methods for getting current time in HH:MM:SS format
def current_time():
    return datetime.now().strftime("%H:%M:%S")


# Keyboard interrupt handler
def sigint_handler(sig, frame):
    print(f'[{current_time()}] Worker terminated, closing the connection')
    sys.exit(0)


def main():
    # Initialising the algorithm
    sieve = Eratosthenes()

    # Announcing interrupt handler
    signal.signal(signal.SIGINT, sigint_handler)

    # Connecting and subscribing to worker input socket
    print(f'[{current_time()}] Connecting to worker input port...')
    i_context = zmq.Context()
    i_socket = i_context.socket(zmq.SUB)
    i_socket.connect(f'tcp://127.0.0.1:{i_port}')
    i_socket.setsockopt_string(zmq.SUBSCRIBE, 'isprime ')  # Setting a prefix filter
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
            if len(request.split()) != 2:
                print(f'[{current_time()}] Format mismatch, moving on')
                continue

            # Since almighty Python can't provide a function for
            # checking if string is integer, we need to do some hacks
            n = int(request.split()[1]) if request.split()[1].lstrip('-').isdigit() else None

            # Not a number, skipping it
            if n is None:
                print(f'[{current_time()}] Format mismatch, moving on')
                continue

            # Posting to server
            isprime = sieve.is_prime(n)
            print(f'[{current_time()}] Prime?: {isprime}')
            o_socket.send_string(f'Primer: {n} is ' + ('not ' if not isprime else '') + 'prime')
        # In case the connection between server and worker is lost
        except zmq.ZMQError:
            print(f'[{current_time()}] ERROR: Server is unreachable')
            sys.exit(0)


if __name__ == '__main__':
    main()
