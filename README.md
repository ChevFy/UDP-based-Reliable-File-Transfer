# Socket Programing Project - Computer Network [CE-KMITL]
### UDP-based Reliable File Transfer 
Reliable file transfer over UDP with packet loss and duplication handling.


## Usage

**Server:**
```bash
python urft_server.py <server_ip> <server_port>
```

**Client:**
```bash
python urft_client.py <file_path> <server_ip> <server_port>
```

## Example
```bash
# Terminal 1
python urft_server.py 127.0.0.1 5000

# Terminal 2
python urft_client.py test.bin 127.0.0.1 5000
```

## Features
- Binary file support
- Handles packet loss & duplication
- Cross-subnet communication
- Automatic file naming
