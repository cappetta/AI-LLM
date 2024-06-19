import socket
import os
from datetime import datetime

def start_listener(host='0.0.0.0', port=9999, storage_dir='./received_zips'):
    # Ensure the storage directory exists
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ip = addr[0].replace('.', '_')
        filename = f"{storage_dir}/directory_{ip}_{timestamp}.zip"
        
        with open(filename, 'wb') as f:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                f.write(data)
        
        print(f"Saved zip file to {filename}")
        client_socket.close()

if __name__ == '__main__':
    start_listener()

