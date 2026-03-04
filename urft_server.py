
import sys
import socket

BUFFER_SIZE = 1024

def main(arg):

    if(len(arg) != 3):
        print("Error")
        sys.exit(0)

    server_ip , server_port = str(arg[1]) , int(arg[2])
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((server_ip,server_port))
    print(f"Listening for UDP packets on {server_ip}:{server_port}")
    while(True):
        data, addr = sock.recvfrom(BUFFER_SIZE)
        print(f"Received message: {data} from {addr}")
        with open("example.bin", "wb") as file:
            file.write(data)
        
        
        



if __name__ == "__main__":
    main(sys.argv)

