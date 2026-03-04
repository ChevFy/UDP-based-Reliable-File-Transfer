import sys
import socket
from pathlib import Path

def main(arg):
    if(len(arg) != 4):
        print("Error")
        sys.exit(0)
    
    file_path , server_ip , server_port =  Path(arg[1]) ,str(arg[2]) , int(arg[3])
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try :
        with open(file_path, 'rb')  as file:
            file_raw_byte = file.read()
            print(file_raw_byte)
    
    except FileNotFoundError :
        print("File not fouud!!")
        sys.exit(0)

    sock.sendto(file_raw_byte,(server_ip,server_port))
    sock.close()


if __name__ == "__main__":
    main(sys.argv)

