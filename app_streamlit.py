import streamlit as st
import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "deepseek-coder:1.3b"
# OLLAMA_MODEL = "phi:latest"

def get_file_summary(file_content):
    prompt = (
        "Summarize the following file content in a few sentences for a developer:\n\n"
        f"{file_content[:4000]}"  # Limit to 4000 chars for LLM context
    )
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Could not generate summary.")
    except Exception as e:
        return f"Error generating summary: {e}"

# Streamlit page configuration
st.set_page_config(page_title="Chatbot", layout="wide")

# Initialize session state variables
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = []
if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_summary" not in st.session_state:
    st.session_state.file_summary = ""

# Sidebar settings
with st.sidebar:
    st.title("Chat Settings")
    dark_mode = st.toggle("🌙 Dark Mode", value=False)

    st.markdown("### Chats History")
    for i, chat in enumerate(st.session_state.chat_histories):
        is_selected = (i == st.session_state.current_chat_index)
        button_label = chat["title"]
        if is_selected:
            button_label = f"**{button_label}**"
        if st.button(button_label, key=f"chat_list_{i}"):
            st.session_state.messages = chat["messages"].copy()
            st.session_state.file_summary = chat.get("file_summary", "")
            st.session_state.current_chat_index = i

    if st.button("🆕 New Chat"):
        # Save current chat if there are any messages
        if st.session_state.messages:
            first_user_msg = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "New Chat")
            short_title = " ".join(first_user_msg.split()[:8]) + ("..." if len(first_user_msg.split()) > 8 else "")
            chat_data = {
                "title": short_title,
                "messages": st.session_state.messages.copy(),
                "file_summary": st.session_state.file_summary,
                "file_name": st.session_state.get("last_uploaded_file", ""),
            }
            if st.session_state.current_chat_index is not None and \
               st.session_state.current_chat_index < len(st.session_state.chat_histories):
                st.session_state.chat_histories[st.session_state.current_chat_index] = chat_data
            else:
                st.session_state.chat_histories.append(chat_data)

        # Start new chat
        st.session_state.messages = []
        st.session_state.file_summary = ""
        st.session_state.current_chat_index = len(st.session_state.chat_histories)
        st.session_state.chat_histories.append({
            "title": "New Chat",
            "messages": [],
            "file_summary": "",
            "file_name": "",
        })

    if st.button("🗑️ Clear All History"):
        st.session_state.chat_histories = []
        st.session_state.current_chat_index = None
        st.session_state.messages = []
        st.session_state.file_summary = ""
        # Only reset file uploader if you want to clear the file
        # st.session_state.file_uploader_key += 1
        st.rerun()

    uploaded_file = st.file_uploader(
        "Upload a file",
        type=["txt", "pdf", "docx"],
        key=f"uploaded_file_{st.session_state.file_uploader_key}"
    )

