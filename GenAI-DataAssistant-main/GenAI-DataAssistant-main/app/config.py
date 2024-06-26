import boto3
from botocore.client import Config

# Amazon Bedrock settings
session = boto3.session.Session()
region = session.region_name
region='us-east-1'
bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_client = boto3.client('bedrock-runtime', region_name=region)
bedrock_agent_client = boto3.client("bedrock-agent-runtime", config=bedrock_config, region_name=region)

model_id = "anthropic.claude-3-haiku-20240307-v1:0"
model_kwargs = {
    "max_tokens": 2048,
    "temperature": 0.0,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman"],
}

KB_IDS = {
    "Metadata": "VKMO0RRXJY",
    "StarBurst Data": "QM100Z4RFN",
    "Usage": "KRND7WLJHM"
}

print(bedrock_client)