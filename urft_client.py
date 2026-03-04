import sys
import socket
from pathlib import Path
from urft_utilities import *

BUFFER_SIZE = 1024

# Type 0 for handshake
# Type 1 for Send Packet
# Tpye 2 for Close


def main(arg):
    if len(arg) != 4:
        print("Error")
        sys.exit(0)

    file_path, server_ip, server_port = Path(arg[1]), str(arg[2]), int(arg[3])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    seq = 0

    # Handshake
    handshake = False
    isValid = True
    file_name = file_path.name
    packet_handshake = Packet(seq, 0, file_name.encode("utf-8"))
    sock.sendto(packet_handshake.to_bytes(), (server_ip, server_port))

    Ack = False
    while True:

        while not Ack:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                print("Timeout : resending handshake...")
                sock.sendto(packet_handshake.to_bytes(), (server_ip, server_port))
                continue
            recv_seq, recv_packet_type, recv_checksum, recv_payload = (Packet.from_byte(data))
            print(f"Received SEQ : {recv_seq} , Type : {recv_packet_type} , Checksum : {recv_checksum} , Payload : {recv_payload} from {addr}")
            if not handshake and recv_packet_type == 0 and seq == recv_seq  and  hashlib.md5(recv_payload).digest() == recv_checksum:
                seq += 1
                handshake = True
                Ack = True
                print(f"Handshake with {addr} Sucess")
            else:
                print("Error : Something isn't valid")
                sock.sendto(packet_handshake.to_bytes(), (server_ip, server_port))
                continue
                

        if Ack:
            break
            

        # try:
        #     with open(file_path, "rb") as file:
        #         file_raw_byte = file.read(BUFFER_SIZE)
        #         print(f"SEQ : {seq} , ", file_raw_byte)
        # except FileNotFoundError:
        #     print("File not fouud!!")
        #     sys.exit(0)

        # sock.sendto(file_raw_byte, (server_ip, server_port))

    sock.close()


if __name__ == "__main__":
    main(sys.argv)
