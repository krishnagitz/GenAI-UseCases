# ------------------------------------------------------
# Streamlit
# 3DP DataGenie Knowledge Bases for Amazon Bedrock and LangChain
# ------------------------------------------------------

import boto3
import logging
from botocore.client import Config

from typing import List, Dict
from pydantic import BaseModel
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_aws import ChatBedrock
from langchain_aws import AmazonKnowledgeBasesRetriever
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

# ------------------------------------------------------
# Log level

logging.getLogger().setLevel(logging.ERROR)  # reduce log level

# ------------------------------------------------------
# Amazon Bedrock - settings

session = boto3.session.Session()
region = session.region_name
region = 'us-east-1'
bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_client = boto3.client('bedrock-runtime', region_name=region)
bedrock_agent_client = boto3.client("bedrock-agent-runtime",
                                    config=bedrock_config, region_name=region)

model_id = "anthropic.claude-3-haiku-20240307-v1:0"
model_kwargs = {
    "max_tokens": 2048,
    "temperature": 0.0,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman"],
}

# ------------------------------------------------------
# Knowledge Base IDs

KB_IDS = {
    "Metadata": "VKMO0RRXJY",
    "StarBurst Data": "QM100Z4RFN",
    "Usage": "KRND7WLJHM"
}

# ------------------------------------------------------
# LangChain - RAG chain with chat history

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."
                   "Answer the question based only on the following context:\n {context}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

model = ChatBedrock(
    client=bedrock_client,
    model_id=model_id,
    model_kwargs=model_kwargs,
)

# Streamlit Chat Message History
history = StreamlitChatMessageHistory(key="chat_messages")

# Pydantic data model and helper function for Citations

class Citation(BaseModel):
    page_content: str
    metadata: Dict

def extract_citations(response: List[Dict]) -> List[Citation]:
    return [Citation(page_content=doc.page_content, metadata=doc.metadata) for doc in response]

# S3 Presigned URL

def create_presigned_url(bucket_name: str, object_name: str, expiration: int = 300) -> str:
    """Generate a presigned URL to share an S3 object"""
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except NoCredentialsError:
        st.error("AWS credentials not available")
        return ""
    return response

def parse_s3_uri(uri: str) -> tuple:
    """Parse S3 URI to extract bucket and key"""
    parts = uri.replace("s3://", "").split("/")
    bucket = parts[0]
    key = "/".join(parts[1:])
    return bucket, key

# Streamlit

import streamlit as st

# Page title
st.set_page_config(page_title='3 DP Data Genie')

# Clear Chat History function
def clear_chat_history():
    history.clear()
    st.session_state.messages = [{"role": "3DP Data Assistant", "content": "How may I assist you today?"}]

with st.sidebar:
    st.title('3 DP Data Genie 🦜️🔗')
    streaming_on = st.checkbox('Streaming')
    st.button('Clear Chat History', on_click=clear_chat_history)
    # st.divider()
    st.markdown("---")
    st.write("History Logs")
    st.write(history.messages)
    
    # Radio buttons for Knowledge Base ID selection
    kb_selection = st.radio("Select Use Cases", list(KB_IDS.keys()))
    selected_kb_id = KB_IDS[kb_selection]

# Initialize the retriever with the selected KB ID
retriever = AmazonKnowledgeBasesRetriever(
    knowledge_base_id=selected_kb_id,
    retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 10, 'overrideSearchType': "HYBRID",}},
)

# Update the chain with the retriever
chain = (
    RunnableParallel({
        "context": itemgetter("question") | retriever,
        "question": itemgetter("question"),
        "history": itemgetter("history"),
    })
    .assign(response=prompt | model | StrOutputParser())
    .pick(["response", "context"])
)

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: history,
    input_messages_key="question",
    history_messages_key="history",
    output_messages_key="response",
)

# Initialize session state for messages if not already present
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat Input - User Prompt 
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    config = {"configurable": {"session_id": "any"}}
    
    if streaming_on:
        # Chain - Stream
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ''
            for chunk in chain_with_history.stream(
                {"question": prompt, "history": history},
                config
            ):
                if 'response' in chunk:
                    full_response += chunk['response']
                    placeholder.markdown(full_response)
                else:
                    full_context = chunk['context']
            placeholder.markdown(full_response)
            # Citations with S3 pre-signed URL
            citations = extract_citations(full_context)
            with st.expander("Show source details >"):
                for citation in citations:
                    st.write("Page Content:", citation.page_content)
                    s3_uri = citation.metadata['location']['s3Location']['uri']
                    bucket, key = parse_s3_uri(s3_uri)
                    presigned_url = create_presigned_url(bucket, key)
                    if presigned_url:
                        st.markdown(f"Source: [{s3_uri}]({presigned_url})")
                    else:
                        st.write(f"Source: {s3_uri} (Presigned URL generation failed)")
                    st.write("Score:", citation.metadata['score'])
            # session_state append
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    else:
        # Chain - Invoke
        with st.chat_message("assistant"):
            response = chain_with_history.invoke(
                {"question": prompt, "history": history},
                config
            )
            st.write(response['response'])
            # Citations with S3 pre-signed URL
            citations = extract_citations(response['context'])
            with st.expander("Show source details >"):
                for citation in citations:
                    st.write("Page Content:", citation.page_content)
                    s3_uri = citation.metadata['location']['s3Location']['uri']
                    bucket, key = parse_s3_uri(s3_uri)
                    presigned_url = create_presigned_url(bucket, key)
                    if presigned_url:
                        st.markdown(f"Source: [{s3_uri}]({presigned_url})")
                    else:
                        st.write(f"Source: {s3_uri} (Presigned URL generation failed)")
                    st.write("Score:", citation.metadata['score'])
            # session_state append
            st.session_state.messages.append({"role": "assistant", "content": response['response']})
