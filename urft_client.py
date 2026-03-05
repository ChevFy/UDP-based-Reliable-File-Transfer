import sys
import socket
from pathlib import Path
from urft_utilities import *

BUFFER_SIZE = 1024

# Type 0 for handshake
# Type 1 for Send Packet
# Tpye 2 for ACK


def main(arg):
    if len(arg) != 4:
        print("Error")
        sys.exit(0)

    file_path, server_ip, server_port = Path(arg[1]), str(arg[2]), int(arg[3])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    seq = 0
    addr_server = (server_ip, server_port)

    handshake = False

    Ack = False
    while True:

        # Three way handshake
        if not handshake:
            print("---------- Handshake Started ----------")
            syn_packet = Packet(seq, 0, None)
            if syn_packet is None:
                print("syn_packet has been failed")
                return

            sock.sendto(syn_packet.to_bytes(), addr_server)
            print(
                f"SEND SEQ : {seq} , Type : 0 , Checksum : None , Payload : None to {addr_server}"
            )
            while not Ack:
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    print("Timeout : resending handshake...")
                    sock.sendto(syn_packet.to_bytes(), addr_server)
                    print(
                        f"SEND SEQ : {seq} , Type : 0 , Checksum : None , Payload : None to {addr_server}"
                    )
                    continue
                recv_seq, recv_packet_type, recv_checksum, recv_payload = (
                    Packet.from_byte(data)
                )

                print(
                    f"Received SEQ : {recv_seq} , Type : {recv_packet_type} , Checksum : {recv_checksum} , Payload : {recv_payload} from {addr}"
                )
                if (
                    recv_packet_type == 2
                    and seq == recv_seq
                    and hashlib.md5(recv_payload).digest() == recv_checksum
                ):
                    seq += 1
                    handshake = True
                    Ack = True
                    print(f"----Handshake with {addr_server} Success----")
                else:
                    print("Error : Something isn't valid")
                    sock.sendto(syn_packet.to_bytes(), (server_ip, server_port))
                    print(
                        f"SEND SEQ : {seq} , Type : 0 , Checksum : None , Payload : None to {addr_server}"
                    )
                    continue

            file_name = file_path.name
            packet_ack = Packet(seq, 1, file_name.encode("utf-8"))
            sock.sendto(packet_ack.to_bytes(), addr_server)
            print(
                f"SEND SEQ : {seq} , Type : 1 , Checksum : None , Payload : {file_name.encode('utf-8')} to {addr_server}"
            )

        if Ack:
            break

    sock.close()


if __name__ == "__main__":
    main(sys.argv)
