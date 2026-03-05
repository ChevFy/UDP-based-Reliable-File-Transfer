# ============================================================
#  URFT – UDP-based Reliable File Transfer
# ============================================================

# ---------- default config ----------
SERVER_IP   ?= 192.168.1.155
SERVER_PORT ?= 8080
FILE        ?= test_1MiB.bin
# ------------------------------------

.PHONY: server client list help stop

help:
	@echo ""
	@echo "Usage:"
	@echo "  make server                         - Start URFT server"
	@echo "  make client                         - Send file to server  (default: $(FILE))"
	@echo "  make client FILE=test_1MiB.bin      - Send a specific file from client_file/"
	@echo "  make list                           - List available files in client_file/"
	@echo "  make stop                           - Stop running URFT server process"
	@echo ""
	@echo "Options:"
	@echo "  SERVER_IP   = $(SERVER_IP)"
	@echo "  SERVER_PORT = $(SERVER_PORT)"
	@echo "  FILE        = $(FILE)"
	@echo ""

server:
	python3 urft_server.py $(SERVER_IP) $(SERVER_PORT)

client:
	python3 urft_client.py client_file/$(FILE) $(SERVER_IP) $(SERVER_PORT)

list:
	@echo "Files in client_file/:"
	@ls -lh client_file/

stop:
	@pkill -f 'python3 urft_server.py' && echo "URFT server stopped." || echo "No running URFT server found."