# Apply dark mode styles
if dark_mode:
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #1e1f24 !important;
            color: #f1f1f1 !important;
        }
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stFileUploader label div,
        .stButton>button {
            background: #2b2d31 !important;
            color: #f1f1f1 !important;
            border: 1px solid #3c3f45;
        }
        .stChatMessage, .stChatMessageContent, .stMarkdown, .stMarkdown p {
            background-color: #2c2f33 !important;
            color: #f1f1f1 !important;
            border-radius: 8px;
            padding: 10px;
        }
        .stFileUploader, .css-1p05t8e, .css-1y4p8pa {
            background-color: transparent !important;
        }
        .block-container {
            padding-top: 2rem;
        }
        .css-1x8cf1d {
            color: white;
        }
        div[data-testid="stVerticalBlock"] > div:has(> .stButton) {
            padding-top: 0.5rem;
        }
        .summary-box {
            background-color: #2d3436 !important;
            color: #f1f1f1 !important;
            padding: 16px;
            border-radius: 10px;
            border: 1px solid #444;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        .summary-box {
            background-color: #eafaf1 !important;
            color: #222 !important;
            padding: 16px;
            border-radius: 10px;
            border: 1px solid #ddd;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Show file summary if uploaded
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8", errors="ignore")
    file_name = uploaded_file.name

    # Always summarize on every upload
    with st.spinner("Summarizing file..."):
        summary = get_file_summary(file_content)
    st.session_state.file_summary = summary
    st.session_state.last_uploaded_file = file_name
    st.session_state.last_file_content = file_content

    # Store summary and title in current chat history
    if st.session_state.current_chat_index is not None:
        chat = st.session_state.chat_histories[st.session_state.current_chat_index]
        chat["file_summary"] = summary
        chat["file_name"] = file_name
        chat["title"] = f"Summary of {file_name}"
        st.session_state.file_summary = summary  # Ensure UI updates!
    else:
        # If no chat exists, create a new one for the summary
        st.session_state.chat_histories.append({
            "title": f"Summary of {file_name}",
            "messages": [],
            "file_summary": summary,
            "file_name": file_name,
        })
        st.session_state.current_chat_index = len(st.session_state.chat_histories) - 1
        st.session_state.file_summary = summary  # Ensure UI updates!

    st.session_state.file_uploader_key += 1  # This resets the file uploader
    st.session_state.file_content = file_content

# Main chat interface
st.title("💬 Chatbot")

# Process selected suggestion if present (always, not just when messages are empty)
if "selected_suggestion" in st.session_state and st.session_state.selected_suggestion:
    s = st.session_state.selected_suggestion
    st.session_state.messages.append({"role": "user", "content": s})
    with st.chat_message("user"):
        st.markdown(s)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": s,
                        "stream": False
                    },
                    timeout=120
                )
                response.raise_for_status()
                result = response.json()
                assistant_reply = result.get("response", "Sorry, I couldn't generate a response.")
            except Exception as e:
                assistant_reply = f"Error: {e}"

            st.markdown(assistant_reply)
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    # Update chat history
    if st.session_state.current_chat_index is not None:
        chat = st.session_state.chat_histories[st.session_state.current_chat_index]
        chat["messages"] = st.session_state.messages.copy()
        # Auto-generate title if it's still default
        if chat["title"] == "New Chat":
            first_prompt = s.strip()
            short_title = " ".join(first_prompt.split()[:8]) + ("..." if len(first_prompt.split()) > 8 else "")
            chat["title"] = short_title
    st.session_state.selected_suggestion = None  # Reset after processing
    st.rerun()

# Show greeting and suggestions if chat is empty
if not st.session_state.messages:
    st.markdown("👋 **Hi! I'm your coding assistant.**")
    st.markdown("Here are some things you can ask me:")
    suggestions = [
        "How do I write a Python function to reverse a string?",
        "Can you explain the difference between a list and a tuple in Python?",
        "Show me an example of a REST API using FastAPI.",
        "How do I read a CSV file with pandas?",
        "Write a unit test for a function that adds two numbers.",
        "What is a decorator in Python and how do I use it?",
        "How can I optimize a slow Python loop?",
        "Explain the concept of async/await in Python.",
    ]
    if "selected_suggestion" not in st.session_state:
        st.session_state.selected_suggestion = None

    for s in suggestions:
        if st.button(s, key=f"suggestion_{s}"):
            st.session_state.selected_suggestion = s
            st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Show file summary box
if st.session_state.file_summary:
    st.markdown(
        f"""
        <div class="summary-box">
            <b>Summary:</b>
            <div style="margin-top: 10px;">{st.session_state.file_summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# User input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=120
                )
                response.raise_for_status()
                result = response.json()
                assistant_reply = result.get("response", "Sorry, I couldn't generate a response.")
            except Exception as e:
                assistant_reply = f"Error: {e}"

            st.markdown(assistant_reply)
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    # Update chat history
    if st.session_state.current_chat_index is not None:
        chat = st.session_state.chat_histories[st.session_state.current_chat_index]
        chat["messages"] = st.session_state.messages.copy()
        chat["file_summary"] = st.session_state.file_summary
        # Auto-generate title if it's still default
        if chat["title"] == "New Chat":
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    first_prompt = msg["content"].strip()
                    short_title = " ".join(first_prompt.split()[:8]) + ("..." if len(first_prompt.split()) > 8 else "")
                    chat["title"] = short_title
                    break
