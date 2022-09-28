import os
import socket
import sys
import time

# Default buffer size
buffer_size = 1024

# Instead of 127.0.0.1 we can use this approach
local_addr = socket.gethostbyname(socket.gethostname())
local_port = int(sys.argv[1])

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

s.bind((local_addr, local_port))

print(f'address: {socket.gethostbyname(socket.gethostname())}, port: {local_port}')

# Metaata will be stored here
meta = ''

# Waiting for correct metadata
while len(meta) != 4:
    meta, addr = s.recvfrom(buffer_size)
    meta = meta.decode().split(" | ")

    print(f'message #{meta[1]}: metadata received, file name - {meta[2]}, file size - {meta[3]}')

    s.sendto(f'a | {meta[1]} | {buffer_size}'.encode(), addr)

# Parsing data
next_seqno = int(meta[1]) + 1
file_name = meta[2]
file_size = int(meta[3])
data = bytearray()

with open(file_name, "wb") as file:
    try:
        while len(data) != file_size:
            s.settimeout(3)
            packet, addr = s.recvfrom(buffer_size)
            packet = packet.split(" | ".encode(), maxsplit=2)
            resp = f'a | '.encode() + packet[1]
            s.sendto(resp, addr)

            # Checking if the packet arrived matches with the expected one
            if int(packet[1]) == next_seqno:
                data += packet[2]
                next_seqno += 1

                print(f'packet #{packet[1].decode()}: data chunk with length {len(packet[2])} received, waiting for seq#{next_seqno}')

        print('transmission is completed successfully, closing the connection...')
        # Waiting for 1 second
        time.sleep(1)
        file.write(data)

    except TimeoutError:
        print('client timed out, ending the transfer')
        file.close()
        os.remove(file_name)
        exit(2)

