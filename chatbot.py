import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# validate API key
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("ERROR: GROQ_API_KEY not found in .env file")
    print("Create .env file and add:")
    print("GROQ_API_KEY=your_key_here")
    exit(1)

# connect to AI
client = Groq(api_key=api_key)

SYSTEM_PROMPT = "You are a helpful, friendly assistant."

conversation_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


def chat(user_message):

    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=conversation_history,

            temperature=0.7,
            max_tokens=500
        )

        ai_reply = response.choices[0].message.content

        conversation_history.append({
            "role": "assistant",
            "content": ai_reply
        })

        return ai_reply

    except Exception as e:

        # remove failed message
        conversation_history.pop()

        error_msg = str(e).lower()

        if "api" in error_msg:
            return "Error: API key problem. Check .env file."

        elif "rate" in error_msg:
            return "Error: Too many requests. Wait a moment."

        elif "quota" in error_msg:
            return "Error: API limit reached."

        elif "connection" in error_msg:
            return "Error: Check internet connection."

        else:
            return f"Unexpected error: {error_msg}"


print("Chatbot Ready! (type quit to exit)")
print("type reset to clear memory\n")


while True:

    user_input = input("You: ").strip()

    if not user_input:
        continue

    if user_input.lower() in {"quit", "exit"}:
        print("AI: Goodbye!")
        break

    if user_input.lower() == "reset":

        conversation_history.clear()

        conversation_history.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })

        print("Chat reset\n")

        continue

    reply = chat(user_input)

    print("AI:", reply, "\n")
