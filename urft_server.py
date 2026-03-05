import sys
import socket
from pathlib import Path
from urft_utilities import *

BUFFER_SIZE = 1024


def main(arg):

    if len(arg) != 3:
        print("Error")
        sys.exit(0)

    server_ip, server_port = str(arg[1]), int(arg[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, server_port))
    print(f"Listening for UDP packets on {server_ip}:{server_port}")

    handshake = False
    syn_ack = False
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        recv_seq, recv_packet_type, recv_checksum, recv_payload = Packet.from_byte(data)
        print(
            f"Received SEQ : {recv_seq} , Type : {recv_packet_type} , Checksum : {recv_checksum} , Payload : {recv_payload} from {addr}"
        )

        # Three way handshake
        if not handshake and not syn_ack:
            if (
                recv_packet_type == 0
                and recv_checksum == hashlib.md5(recv_payload).digest()
            ):
                handshake = True
                ack_packet = Packet(recv_seq, 2, None)
                sock.sendto(ack_packet.to_bytes(), addr)
                print(
                    f"SEND SEQ : {recv_seq} , Type : 2 , Checksum : None , Payload : None to {addr}"
                )

        if not syn_ack:
            if (
                recv_packet_type == 1
                and recv_checksum == hashlib.md5(recv_payload).digest()
            ):
                with open( "server_file/" + recv_payload.decode("utf-8"), "w") as file:
                    ack_packet = Packet(recv_seq, 2, None)

                    sock.sendto(ack_packet.to_bytes(), addr)
                    print(
                        f"SEND SEQ : {recv_seq} , Type : 2 , Checksum : None , Payload : None to {addr}"
                    )
                    syn_ack = True
                    print(f"----Handshake with {addr} Sucess----")
                    continue


if __name__ == "__main__":
    main(sys.argv)
