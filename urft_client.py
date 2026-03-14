import sys , os
import socket
from pathlib import Path
from urft_utilities import *

BUFFER_SIZE = 4096

# Type 0 for handshake
# Type 1 for Send Packet
# Tpye 2 for ACK
# Type 3 for FIN
# Type 4 for SACK


BUFFER_PACKET = []

def ADD_BUFFER_PACKET( current_seq : int ,current_packet : Packet):
    if(current_seq == current_packet.seq):
        for p in BUFFER_PACKET:
            if p.seq == current_seq:
                return False
        BUFFER_PACKET.append(current_packet)
        return True
    return False


def handshakeConnectionClient( seq :int , sock : socket.socket , addr_server):

    connect_result = False
    SYN_ACK_recv = False

    #send SYN
    SYN_packet = Packet(seq,0,None)
    if(not SYN_packet) :
        return {"Error" : "Syn Packet failed to pack"} , connect_result , seq
    
    print(f"SEND SEQ : {seq} , Type : 0 , Checksum : None , Payload : None")
    sock.sendto( SYN_packet.to_bytes() ,addr_server)

    count = 0

    if not SYN_ACK_recv :
        #wating for reciev syn-ack 
        while True :
            print("Waiting for SYN-ACK...")
            count+=1
            if(count >= 3):
                return {"Error" : "Connection Failed!!"} , connect_result , seq
            try :
                SYN_ACK_data , addr = sock.recvfrom(BUFFER_SIZE)
                SYN_ACK_recv_seq, SYN_ACK_recv_packet_type, SYN_ACK_recv_checksum, SYN_ACK_recv_payload = Packet.from_byte(SYN_ACK_data)
                print(f"Received SEQ : {SYN_ACK_recv_seq} , Type : {SYN_ACK_recv_packet_type} , Checksum : {SYN_ACK_recv_checksum} , Payload : {SYN_ACK_recv_payload} from {addr}")
                if(SYN_ACK_recv_packet_type == 2 and SYN_ACK_recv_seq == seq and hashlib.md5(SYN_ACK_recv_payload).digest() == SYN_ACK_recv_checksum) :
                    connect_result , SYN_ACK_recv = True, True
                    print("SYN-ACK received successfully")
                    # ACK for handshake should be Type 2 (ACK)
                    ACK_packet = Packet(seq,2,None)
                    if(not ACK_packet) :
                        return {"Error" : "ACK Packet failed to pack"} , connect_result , seq
                    print(f"SEND SEQ : {seq} , Type : 2 , Checksum : None , Payload : None")
                    sock.sendto( ACK_packet.to_bytes() ,addr_server)
                    seq += 1
                    break
                else :
                    print("Error : Something isn't valid")
                    print("Resend... : SYN Packet")
                    sock.sendto( SYN_packet.to_bytes() ,addr_server)
            except socket.timeout :
                print("Timeout!!!")
                print("Resend... : SYN Packet")
                sock.sendto( SYN_packet.to_bytes() ,addr_server)

    return {"Success" : "Client Connection Success"} , connect_result , seq
 
def sendPacket( payload : str , type : int,current_seq : int , sock : socket.socket , addr_server):
    send_data_result = False
    data_packet = Packet(current_seq, type , payload)
    if not data_packet :
       return {"Error" : "Packet failed to pack!"} , send_data_result , current_seq
    if(type == 1):
        ADD_BUFFER_PACKET(current_seq,data_packet)
        print(f"ADD packet to buffer, SEQ : {current_seq} , Type : Data")
    sock.sendto(data_packet.to_bytes(),addr_server)
    print(f"Sending Data Packet..., SEQ : {current_seq} , Type : {type}")
    current_seq+=1
    return {"Success" : "Packet has been sent"} , send_data_result , current_seq


def main(arg):
    if len(arg) != 4:
        print("Error")
        sys.exit(0)

    file_path, server_ip, server_port = Path(arg[1]), str(arg[2]), int(arg[3])
    file_name = file_path.name
    file_size = os.path.getsize(file_path)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    seq = 0
    addr_server = (server_ip, server_port)

    # Try to connet server 3 times
    connection_result_client = False
    for _ in range(3):

        message_client , connection_result_client , seq = handshakeConnectionClient(seq,sock,addr_server)
        print(message_client)
        if(connection_result_client):
            break
    if not connection_result_client :
        print("Connection failed")
        sys.exit(0)
    
    # Send data first time (file_name)
    message_client , send_filename_result , seq = sendPacket(file_name.encode("utf-8"),1,seq,sock,addr_server)
    if not send_filename_result :
        print("Error : Filename failed to sent")
    
    with open(file_path, "rb") as file :
        offset = 0
        payload_size = BUFFER_SIZE - Packet.header_size()
        while True :
            file.seek(offset)
            buffer_read = file.read(payload_size)
            if not buffer_read :
                message_client , send_data_result, seq = sendPacket(None,3,seq,sock,addr_server)
                print("send FIN packet" , {seq-1})
                break

            message_client , send_data_result, seq = sendPacket(buffer_read,1,seq,sock,addr_server)
            offset += len(buffer_read)
    
    ## Check ACK for FIN
    fin_seq = seq - 1 
    print("fin_seq" , fin_seq)
    fin_packet = Packet(fin_seq, 3, None)
    while True :
        try :
            data , addr = sock.recvfrom(BUFFER_SIZE)
            recv_seq, recv_packet_type, recv_checksum, recv_payload = Packet.from_byte(data)
            print(f"recv seq : {recv_seq} , type : {recv_packet_type} , Checksum : {recv_checksum} , Payload : {recv_payload} from {addr}")
            if(recv_packet_type == 2 and recv_seq == fin_seq and hashlib.md5(recv_payload).digest() == recv_checksum) :
                print("ACK for FIN recv successfully")
                break
            else:
                print("Ignoring non-ACK packet while waiting for FIN ACK")
        except socket.timeout :
            print("Timeout!!!")
            print("Resend... : FIN Packet")
            sock.sendto(fin_packet.to_bytes(), addr_server)

    ## SACK : Missiong packet
    server_fin_ackd = False
    while True :
        try :
            data , addr = sock.recvfrom(BUFFER_SIZE)
            recv_seq, recv_packet_type, recv_checksum, recv_payload = Packet.from_byte(data)
            print(f"Received SEQ : {recv_seq} , Type : {recv_packet_type} , Checksum : {recv_checksum} , Payload : {recv_payload} from {addr}")
            # FIN from server: don't enforce checksum for this control packet.
            if(recv_packet_type == 3):
                print("FIN received from server")
                fin_ack = Packet(recv_seq, 2, None)
                sock.sendto(fin_ack.to_bytes(), addr_server)
                server_fin_ackd = True
                print("----tranfer----")
                break
            # SACK from server: accept even if checksum differs so we can recover missing data.
            if(recv_packet_type == 4):
                print("SACK received successfully")
                missing_seqs = []
                for i in range(0, len(recv_payload), 4):
                    missing_seqs.append(int.from_bytes(recv_payload[i:i+4], byteorder='big'))
                print(f"Missing seqs from server: {missing_seqs}")
                for missing_seq in missing_seqs:
                    for packet in BUFFER_PACKET:
                        if packet.seq == missing_seq:
                            sock.sendto(packet.to_bytes(), addr_server)
                            print(f"Resent packet with seq : {missing_seq}")
                            break
        except socket.timeout :
            print("Timeout!!! Waiting for SACK...")

    print("completed successfully!")
    sock.close()
    sys.exit(0)
    

if __name__ == "__main__":
    main(sys.argv)
