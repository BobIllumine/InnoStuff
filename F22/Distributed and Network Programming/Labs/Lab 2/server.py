import signal
import socket
import sys
from multiprocessing import Queue
import threading

local_port = int(sys.argv[1])
connection_queue = Queue()
# Flag for stopping the server
running = True


# Function for checking numbers
def is_prime(n: int) -> bool:
    i = 2
    # Going for square root is faster
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


# Worker thread
def serve():
    # While flag is active, the thread is running
    while running:
        entry = connection_queue.get()
        # Condition for termination of the program
        if entry is None:
            connection_queue.put(None)
            return

        else:
            sock_conn, sock_addr = entry
            # Guaranteed that connection will close
            with sock_conn:
                print(f'Connected to {sock_addr}')
                while True:
                    # Timeouts are needed in order to prevent blocking
                    sock_conn.settimeout(.5)
                    try:
                        data = sock_conn.recv(2048).decode()
                    except socket.timeout:
                        continue
                    print(f'[{sock_addr[0]}:{sock_addr[1]}]: {data}')
                    # Signal from client that the transmission is finished
                    if data.lower() == 'q':
                        print('Completed')
                        break
                    # Incorrect value
                    elif not data.isdigit():
                        sock_conn.send('Received value is not a positive integer number'.encode())
                    else:
                        sock_conn.send((f'{data} is ' + ('prime' if is_prime(int(data)) else 'not prime')).encode())


# Handler for keyboard interrupt
def exit_handler(sig, frame):
    print('Process terminated, closing all connections')
    global running
    running = False
    # Putting None to queue in order to terminate all threads
    connection_queue.put(None)


# Main function
def main():
    # Announcing the interrupt handler
    signal.signal(signal.SIGINT, exit_handler)
    # Guaranteed that connection will be closed
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(('127.0.0.1', local_port))
        print(f'Server is set on {server.getsockname()}')
        # Making threads and starting them
        threads = [threading.Thread(target=serve, name=f'thread#{i}') for i in range(64)]
        for t in threads:
            t.start()
        # While flag is active, the server is running
        while running:
            server.listen()
            # Setting timeout to prevent blocking
            server.settimeout(.5)
            try:
                conn, addr = server.accept()
                connection_queue.put((conn, addr))
            except socket.timeout:
                continue


if __name__ == "__main__":
    main()
