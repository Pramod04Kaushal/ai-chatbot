import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import sqlite3
import json
from datetime import datetime
import time
USD_TO_LKR = 300

# ─────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────
load_dotenv()

st.set_page_config(
    page_title="Travel AI Assistant",
    page_icon="🌍",

)

MODEL = "llama-3.3-70b-versatile"

# ─────────────────────────────────────────
# 2. DATABASE (KNOWLEDGE BASE)
# ─────────────────────────────────────────


def init_db():
    conn = sqlite3.connect("knowledge.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            question TEXT PRIMARY KEY,
            answer TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS destinations (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           name TEXT UNIQUE,
           country TEXT,
           price INTEGER,
           type TEXT,
           description TEXT
        )
    """)

    conn.commit()
    conn.close()


def seed_data():

    conn = sqlite3.connect("knowledge.db")

    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Bali', 'Indonesia', 1200, 'Beach', 'Beautiful beaches and temples')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Japan', 'Japan', 2500, 'Cultural', 'Rich culture and modern cities')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Sri Lanka', 'Sri Lanka', 800, 'Nature', 'Wildlife, beaches, and mountains')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Maldives', 'Maldives', 3000, 'Luxury', 'Luxury islands and resorts')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Thailand', 'Thailand', 1000, 'Beach', 'Famous for beaches and nightlife')")

    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Dubai', 'UAE', 2800, 'Luxury', 'Modern city with luxury shopping')")
    conn.execute("INSERT OR IGNORE INTO destinations VALUES (NULL, 'Switzerland', 'Switzerland', 3200, 'Nature', 'Beautiful mountains and snow')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'India', 'India', 900, 'Cultural', 'Rich history and heritage')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Italy', 'Italy', 2700, 'Cultural', 'Famous for art, food, and history')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Singapore', 'Singapore', 2200, 'City', 'Clean and modern city')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Australia', 'Australia', 3500, 'Nature', 'Wildlife and beaches')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'France', 'France', 2600, 'Cultural', 'Paris and romantic destinations')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Nepal', 'Nepal', 700, 'Nature', 'Mountains and trekking')")
    conn.execute(
        "INSERT OR IGNORE INTO destinations VALUES (NULL, 'Vietnam', 'Vietnam', 850, 'Budget', 'Affordable travel and culture')")

    conn.commit()
    conn.close()


def get_destinations(max_price=None):
    conn = sqlite3.connect("knowledge.db")
    cursor = conn.cursor()

    if max_price:
        cursor.execute(
            "SELECT name, country, price, type, description FROM destinations WHERE price <= ?",
            (max_price,))
    else:
        cursor.execute(
            "SELECT name, country, price, type, description FROM destinations")

    data = cursor.fetchall()
    conn.close()
    return data


def get_answer_from_db(question):
    conn = sqlite3.connect("knowledge.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT answer FROM knowledge WHERE question LIKE ?",
        ('%' + question + '%',)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def save_to_db(question, answer):
    conn = sqlite3.connect("knowledge.db")
    conn.execute(
        "INSERT OR REPLACE INTO knowledge (question, answer) VALUES (?, ?)",
        (question, answer)
    )
    conn.commit()
    conn.close()


init_db()
seed_data()


# ─────────────────────────────────────────
# 3. SIMPLE NLP ENGINE
# ─────────────────────────────────────────


def preprocess(text):
    return text.lower().strip()


def detect_intent(text):
    text = preprocess(text)

    if any(word in text for word in ["hello", "hi", "hey"]):
        return "greeting"
    elif any(word in text for word in ["price", "cost"]):
        return "pricing"

    elif "teach" in text:
        return "learning"
    elif "weather" in text:
        return "weather"
    else:
        return "unknown"

# ─────────────────────────────────────────
# 4. STATIC KNOWLEDGE (RULE BASED)
# ─────────────────────────────────────────


def rule_based_response(intent):
    responses = {
        "greeting": "Hello! I'm your Travel Assistant 🌍. Ask me about places!",
        "pricing": "Travel packages range from $500 to $3000 depending on location.",
        "recommendation": "I recommend visiting Bali, Japan, or Switzerland!",
        "weather": "Weather depends on the destination 🌦️. Where are you planning to go?"
    }
    return responses.get(intent, None)


# ─────────────────────────────────────────
# 5. GROQ CLIENT
# ─────────────────────────────────────────
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API key missing!")
    st.stop()

client = Groq(api_key=api_key)

# ─────────────────────────────────────────
# 🧠 MULTI CHAT SYSTEM
# ─────────────────────────────────────────
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {"Chat 1": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"


def get_messages():
    return st.session_state.chat_sessions[st.session_state.current_chat]


if "learning_mode" not in st.session_state:
    st.session_state.learning_mode = False
    st.session_state.last_question = None

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None

if "show_quick_options" not in st.session_state:
    st.session_state.show_quick_options = True

if "hide_options_next" not in st.session_state:
    st.session_state.hide_options_next = False

if "scroll_after_render" not in st.session_state:
    st.session_state.scroll_after_render = False

if "scroll_now" not in st.session_state:
    st.session_state.scroll_now = False

# ─────────────────────────────────────────
# 7. SAVE CHAT HISTORY
# ─────────────────────────────────────────


def save_chat(messages):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)

    return filename


def auto_save():
    filename = f"{st.session_state.current_chat}.json"
    with open(filename, "w") as f:
        json.dump(get_messages(), f, indent=2)


# ─────────────────────────────────────────
# 8. UI
# ─────────────────────────────────────────
st.markdown("## 🌍 Travel AI Assistant")
st.caption("Smart travel recommendations powered by AI")

st.markdown("""
<style>

/* Stick input to bottom */
section[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    left: 300px;
    right: 20px;
    z-index: 999;
}
            
button[kind="primary"] {
    border-radius: 50% !important;

}

/* Sidebar width */
section[data-testid="stSidebar"] {
    width: 260px !important;
}

/* Buttons look modern */
section[data-testid="stSidebar"] button {
    border-radius: 10px !important;
    margin-bottom: 6px;
    transition: 0.2s;
}

/* Hover effect */
section[data-testid="stSidebar"] button:hover {
    background-color: #1e293b !important;
}

       


</style>
""", unsafe_allow_html=True)


if st.session_state.show_quick_options:

    st.markdown("### 💡 Quick Options")

    col1, col2, col3 = st.columns(3)

    if col1.button("💸 Cheap Travel"):
        st.session_state.quick_prompt = "cheap travel"

    if col2.button("💎 Luxury Travel"):
        st.session_state.quick_prompt = "luxury travel"

    if col3.button("📋 Travel Plans"):
        st.session_state.quick_prompt = "all travel"


with st.sidebar:

    # 🔥 HEADER (MODERN)
    st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
            <div style="font-size:28px;">🌍</div>
            <div>
                <div style="font-size:18px;font-weight:600;">Travel AI</div>
                <div style="font-size:12px;color:#9ca3af;">Smart assistant</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 🔥 NEW CHAT BUTTON
    if st.button("+  New Chat", use_container_width=True):
        new_chat = f"Chat {len(st.session_state.chat_sessions) + 1}"
        st.session_state.chat_sessions[new_chat] = []
        st.session_state.current_chat = new_chat
        st.session_state.show_quick_options = True
        st.rerun()

    st.markdown("### Chats")

    # 🔥 CHAT LIST WITH ACTIVE STYLE
    for chat in st.session_state.chat_sessions:

        is_active = chat == st.session_state.current_chat

        button_style = """
            background-color:#2563eb;
            color:white;
            border-radius:10px;
            padding:6px;
        """ if is_active else """
            background-color:transparent;
            color:#cbd5f5;
        """

        if st.button(chat, use_container_width=True):
            st.session_state.current_chat = chat
            st.rerun()

    st.markdown("---")

    # 🔥 SETTINGS SECTION
    st.markdown("Settings")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.chat_sessions[st.session_state.current_chat] = []
        st.rerun()

    if st.button("Save Chat", use_container_width=True):
        file = save_chat(get_messages())
        st.success(f"Saved: {file}")

# AUTO SCROLL


def auto_scroll():
    st.markdown("""
        <script>
            setTimeout(function(){
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'auto'
                });
            }, 200);
        </script>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# 9. DISPLAY CHAT
