import sys , os
import socket
from pathlib import Path
from urft_utilities import *

BUFFER_SIZE = 4096

# Type 0 for handshake
# Type 1 for Send Packet
# Tpye 2 for ACK
# Type 3 for FIN


def handshakeConnection( seq :int , sock : socket.socket , addr_server):

    connect_result = False
    SYN_ACK_recv = False

    #send SYN
    
    SYN_packet = Packet(seq,0,None)
    if(SYN_packet) :
        return {"Error" : "Syn Packet failed to pack"} , connect_result
    
    print(f"SEND SEQ : {seq} , Type : 0 , Checksum : None , Payload : None")
    sock.sendto( SYN_packet.to_bytes() ,addr_server)

    count = 0

    if not SYN_ACK_recv :
        #wating for reciev syn-ack 
        while True :
            print("Waiting for SYN-ACK...")
            try :
                SYN_ACK_data , addr = sock.recvfrom(BUFFER_SIZE)
                SYN_ACK_recv_seq, SYN_ACK_recv_packet_type, SYN_ACK_recv_checksum, SYN_ACK_recv_payload = Packet.from_byte(SYN_ACK_data)
                print(f"Received SEQ : {SYN_ACK_recv_seq} , Type : {SYN_ACK_recv_packet_type} , Checksum : {SYN_ACK_recv_checksum} , Payload : {SYN_ACK_recv_payload} from {addr}")
                if(SYN_ACK_recv_packet_type == 2 and SYN_ACK_recv_seq == seq and hashlib.md5(SYN_ACK_recv_payload).digest() == SYN_ACK_recv_checksum) :
                    connect_result , SYN_ACK_recv = True, True
                    print("SYN-ACK received successfully")
                    break
                else :
                    if(count >= 3):
                            return { {"Error" : "Connetion Failed!!"} , connect_result}
                    count+=1
                    print("Error : Something isn't valid")
                    print("Resend... : SYN Packet")
                    sock.sendto( SYN_packet.to_bytes() ,addr_server)
            except socket.timeout :
                print("Timeout!!!")
                print("Resend... : SYN Packet")
                sock.sendto( SYN_packet.to_bytes() ,addr_server)

    return {"Success" : "Client Connection Success"} , connect_result , seq
 




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

    for _ in range(3):
        message_client , connection_result_client , seq = handshakeConnection(seq,sock,addr_server)
        print(message_client)
        if(connection_result_client):
            break

    
    
    
    

    
        

        
    

                    
                    
                   
                    
                    


                    
            



            


        
            



if __name__ == "__main__":
    main(sys.argv)
