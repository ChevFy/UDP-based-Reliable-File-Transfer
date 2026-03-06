import sys
import socket
from pathlib import Path
from urft_utilities import *

BUFFER_SIZE = 4096

def handshakeConnection( sock : socket.socket):
    connection_result =  False

    #waiting recv SYN
    while not connection_result :
        print("Waiting for Connection...")
        SYN_data, addr = sock.recvfrom(BUFFER_SIZE)
        SYN_recv_seq, SYN_recv_packet_type, SYN_recv_checksum, SYN_recv_payload = (Packet.from_byte(SYN_data))
        print(
            f"Received SEQ : {SYN_recv_seq} , Type : {SYN_recv_packet_type} , Checksum : {SYN_recv_checksum} , Payload : {SYN_recv_payload} from {addr}"
        )
        if (SYN_recv_packet_type == 0 and SYN_recv_checksum == hashlib.md5(SYN_recv_payload).digest()):
            ## send SYN-ACK
            ack_packet = Packet(SYN_recv_seq, 2, None)
            if(not ack_packet) :
                print("Error: Failed to create ACK packet")
                continue
            sock.sendto(ack_packet.to_bytes(), addr)
            print(
                f"SEND SEQ : {SYN_recv_seq} , Type : 2 , Checksum : None , Payload : None to {addr}"
            )
        sock.settimeout(0.5)
        while True :
            try :
                ACK_data, addr = sock.recvfrom(BUFFER_SIZE)
                ACK_recv_seq, ACK_recv_packet_type, ACK_recv_checksum, ACK_recv_payload = (Packet.from_byte(ACK_data))
                print(
                    f"Received SEQ : {ACK_recv_seq} , Type : {ACK_recv_packet_type} , Checksum : {ACK_recv_checksum} , Payload : {ACK_recv_payload} from {addr}"
                )
                if (ACK_recv_packet_type == 1 and ACK_recv_seq == SYN_recv_seq and ACK_recv_checksum == hashlib.md5(ACK_recv_payload).digest()):
                    connection_result = True
                    print("Connection established successfully")
                    return {"Success" : "Server Connection Success"} , connection_result , SYN_recv_seq , addr
                else :
                    print("Error: Invalid ACK received")
            except socket.timeout :
                print("Timeout waiting for ACK, resending SYN-ACK...")
                sock.sendto(ack_packet.to_bytes(), addr)
            
        
        


        
    


def main(arg):

    if len(arg) != 3:
        print("Error")
        sys.exit(0)

    server_ip, server_port = str(arg[1]), int(arg[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, server_port))
    print(f"Listening for UDP packets on {server_ip}:{server_port}")
    sock.settimeout(0.5)

    message_server , connection_result_server , seq , addr = handshakeConnection(sock)
    print(message_server)
    if(connection_result_server):
        print(f"Connection established with client at {addr}")
    else :
        print("Connection failed")
        return 


if __name__ == "__main__":
    main(sys.argv)
