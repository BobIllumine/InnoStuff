import socket
import sys
import time

# List of numbers
numbers = [15492781, 15492787, 15492803,
           15492811, 15492810, 15492833,
           15492859, 15502547, 15520301,
           15527509, 15522343, 1550784]

try:
    # Guaranteed that connection will be closed
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        # Server info
        server_addr = sys.argv[1].split(":")
        server_ip = server_addr[0]
        server_port = int(server_addr[1])

        print(f'Connecting to {server_ip}:{server_port}...')
        client.connect((server_ip, server_port))
        print(f'Connected!')
        # Requests
        for number in numbers:
            # Checking if numbers in the list are integers
            if isinstance(number, int):
                client.send(f'{number}'.encode())
                client.settimeout(3)
                data = client.recv(2048)
                print(data.decode())
            else:
                print('Incorrect value in the list of requests')
                continue
        # Sending the signal telling the server about the end of transmission
        client.send('Q'.encode())
# Handling connection errors
except ConnectionError as err:
    print(f'Oops! Lost connection to server, {err}')
