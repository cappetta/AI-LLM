import socket
import requests
import ray

ray.init()

print('''This cluster consists of
    {} nodes in total
    {} CPU resources in total
'''.format(len(ray.nodes()), ray.cluster_resources()['CPU']))

@ray.remote
def fetch_metadata():
    metadata_urls = {
        "aws": "http://169.254.169.254/latest/meta-data/iam/security-credentials/ray-autoscaler-v1",
        # "gcp": "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
        # "azure": "http://169.254.169.254/metadata/instance?api-version=2021-01-01"
    }
    
    headers = {
        "gcp": {"Metadata-Flavor": "Google"},
        # "azure": {"Metadata": "true"}
    }
    
    results = {"ip": socket.gethostbyname(socket.gethostname())}

    for cloud, url in metadata_urls.items():
        try:
            if cloud in headers:
                response = requests.get(url, headers=headers[cloud], timeout=5)
            else:
                response = requests.get(url, timeout=5)
            results[f"{cloud}_status_code"] = response.status_code
            results[f"{cloud}_response_body"] = response.text
        except requests.RequestException as e:
            results[f"{cloud}_error"] = str(e)

    return results

# Only create a single task since we need just one result per cloud provider
object_id = fetch_metadata.remote()
result = ray.get(object_id)

ip_address = result["ip"]

print('Tasks executed')
print('    Task on {}'.format(ip_address))

# Print out the responses to see the fetched metadata
print(f"IP: {result['ip']}")
for cloud in ["aws", "gcp", "azure"]:
    status_key = f"{cloud}_status_code"
    body_key = f"{cloud}_response_body"
    if status_key in result:
        print(f"  {cloud.upper()} - Status Code: {result[status_key]}, Response Body: {result[body_key]}")
    else:
        print(f"  {cloud.upper()} - Error: {result.get(f'{cloud}_error', 'Unknown error')}")
