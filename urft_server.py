import sys
import socket
from pathlib import Path
from urft_utilities import *


# Type 0 for handshake
# Type 1 for Send Packet
# Tpye 2 for ACK
# Type 3 for FIN
# Type 4 for SACK


BUFFER_SIZE = 4096

BUFFER_PACKET = []

def CLEAR_BUFFER_PACKET():
    BUFFER_PACKET.clear()

def ADD_BUFFER_PACKET( current_seq : int ,current_packet : Packet):
    if(current_seq == current_packet.seq):
        for p in BUFFER_PACKET:
            if p.seq == current_seq:
                return False
        BUFFER_PACKET.append(current_packet)
        return True
    return False

def handshakeConnectionServer( sock : socket.socket):
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
        socket.timeout(3)
        while True :
            # waiting for
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
    current_addr = None
    server_ip, server_port = str(arg[1]), int(arg[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, server_port))
    print(f"Listening for UDP packets on {server_ip}:{server_port}")

    ## Handshake
    connection_result_server = False
    while not connection_result_server:
        message_server , connection_result_server , seq , current_addr = handshakeConnectionServer(sock)
        print(message_server)
        if(connection_result_server):
            print(f"Connection established with client at {current_addr}")
            connection_result_server = True
            break
        else :
            print("Connection failed")
    
    ## wating recv packet
    while True :
        data , addr = sock.recvfrom(BUFFER_SIZE)
        if (current_addr != addr ):
            print(f"{addr} , {current_addr} isn't match")
            return main(arg)
        recv_seq, recv_packet_type, recv_checksum, recv_payload = (Packet.from_byte(data))
        if recv_checksum != hashlib.md5(recv_payload).digest():
            print("Checksum mismatch, ignoring packet")
            continue
        if(recv_packet_type == 1):
            current_recv_packet = Packet(recv_seq,recv_packet_type,recv_payload)
            ADD_BUFFER_PACKET(recv_seq,current_recv_packet)
            print("Data packet received and added to buffer" + " --> "+ f"SEQ : {recv_seq}")
        
        if(recv_packet_type == 3):
            print("FIN packet received")
            # send ACK for FIN
            ack_packet = Packet(recv_seq, 2, None)
            sock.sendto(ack_packet.to_bytes(), addr)
            print(f"SEND SEQ : {recv_seq} , Type : 2 , Checksum : None , Payload : None to {addr}")
            break

    BUFFER_PACKET.sort(key=lambda x: x.seq)
    ##Check buffer 
    if len(BUFFER_PACKET) > 0 :
            # find all missing seq 
            missing_seqs = []
            before_seq = BUFFER_PACKET[0].seq
            for packet in BUFFER_PACKET:
                while packet.seq > before_seq :
                    missing_seqs.append(before_seq)
                    before_seq += 1
                if packet.seq == before_seq:
                    before_seq += 1

            for missing in missing_seqs:
                socket.timeout(0.5)
                print(f"Packet seq {missing} is missing!!")
                sock.sendto(Packet(seq, 4, missing.to_bytes(4, byteorder='big')).to_bytes(), addr)
                while True :
                    try :
                        data , addr = sock.recvfrom(BUFFER_SIZE)
                        recv_seq, recv_packet_type, recv_checksum, recv_payload = (Packet.from_byte(data))
                        if recv_checksum != hashlib.md5(recv_payload).digest():
                            print("Checksum mismatch")
                            continue
                        if(recv_packet_type == 1 and recv_seq == missing):
                            current_recv_packet = Packet(recv_seq,recv_packet_type,recv_payload)
                            if ADD_BUFFER_PACKET(recv_seq,current_recv_packet) :
                                print("miss packet recev and added to buffer" + " --> "+ f"SEQ : {recv_seq}")
                            else :
                                print("recv packet is already in buffer, ignoring it...")
                            break
                        else :
                            print("Received packet is not the missing packet, ignoring it...")
                    except socket.timeout :
                        print("timeout for waiting miss packet!! resending SACK...")
                        sock.sendto(Packet(seq, 4, missing.to_bytes(4, byteorder='big')).to_bytes(), addr)

    else :
        print("No packets in buffer, waiting for new packets...")
        CLEAR_BUFFER_PACKET()
        return main(arg)
    
    BUFFER_PACKET.sort(key=lambda x: x.seq)
    # print(BUFFER_PACKET)

    #sent FIN-ACK
    fin_ack_packet = Packet(seq, 3, None)
    sock.sendto(fin_ack_packet.to_bytes(), addr)
    print(f"SEND SEQ : {seq} , Type : 3 , Checksum : None , Payload : None to {addr}")
    
        
    #write file
    recv_seq, recv_packet_type, recv_checksum, recv_payload = (Packet.from_byte(BUFFER_PACKET[0].to_bytes()))
    file_name = recv_payload.decode()
    file_path = Path(file_name)
    with open(file_path, 'wb') as file:
        for packet in BUFFER_PACKET[1:]:
            file.write(packet.payload)
    print(f"File '{file_name}' has been written successfully")
        
    
    #reset buffer
    CLEAR_BUFFER_PACKET()
    print("Buffer cleared, ready for new connections")
    

if __name__ == "__main__":
    main(sys.argv)
