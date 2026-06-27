# NexBot — AI-Powered Customer Support Chatbot

An intelligent chatbot built with **NLP**, **Flask**, and **SQLite** that handles customer support queries with contextual responses and full interaction logging.

![Python]
![Flask]
![NLTK]
![SQLite]
![License]

---

## Features

-  Real-time chat interface with typing indicator
-  NLP intent classification using NLTK (lemmatization, tokenization, stopword filtering)
-  **Logs panel** — full interaction history stored in SQLite
-  **Analytics dashboard** — message counts, session stats, top intents
-  Quick-topic chips for one-click queries
-  Responsive dark UI with sidebar navigation
-  REST API for integration with other apps

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.10+, Flask 3.0             |
| NLP        | NLTK (tokenizer, lemmatizer, stopwords) |
| Database   | SQLite3 (conversations + sessions)  |
| Frontend   | Vanilla JS, CSS3                    |
| Server     | Gunicorn (production)               |

---

##  Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-chatbot.git
cd ai-chatbot
```

### 2. Create a virtual environment

```bash
python -m venv venv --without-pip
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

##  Project Structure

```
ai-chatbot/
├── app.py                  # Flask app, NLP engine, SQLite logic
├── requirements.txt
├── templates/
│   └── index.html          # Chat UI (3-panel: Chat, Logs, Stats)
├── static/
│   ├── css/style.css
│   └── js/main.js
├── database/
│   └── chatbot.db          # Auto-created at runtime
└── README.md
```

---

##  API Reference

### `POST /chat`
```json
{ "message": "Track my order", "session": "sess_abc123" }
```
Response:
```json
{ "reply": "To track your order…", "intent": "order", "session": "sess_abc123" }
```

### `GET /history/<session_id>`
Returns all messages for a session.

### `GET /stats`
Returns total messages, sessions, and top intents.

---

##  Supported Intents

| Intent    | Example queries                              |
|-----------|----------------------------------------------|
| greeting  | "Hello", "Hi", "Hey"                         |
| farewell  | "Bye", "Goodbye"                             |
| help      | "I need help", "What can you do?"            |
| order     | "Track my order", "Where is my package?"     |
| refund    | "I want a refund", "My item is broken"       |
| pricing   | "How much does it cost?", "Any discounts?"   |
| account   | "Forgot password", "Can't log in"            |
| hours     | "When are you open?", "Weekend hours?"       |
| contact   | "Talk to a human", "Phone number?"           |
| joke      | "Tell me a joke"                             |

---

##  License

MIT © 2024
