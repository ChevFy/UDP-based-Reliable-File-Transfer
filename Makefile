# ============================================================
#  URFT – UDP-based Reliable File Transfer
# ============================================================

# ---------- default config ----------
SERVER_IP   ?= 127.0.0.1
SERVER_PORT ?= 12345
FILE        ?= test.txt
# ------------------------------------

.PHONY: server client list help

help:
	@echo ""
	@echo "Usage:"
	@echo "  make server                         - Start URFT server"
	@echo "  make client                         - Send file to server  (default: $(FILE))"
	@echo "  make client FILE=test_1MiB.bin      - Send a specific file from client_file/"
	@echo "  make list                           - List available files in client_file/"
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
