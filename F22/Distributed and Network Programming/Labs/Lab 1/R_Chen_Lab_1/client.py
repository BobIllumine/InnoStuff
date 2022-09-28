# Created by R. Chen
# BS20-AI
import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((socket.gethostname(), 0))

# Command line arguments
port, file_path, file_name = int(sys.argv[1]), sys.argv[2], sys.argv[3]

print(f"port: {port}, path: {file_path}, name: {file_name}")

# seqno_0 and default server buffer size
next_seqno = 0
server_buffer_size = 1024

# Doing this will close the file automatically after transmission
with open(file_path, "rb") as file:
    data = file.read()
    resp = ''

    # Retries count, refreshes every successful acknowledgement
    retries = 0
    # Re-sending start message until we get an acknowledgement and buffer size
    while len(resp) != 3:
        try:
            print(f'sending message #{next_seqno}: file name - {file_name}, file size - {len(data)}')

            msg = f's | {next_seqno} | {file_name} | {len(data)}'
            s.sendto(msg.encode(), (socket.gethostname(), port))

            s.settimeout(0.5)
            resp, addr = s.recvfrom(1024)

        except TimeoutError:
            if retries < 5:
                print(f'no ack response received, retry #{retries + 1}...')
                retries += 1
                continue
            else:
                print('server timed out, closing the connection')
                file.close()
                exit(2)

        resp = resp.decode().split(" | ")
        retries = 0

    # Parsing ack message data
    next_seqno = int(resp[1]) + 1
    server_buffer_size = int(resp[2])
    # We need to take an overhead in each message (prefix and seqno) into account
    # seqno is increasing with file size, so it is better to have a bit more room for it
    chunk_size = server_buffer_size - 256
    # Slice pointer, we will move it with every successful packet delivery
    slice_pos = 0

    retries = 0
    while slice_pos < len(data):
        # Calculating right boundary of a slice
        next_slice_pos = (slice_pos + chunk_size
                          if slice_pos + chunk_size <= len(data)
                          else slice_pos + (len(data) % chunk_size))
        try:
            print(f'sending packet #{next_seqno}: slice [{slice_pos}..{next_slice_pos}]')

            msg = f'd | {next_seqno} | '.encode() + data[slice_pos : next_slice_pos]
            s.sendto(msg, (socket.gethostname(), port))

            s.settimeout(0.5)
            resp, addr = s.recvfrom(1024)

        except TimeoutError:
            if retries < 5:
                print(f'no ack response received, retry #{retries + 1}...')
                retries += 1
                continue
            else:
                print('server timed out, closing the connection')
                file.close()
                exit(2)

        retries = 0
        resp = resp.decode().split(" | ")

        next_seqno = int(resp[1]) + 1
        # We can calculate next position for slice pointer as if it is in arithmetic progression
        slice_pos = chunk_size * (next_seqno - 1)


