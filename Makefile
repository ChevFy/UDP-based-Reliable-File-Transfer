SERVER_IP   ?= 192.168.1.173
SERVER_PORT ?= 8080
FILE        ?= FFFFF.pdf

.PHONY: server client list help stop

server:
	python3 urft_server.py $(SERVER_IP) $(SERVER_PORT)

client:
	python3 urft_client.py $(FILE) $(SERVER_IP) $(SERVER_PORT)
