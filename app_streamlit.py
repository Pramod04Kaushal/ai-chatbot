# app_streamlit.py   Full Streamlit Chatbot with Memory (Groq)

import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# Save Chat history
import json
from datetime import datetime


def save_chat_history(messages):
    """Save conversation to a JSON file with timestamp."""

    # Remove system message
    export_messages = [m for m in messages if m["role"] != "system"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(export_messages, f, indent=2, ensure_ascii=False)

    return filename


# ─────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────
load_dotenv()

# Page settings (must be FIRST Streamlit command)
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

SYSTEM_PROMPT = """You are a helpful, friendly, and knowledgeable AI assistant.
You give clear and concise answers. If you are unsure, you say so honestly."""

MODEL = "llama-3.3-70b-versatile"  # Groq model

# ─────────────────────────────────────────
# 2. INITIALIZE GROQ CLIENT
# ─────────────────────────────────────────
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API key not found! Please add GROQ_API_KEY in .env file")
    st.stop()

client = Groq(api_key=api_key)

# ─────────────────────────────────────────
# 3. SESSION STATE (MEMORY)
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]


# ─────────────────────────────────────────
# TOKEN MANAGEMENT (NEW)
# ─────────────────────────────────────────
def trim_conversation_history(messages):
    system_prompt = messages[0]
    conversation = messages[1:]

    if len(conversation) > 20:
        conversation = conversation[-20:]

    return [system_prompt] + conversation


# ─────────────────────────────────────────
# 4. UI (HEADER + SIDEBAR)
# ─────────────────────────────────────────
st.title("🤖 AI Chatbot")
st.markdown("*Powered by Groq · Built with Streamlit*")

with st.sidebar:
    st.header("⚙ Settings")

    # Sliders
    temperature = st.slider(
        "Creativity",
        0.0,
        1.0,
        0.7
    )

    max_tokens = st.slider(
        "Max Response Length",
        50,
        1000,
        500
    )

    st.divider()

    # ─────────────────────────────
    # 🧠 PERSONA SYSTEM
    # ─────────────────────────────
    st.subheader("🤖 Bot Persona")

    persona = st.selectbox(
        "Choose a persona:",
        [
            "Helpful Assistant",
            "Python Tutor",
            "Creative Writer",
            "Debate Partner",
            "Custom"
        ]
    )

    persona_prompts = {
        "Helpful Assistant": "You are a helpful, friendly AI assistant.",
        "Python Tutor": "You are an expert Python tutor. Explain clearly with examples and guide step-by-step.",
        "Creative Writer": "You are a creative writer who creates engaging stories, poems, and imaginative content.",
        "Debate Partner": "You challenge ideas and present logical counterarguments."
    }

    if persona == "Custom":
        system_prompt = st.text_area(
            "Write your own persona:",
            "You are a helpful assistant."
        )
    else:
        system_prompt = persona_prompts[persona]

    if st.button("Apply Persona"):
        st.session_state.messages = [
            {"role": "system", "content": system_prompt}
        ]
        st.success(f"Persona set to: {persona}")

    st.divider()

    # Message count
    msg_count = len([
        m for m in st.session_state.messages
        if m["role"] != "system"
    ])
    st.metric("Messages", msg_count)

    # Clear chat
    if st.button("Clear Chat"):
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        st.rerun()

    st.divider()

    # 💾 SAVE CHAT (FIXED POSITION)
    if st.button("💾 Save Chat History"):
        if len(st.session_state.messages) > 1:
            filename = save_chat_history(st.session_state.messages)
            st.success(f"Saved to {filename}")
        else:
            st.warning("No messages to save yet.")


# ─────────────────────────────────────────
# 5. DISPLAY CHAT HISTORY
# ─────────────────────────────────────────
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ─────────────────────────────────────────
# 6. USER INPUT + AI RESPONSE
# ─────────────────────────────────────────
if prompt := st.chat_input("Type your message..."):

    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # ✅ Trim history BEFORE API call
    st.session_state.messages = trim_conversation_history(
        st.session_state.messages
    )

    # AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                ai_reply = response.choices[0].message.content

                st.markdown(ai_reply)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_reply
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.messages.pop()
