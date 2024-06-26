import streamlit as st
from operator import itemgetter
from langchain_core.runnables import RunnableParallel
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from config import KB_IDS
from logging_setup import setup_logging
from model import model, prompt
from retriever import initialize_retriever
from streamlit_ui import setup_sidebar, setup_session_state, history
from utils import extract_citations
from s3_utils import create_presigned_url, parse_s3_uri

setup_logging()

st.set_page_config(page_title='3 DP Data Genie')

streaming_on = setup_sidebar()
setup_session_state()

kb_selection = st.sidebar.radio("Select Use Cases", list(KB_IDS.keys()))
selected_kb_id = KB_IDS[kb_selection]
retriever = initialize_retriever(selected_kb_id)

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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    config = {"configurable": {"session_id": "any"}}
    
    if streaming_on:
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
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    else:
        with st.chat_message("assistant"):
            response = chain_with_history.invoke(
                {"question": prompt, "history": history},
                config
            )
            st.write(response['response'])
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
            st.session_state.messages.append({"role": "assistant", "content": response['response']})
