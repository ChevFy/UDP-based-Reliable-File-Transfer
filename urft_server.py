import sys
import socket
from pathlib import Path
from urft_utilities import *
import time


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
    sock.settimeout(None)  # Reset timeout for blocking wait on new connections

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
        sock.settimeout(3)
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
            
server_state = False
sock = None

def main(arg):

    if len(arg) != 3:
        print("Error")
        sys.exit(0)
    global server_state, sock
    if( not server_state) :
        server_state = True
        current_addr = None
        server_ip, server_port = str(arg[1]), int(arg[2])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((server_ip, server_port))
        print(f"Listening for UDP packets on {server_ip}:{server_port}")

    data_length_packet = 0
    
    while True:

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
            break

      if not connection_result_server:
          continue

      start_time = time.time()
      ## wating recv packet
      while True :
        data , addr = sock.recvfrom(BUFFER_SIZE)
        if (current_addr != addr ):
            print(f"{addr} , {current_addr} isn't match")
            continue
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
            data_length_packet = recv_seq
            print( "FIN from Client: ", recv_seq)
            break

      BUFFER_PACKET.sort(key=lambda x: x.seq)
      ##Check buffer 
      if len(BUFFER_PACKET) > 0 :
              # find all missing seq 
              buffet_packet_completely = False
              while not buffet_packet_completely :
                received_seqs = {packet.seq for packet in BUFFER_PACKET}
                missing_seqs = [i for i in range(1, data_length_packet) if i not in received_seqs]
                print(f"Missing seq : {missing_seqs}")

                if not missing_seqs:
                    buffet_packet_completely = True
                    break

                #SEND SACK with all missing seqs
                missing_payload = b''.join(m.to_bytes(4, byteorder='big') for m in missing_seqs)
                sock.sendto(Packet(seq, 4, missing_payload).to_bytes(), addr)
                print(f"Sent SACK with missing seqs: {missing_seqs}")

                missing_set = set(missing_seqs)
                sock.settimeout(0.5)
                while missing_set:
                    try:
                        data, addr = sock.recvfrom(BUFFER_SIZE)
                        recv_seq, recv_packet_type, recv_checksum, recv_payload = Packet.from_byte(data)
                        if recv_checksum != hashlib.md5(recv_payload).digest():
                            print("Checksum mismatch")
                            continue
                        if recv_packet_type == 1 and recv_seq in missing_set:
                            current_recv_packet = Packet(recv_seq, recv_packet_type, recv_payload)
                            if ADD_BUFFER_PACKET(recv_seq, current_recv_packet):
                                missing_set.discard(recv_seq)
                                print(f"Missing packet received and added to buffer --> SEQ : {recv_seq}")
                            else:
                                print("recv packet is already in buffer, ignoring it...")
                        else:
                            print(f"Unexpected packet SEQ: {recv_seq}, Type: {recv_packet_type}")
                    except socket.timeout:
                        print(f"Timeout! Resending SACK for remaining missing seqs: {sorted(missing_set)}")
                        break

      else :
          print("No packets in buffer, waiting for new packets...")
          CLEAR_BUFFER_PACKET()
          continue
      
      BUFFER_PACKET.sort(key=lambda x: x.seq)

      #sent FIN-ACK
      fin_ack_packet = Packet(seq, 3, None)
      sock.sendto(fin_ack_packet.to_bytes(), addr)
      print(f"SEND SEQ : {seq} , Type : 3 , Checksum : None , Payload : None to {addr}")
      
      #write file
      file_name = BUFFER_PACKET[0].payload.decode()
      if not file_name:
          print("Error : Filename is empty")
          CLEAR_BUFFER_PACKET()
          continue

      file_path = Path(file_name)
      with open(file_path, 'wb') as file:
          for packet in BUFFER_PACKET[1:]:
              file.write(packet.payload)
      print(f"File '{file_name}' has been written successfully")
      
      #reset buffer
      CLEAR_BUFFER_PACKET()
      print("Buffer cleared, ready for new connections")
      end_time = time.time()
      print(f"TIME : {end_time - start_time} second")
      print("------------------------------")
      sock.settimeout(None)  # Reset before next handshake
      sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
