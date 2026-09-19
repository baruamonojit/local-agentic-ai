import re
import uuid
from typing import Any, Dict
from dotenv import load_dotenv
import streamlit as st
import os
from langchain.agents import create_agent
from langchain.messages import AIMessageChunk, HumanMessage
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from tavily import TavilyClient

# 1. Page Config & Env
st.set_page_config(page_title="AI Chef Assistant", page_icon="🍳", layout="centered")
load_dotenv()

# 2. Custom CSS to Align User Messages to the Right and Chef to the Left
st.markdown("""
<style>
    /* Reset base message display */
    .stChatMessage {
        display: flex !important;
        margin-bottom: 0.75rem;
    }

    /* USER MESSAGE: Target user chat container directly */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]),
    .user-msg-container {
        flex-direction: row-reverse !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        max-width: 80% !important;
    }

    /* Move user avatar and text alignment to right */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) div[data-testid="stChatMessageContent"],
    .user-msg-container div[data-testid="stChatMessageContent"] {
        text-align: right !important;
        background-color: #2b2333 !important; /* Elegant subtle purple/dark tint */
        border-radius: 12px !important;
        padding: 8px 14px !important;
    }

    /* ASSISTANT MESSAGE: Keep on left */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) {
        margin-right: auto !important;
        margin-left: 0 !important;
        max-width: 85% !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) div[data-testid="stChatMessageContent"] {
        background-color: #1e232a !important;
        border-radius: 12px !important;
        padding: 8px 14px !important;
        text-align: left !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Cached Models & Agent
@st.cache_resource
def get_llm_and_agent():

    ollama_host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    llm = ChatOllama(
        base_url=ollama_host,
        model="qwen3:8b",
        temperature=0.2,
        num_ctx=4096,
        keep_alive=-1,
    )

    tavily_client = TavilyClient()

    @tool
    def web_search(query: str) -> str:
        """Search the web for rare ingredients, obscure dishes, or trending recipes."""
        results = tavily_client.search(query, max_results=2, search_depth="basic")
        clean_snippets = []
        for res in results.get("results", []):
            content = res.get("content", "")
            content = re.sub(r"\[.*?\]", "", content)
            clean_snippets.append(content.strip())
        return " ".join(clean_snippets)[:600]

    system_prompt = """
    You are a rapid-fire personal chef assistant.
    Your goal is to give quick, ultra-scannable meal ideas under 80 words.

    RULES:
    1. For greetings or chit-chat, reply directly without using tools.
    2. Use internal culinary knowledge first. ONLY call web_search if explicitly asked to search or if ingredients are highly unusual.
    3. Format recipes as:
       - **Dish Name** (bold) + Total Time
       - **Key Ingredients** (comma-separated list)
       - **Quick Method** (maximum 3 concise bullet points)
    4. Never paste search snippets, URLs, or markdown links.
    """

    agent = create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=system_prompt,
        checkpointer=InMemorySaver(),
    )

    return llm, agent


llm, agent = get_llm_and_agent()


# 4. Intent Classifier for Fast Chit-Chat
def is_simple_chat(text: str) -> bool:
    cleaned = text.strip().lower()
    chit_chat = {
        "hi", "hello", "hey", "hola", "yo", "sup", "good morning",
        "good evening", "how are you", "who are you", "what can you do",
        "thanks", "thank you", "bye", "exit", "quit", "help"
    }
    if cleaned in chit_chat or len(cleaned) <= 3:
        return True
    return False


# 5. Session State
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey there! Tell me what ingredients you have, and I'll whip up a quick recipe! 🍳"}
    ]

# 6. Sidebar
with st.sidebar:
    st.title("🍳 Chef Assistant")
    st.caption("⚡ Fast-Path Routing Active")
    st.write(f"**Session ID:** `{st.session_state.thread_id[:8]}...`")

    if st.button("Clear Conversation / New Chat", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = [
            {"role": "assistant", "content": "Chat cleared! What ingredients are we cooking with today?"}
        ]
        st.rerun()

st.title("Quick Recipe Generator")
st.write("Enter leftover ingredients in your kitchen to generate an instant recipe.")

# 7. Render Chat History with Avatars
for msg in st.session_state.messages:
    avatar = "🧑‍🍳" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 8. Chat Input & Processing
if prompt := st.chat_input("e.g. chicken, oil, potatoes, masala..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧑‍🍳"):
        status_placeholder = st.empty()

        # PATH A: Fast Chit-Chat Path
        if is_simple_chat(prompt):
            status_placeholder.markdown("💬 *Chef is typing...*")
            def fast_stream_generator():
                for chunk in llm.stream([
                    ("system", "You are a friendly personal chef. Reply briefly and warmly in 1-2 sentences."),
                    ("user", prompt)
                ]):
                    if chunk.content:
                        yield chunk.content

            full_response = st.write_stream(fast_stream_generator())

        # PATH B: Agent Path
        else:
            status_placeholder.markdown("🍳 *Chef is cooking up an idea...*")
            thread_config = {"configurable": {"thread_id": st.session_state.thread_id}}

            def agent_stream_generator():
                first_token = False
                for chunk, metadata in agent.stream(
                    {"messages": [HumanMessage(content=prompt)]},
                    thread_config,
                    stream_mode="messages",
                ):
                    tool_calls = getattr(chunk, "tool_call_chunks", None) or chunk.additional_kwargs.get("tool_calls")
                    if tool_calls and not first_token:
                        status_placeholder.markdown("🔍 *Checking web for recipe notes...*")

                    if isinstance(chunk, AIMessageChunk) and chunk.content and not tool_calls:
                        if not first_token:
                            status_placeholder.empty()
                            first_token = True
                        yield chunk.content

                if not first_token:
                    status_placeholder.empty()

            full_response = st.write_stream(agent_stream_generator())

    st.session_state.messages.append({"role": "assistant", "content": full_response})