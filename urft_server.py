import sys
import socket
from pathlib import Path
from urft_utilities import *

BUFFER_SIZE = 4096


def main(arg):

    if len(arg) != 3:
        print("Error")
        sys.exit(0)

    server_ip, server_port = str(arg[1]), int(arg[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, server_port))
    print(f"Listening for UDP packets on {server_ip}:{server_port}")

    handshake = False
    recv_syn = False
    while True:

        # Three way handshake
        if not handshake:

            while not recv_syn:
                # recieve SYN
                data, addr = sock.recvfrom(BUFFER_SIZE)
                recv_seq, recv_packet_type, recv_checksum, recv_payload = (
                    Packet.from_byte(data)
                )
                print(
                    f"Received SEQ : {recv_seq} , Type : {recv_packet_type} , Checksum : {recv_checksum} , Payload : {recv_payload} from {addr}"
                )
                if (
                    recv_packet_type == 0
                    and recv_checksum == hashlib.md5(recv_payload).digest()
                ):
                    ## send SYN-ACK
                    ack_packet = Packet(recv_seq, 2, None)
                    sock.sendto(ack_packet.to_bytes(), addr)
                    print(
                        f"SEND SEQ : {recv_seq} , Type : 2 , Checksum : None , Payload : None to {addr}"
                    )
                    recv_syn = True

        # Receive ACK with filename (type 1)
        if recv_syn and not handshake:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            recv_seq, recv_packet_type, recv_checksum, recv_payload = Packet.from_byte(
                data
            )
            print(
                f"Received SEQ : {recv_seq} , Type : {recv_packet_type} , Checksum : {recv_checksum} , Payload : {recv_payload} from {addr}"
            )
            if (
                recv_packet_type == 1
                and recv_checksum == hashlib.md5(recv_payload).digest()
            ):
                file_name = recv_payload.decode("utf-8")
                ack_packet = Packet(recv_seq, 2, None)
                sock.sendto(ack_packet.to_bytes(), addr)
                print(
                    f"SEND SEQ : {recv_seq} , Type : 2 , Checksum : None , Payload : None to {addr}"
                )
                handshake = True
                print(f"----Handshake with {addr} Success----")

        # Receive file data
        if handshake:
            with open("server_file/" + file_name, "wb") as file:
                while True:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    recv_seq, recv_packet_type, recv_checksum, recv_payload = (
                        Packet.from_byte(data)
                    )
                    print(
                        f"Received SEQ : {recv_seq} , Type : {recv_packet_type} , Checksum : {recv_checksum} , Payload : {len(recv_payload)} bytes from {addr}"
                    )

                    if recv_checksum != hashlib.md5(recv_payload).digest():
                        print("Checksum mismatch, ignoring packet")
                        continue

                    file.write(recv_payload)

                    # Send ACK
                    ack_packet = Packet(recv_seq, 2, None)
                    sock.sendto(ack_packet.to_bytes(), addr)
                    print(
                        f"SEND SEQ : {recv_seq} , Type : 2 , Checksum : None , Payload : None to {addr}"
                    )

                    # FIN
                    if recv_packet_type == 3:
                        print("-----RECEIVE FILE SUCCESS-----")
                        break

            # Reset
            handshake = False
            recv_syn = False
            print("Ready for next connection...")


if __name__ == "__main__":
    main(sys.argv)
