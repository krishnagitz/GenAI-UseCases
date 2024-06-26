from langchain_aws import AmazonKnowledgeBasesRetriever
from config import KB_IDS

def initialize_retriever(selected_kb_id: str):
    return AmazonKnowledgeBasesRetriever(
        knowledge_base_id=selected_kb_id,
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 10, 'overrideSearchType': "HYBRID"}},
    )
