import boto3
from botocore.client import Config

# Explicitly pass credentials and configuration
session = boto3.client(service_name='bedrock',
    region_name='us-east-1',  # Replace with your region
    config=Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
)

# bedrock_client = session.client('bedrock-runtime')
# bedrock_agent_client = session.client("bedrock-agent-runtime")

# Continue with your code...

print(session.list_foundation_models())
