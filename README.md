# 🌍 Travel AI Assistant

A smart travel recommendation web application built with **Streamlit** and **AI integration**.
This assistant helps users discover travel destinations, explore budget options, and get intelligent travel advice in real time.

---

## 🚀 Features

* 💬 **AI Chat Assistant**
  Ask anything about travel and get intelligent responses.

* 💸 **Budget & Luxury Travel Suggestions**
  Instantly explore cheap and luxury travel destinations.

* 🧠 **Learning System**
  The assistant can learn new answers from users using:

  ```
  teach: your answer
  ```

* 💱 **Currency Conversion (USD → LKR)**
  Automatically converts prices into Sri Lankan Rupees.

* 🗂 **Chat History Saving**
  Save conversations for later use.

* ⚡ **Quick Options Buttons**

  * Cheap Travel
  * Luxury Travel
  * Travel Plans

* 🎨 **Modern UI**

  * ChatGPT-like interface
  * Custom styling
  * Responsive layout

---

## 🛠️ Technologies Used

* Python
* Streamlit
* OpenAI / Groq API
* SQLite Database
* HTML + CSS (custom UI styling)

---

## 📦 Installation

### 1. Clone the repository

```
git clone https://github.com/your-username/travel-ai-assistant.git
cd travel-ai-assistant
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Add your API key

Create a `.env` file:

```
GROQ_API_KEY=your_api_key_here
```

---

## ▶️ Run the App

```
streamlit run app_streamlit.py
```

---

## 🧠 How It Works

1. User enters a prompt
2. System detects intent (cheap, luxury, etc.)
3. Checks:

   * Rule-based responses
   * Database answers
   * AI model fallback
4. Displays formatted response in chat UI

---

## 📁 Project Structure

```
travel-ai-assistant/
│
├── app_streamlit.py      # Main application
├── database.db           # SQLite database
├── .env                  # API key
├── requirements.txt      # Dependencies
└── README.md             # Project documentation
```

---

## ✨ Future Improvements

* 🌐 Deploy online (Streamlit Cloud)
* 🧳 Add hotel & flight recommendations
* 🗺 Google Maps integration
* 🎙 Voice input support
* 📊 Personalized recommendations

---

## 👨‍💻 Author

**Pramod Kaushal**

---

## 📜 License

This project is open-source and available under the MIT License.