# ─────────────────────────────────────────
def render_message(role, content):
    if role == "user":
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; margin-bottom:12px;">
            <div style="
                background:#2563eb;
                color:white;
                padding:10px 14px;
                border-radius:16px;
                max-width:70%;
                font-size:14px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);
            ">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-start; margin-bottom:12px;">
            <div style="
                background:#1e293b;
                color:white;
                padding:10px 14px;
                border-radius:16px;
                max-width:90%;
                font-size:14px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);
            ">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)


if len(get_messages()) == 0:
    st.write("")  # nothing

for msg in get_messages():
    render_message(msg["role"], msg["content"])

# Scroll after rerun (important)

if st.session_state.scroll_after_render:
    auto_scroll()
    st.session_state.scroll_after_render = False

elif st.session_state.scroll_now:
    auto_scroll()
    st.session_state.scroll_now = False

# ─────────────────────────────────────────
# 10. CHAT LOGIC (CORE AI SYSTEM)
# ─────────────────────────────────────────

# chat input
user_input = st.chat_input("Ask about travel...")

prompt = None

if user_input:
    prompt = user_input

elif st.session_state.quick_prompt:
    prompt = st.session_state.quick_prompt
    st.session_state.quick_prompt = None


if prompt:

    # Hide Quick Options after first input
    if st.session_state.show_quick_options:
        st.session_state.hide_options_next = True

    # Save user message
    get_messages().append({"role": "user", "content": prompt})
    auto_save()

    # Show user message (RIGHT SIDE)
    render_message("user", prompt)

    response = ""

    if prompt.lower().startswith("teach:"):
        answer = prompt.replace("teach:", "").strip()
        save_to_db(st.session_state.last_question, answer)
        response = "Got it! I learned something new ✅"

    else:
        intent = detect_intent(prompt)

        is_lkr = any(word in prompt.lower() for word in ["rs", "rupee", "lkr"])

        # CHEAP
        if "cheap" in prompt.lower():
            places = get_destinations(1500)
            response = "Here are budget travel options:<br><br>"

            for p in places:
                price = p[2] * USD_TO_LKR if is_lkr else p[2]
                currency = "Rs." if is_lkr else "$"

                response += f"""<div style="border:1px solid #444;padding:15px;border-radius:10px;margin-bottom:15px;background-color:#1e1e1e;">
🌍 <b style="font-size:18px;">{p[0]} ({p[1]})</b>
<hr style="border:0.5px solid #555;">
💰 Price: {currency} {price:,}<br>
🏷️ Type: {p[3]}<br>
📝 {p[4]}
</div>"""

        # LUXURY
        elif "luxury" in prompt.lower():
            places = get_destinations()
            response = "Here are luxury travel options:<br><br>"

            for p in places:
                if p[2] >= 2500:
                    price = p[2] * USD_TO_LKR if is_lkr else p[2]
                    currency = "Rs." if is_lkr else "$"

                    response += f"""<div style="border:1px solid #444;padding:15px;border-radius:10px;margin-bottom:15px;background-color:#1e1e1e;">
🌍 <b style="font-size:18px;">{p[0]} ({p[1]})</b>
<hr style="border:0.5px solid #555;">
💰 Price: {currency} {price:,}<br>
🏷️ Type: {p[3]}<br>
📝 {p[4]}
</div>"""

        # ALL
        elif "all" in prompt.lower():
            places = get_destinations()
            response = "Here are all available travel plans:<br><br>"

            for p in places:
                price = p[2] * USD_TO_LKR if is_lkr else p[2]
                currency = "Rs." if is_lkr else "$"

                response += f"""<div style="border:1px solid #444;padding:15px;border-radius:10px;margin-bottom:15px;background-color:#1e1e1e;">
🌍 <b style="font-size:18px;">{p[0]} ({p[1]})</b>
<hr style="border:0.5px solid #555;">
💰 Price: {currency} {price:,}<br>
🏷️ Type: {p[3]}<br>
📝 {p[4]}
</div>"""

        elif is_lkr:
            min_price = 500 * USD_TO_LKR
            max_price = 3000 * USD_TO_LKR
            response = f"Travel packages range from Rs. {min_price:,} to Rs. {max_price:,}"

        elif rule_based_response(intent):
            response = rule_based_response(intent)

        else:
            db_answer = get_answer_from_db(preprocess(prompt))
            if db_answer:
                response = db_answer
            else:
                try:
                    ai_response = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": "You are a travel assistant."}] + get_messages(),
                        temperature=0.7,
                        max_tokens=1200
                    )

                    import re
                    response = ai_response.choices[0].message.content
                    response = re.sub(r'(\d+\.)', r'\n\n\1', response)

                    st.session_state.last_question = preprocess(prompt)

                except Exception as e:
                    response = f"Error: {str(e)}"

    # 🔥 SHOW ASSISTANT MESSAGE (FIXED)
    if "<div" in response or "<br>" in response:
        render_message("assistant", response)
    else:
        message_placeholder = st.empty()
        full_text = ""

        for char in response:
            full_text += char
            message_placeholder.markdown(
                f"""<div style="display:flex;justify-content:flex-start;">
                <div style="background:#1e293b;color:white;padding:10px 14px;border-radius:16px;max-width:70%;">
                {full_text}▌</div></div>""",
                unsafe_allow_html=True
            )
            time.sleep(0.008)

        message_placeholder.markdown(
            f"""<div style="display:flex;justify-content:flex-start;">
            <div style="background:#1e293b;color:white;padding:10px 14px;border-radius:16px;max-width:70%;">
            {full_text}</div></div>""",
            unsafe_allow_html=True
        )

    # Save assistant message
    get_messages().append({"role": "assistant", "content": response})
    auto_save()

    # Hide Quick Options AFTER message is shown
    if st.session_state.hide_options_next:
        st.session_state.show_quick_options = False
        st.session_state.hide_options_next = False

        st.session_state.scroll_after_render = True

        st.rerun()
