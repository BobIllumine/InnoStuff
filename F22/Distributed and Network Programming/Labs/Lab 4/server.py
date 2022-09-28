"""
    Created by Robert Chen, BS20-AI

    Server-side script for Lab 4 Assignment
"""
import grpc
import sys
from concurrent import futures
import service_pb2 as pb2
import service_pb2_grpc as pb2_grpc
from datetime import datetime
from time import time

# Getting port number from command line
port = sys.argv[1]


# Method for getting current time in HH:MM:SS format
def current_time():
    return datetime.now().strftime("%H:%M:%S")


# Method for logging any message
def log(message: str):
    print(f'[{current_time()}] {message}')


# Class for block-wise Sieve of Eratosthenes algorithm
# Allows to calculate prime numbers up to SQRT_MAX^2 + BLOCK_SIZE
# Time complexity: O(SQRT_MAX * log(log(SQRT_MAX)) pre-processing,
#                  O(BLOCK_SIZE) per query
# Space complexity: O(SQRT_MAX + BLOCK_SIZE)
class Eratosthenes:
    def __init__(self):
        log('Preprocessing started')
        # For elapsed time measurement
        precalc_st = time()
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

        precalc_fin = time() - precalc_st
        log(f'Preprocessing ended, time elapsed - {precalc_fin}s')

    # Method for checking particular number
    def is_prime(self, n):

        log(f'Query started, args - {n}')
        # For elapsed time measurement
        query_st = time()
        # Binary search to find correct block
        left, right = 0, n // self.BLOCK_SIZE + 1
        while right - left > 1:
            mid = (left + right) // 2
            if n <= mid * self.BLOCK_SIZE:
                right = mid
            else:
                left = mid

        # Needed block number
        k = left
        current_block = [False for i in range(self.BLOCK_SIZE + 1)]

        # Going through pre-calculated primes
        for num in self.primes:
            start_idx = (k * self.BLOCK_SIZE + num - 1) // num
            # Filtering out composite numbers
            for j in range(max(start_idx, 2) * num - k * self.BLOCK_SIZE, self.BLOCK_SIZE + 1, num):
                current_block[j] = True

        # Special case for the first block
        if k == 0:
            current_block[0] = current_block[1] = True

        query_fin = time() - query_st
        log(f'Query calculated, time elapsed - {query_fin}s')
        # Since we found every composite number in the block, we just address the needed one
        return not current_block[n - k * self.BLOCK_SIZE]


# Initializing sieve
primer = Eratosthenes()


# gRPC handler class
class ServerHandler(pb2_grpc.ServerServicer):
    # Method for reversing a string
    def reverse(self, request, context):
        log(f'ReverseRequest, args - {request.message}')
        msg = request.message[::-1]
        return pb2.ReverseResponse(message=msg)

    # Method for splitting string by any delimiter
    def split(self, request, context):
        log(f'SplitRequest, args - {request.message, request.delim}')
        msg, delim = request.message, request.delim
        size, parts = len(msg.split(delim)), msg.split(delim)
        return pb2.SplitResponse(length=size, parts=parts)

    # Method for checking a stream of numbers on their primality
    def isprime(self, request_iterator, context):
        log(f'IsPrimeRequest')
        for num in request_iterator:
            reply = (f'{num.message} is ' + ('' if primer.is_prime(num.message) else 'not ') + 'prime')
            yield pb2.IsPrimeResponse(message=reply)


# Main method
def main():
    # Initializing gRPC server with 10 worker threads
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port(f'127.0.0.1:{port}')
    pb2_grpc.add_ServerServicer_to_server(ServerHandler(), server)
    server.start()
    # Waiting for keyboard interrupt
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print('Server terminated')


if __name__ == '__main__':
    main()
