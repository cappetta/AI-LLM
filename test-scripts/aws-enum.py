import subprocess

def run_aws_command(command, region=None):
    if region:
        command.extend(['--region', region])
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except subprocess.CalledProcessError as e:
        return f"CalledProcessError: {e}"
    except subprocess.TimeoutExpired as e:
        return f"TimeoutExpired: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

def enumerate_aws_resources(region):
    aws_commands = {
        "S3 Buckets": ["aws", "s3", "ls"],
        "EC2 Instances": ["aws", "ec2", "describe-instances"],
        "IAM Roles": ["aws", "iam", "list-roles"],
        "VPCs": ["aws", "ec2", "describe-vpcs"],
        "Subnets": ["aws", "ec2", "describe-subnets"],
        "Security Groups": ["aws", "ec2", "describe-security-groups"],
        "RDS Instances": ["aws", "rds", "describe-db-instances"],
        "Lambda Functions": ["aws", "lambda", "list-functions"],
        "ECS Clusters": ["aws", "ecs", "list-clusters"],
        "EKS Clusters": ["aws", "eks", "list-clusters"],
        "CloudFormation Stacks": ["aws", "cloudformation", "describe-stacks"]
    }
    
    results = {}
    for resource, command in aws_commands.items():
        results[resource] = run_aws_command(command, region)
    
    return results

def check_permissions():
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True
        else:
            print("Error: AWS CLI permissions check failed.")
            print(f"Error Output: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"CalledProcessError: {e}")
        return False
    except subprocess.TimeoutExpired as e:
        print(f"TimeoutExpired: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def main():
    if not check_permissions():
        print("Insufficient AWS CLI permissions.")
        return
    
    regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'af-south-1', 'ap-east-1', 'ap-south-1', 'ap-northeast-1',
        'ap-northeast-2', 'ap-northeast-3', 'ap-southeast-1', 'ap-southeast-2',
        'ca-central-1', 'cn-north-1', 'cn-northwest-1', 'eu-central-1',
        'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1', 'eu-south-1',
        'me-south-1', 'sa-east-1'
    ]
    
    for region in regions:
        print(f"\nStarting AWS environment enumeration for region: {region}...")
        results = enumerate_aws_resources(region)
        
        for resource, output in results.items():
            print(f"\n{resource} in {region}:\n{output}")

if __name__ == "__main__":
    main()
