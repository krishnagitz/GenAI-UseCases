import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

# Ensure session_state is initialized
# if 'chat_messages' not in st.session_state:
#     st.session_state['chat_messages'] = []

history = StreamlitChatMessageHistory(key="chat_messages")

def setup_sidebar():
    st.title('Data Navigator: A Paradigm Shift in Data Product Interaction and Utlization 🦜️🔗')
    streaming_on = st.checkbox('Streaming')
    st.button('Clear Chat History', on_click=clear_chat_history)
    # st.divider()
    st.markdown("---")
    st.write("History Logs")
    st.write(history.messages)
    return streaming_on

def clear_chat_history():
    history.clear()
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

def setup_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
