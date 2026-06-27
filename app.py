import os
import json
import sqlite3
import datetime
import random
import string

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_PATH = os.path.join("database", "chatbot.db")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def get_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            session   TEXT NOT NULL,
            role      TEXT NOT NULL,
            message   TEXT NOT NULL,
            intent    TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id        TEXT PRIMARY KEY,
            started   TEXT NOT NULL,
            messages  INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def log_message(session_id, role, message, intent=None):
    conn = get_db()
    ts = datetime.datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO conversations (session, role, message, intent, timestamp) VALUES (?,?,?,?,?)",
        (session_id, role, message, intent, ts)
    )
    conn.execute(
        "INSERT INTO sessions (id, started, messages) VALUES (?,?,1) "
        "ON CONFLICT(id) DO UPDATE SET messages = messages + 1",
        (session_id, ts)
    )
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# NLP Engine
# ---------------------------------------------------------------------------
import nltk
nltk.download("punkt",     quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet",   quiet=True)
nltk.download("punkt_tab", quiet=True)

from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

lemmatizer = WordNetLemmatizer()
STOP_WORDS  = set(stopwords.words("english"))

INTENTS = {
    "greeting": {
        "patterns": ["hello","hi","hey","good morning","good afternoon","good evening","howdy","greetings","whats up","sup"],
        "responses": [
            "Hello! I'm NexBot, your AI support assistant. How can I help you today?",
            "Hi there! Great to see you. What can I do for you?",
            "Hey! I'm here and ready to help. What's on your mind?",
        ]
    },
    "farewell": {
        "patterns": ["bye","goodbye","see you","take care","later","farewell","quit","exit"],
        "responses": [
            "Goodbye! Have a wonderful day!",
            "See you later! Feel free to come back anytime.",
            "Take care! It was a pleasure chatting with you.",
        ]
    },
    "thanks": {
        "patterns": ["thank","thanks","thank you","appreciate","grateful","cheers"],
        "responses": [
            "You're welcome! Is there anything else I can help you with?",
            "Happy to help! Let me know if you need anything else.",
            "Anytime! That's what I'm here for.",
        ]
    },
    "help": {
        "patterns": ["help","support","assist","problem","issue","trouble","stuck","confused","how do i","how to","what can you do"],
        "responses": [
            "I'm here to help! You can ask me about:\n• Product information\n• Order status\n• Account issues\n• Returns and refunds\n• Technical support\n\nWhat do you need help with?",
            "Sure, I can assist! Tell me more about your issue.",
        ]
    },
    "order": {
        "patterns": ["order","purchase","bought","buy","track","shipping","delivery","package","parcel","dispatch"],
        "responses": [
            "To track your order, please provide your order ID (e.g. ORD-12345). I'll look it up right away!",
            "For order inquiries, I'll need your order number. You can find it in your confirmation email.",
            "Orders typically ship within 1-3 business days. Share your order ID for a precise update.",
        ]
    },
    "refund": {
        "patterns": ["refund","return","money back","cancel","exchange","replace","broken","damaged"],
        "responses": [
            "I'm sorry to hear that! Our return policy allows refunds within 30 days of purchase.\n\nTo start a return:\n1. Share your order ID\n2. Describe the issue\n3. We'll send a prepaid return label\n\nWould you like to proceed?",
            "Refund requests are processed within 3-5 business days. Please share your order number so I can initiate this for you.",
        ]
    },
    "pricing": {
        "patterns": ["price","cost","how much","fee","charge","expensive","cheap","discount","coupon","promo","offer","deal"],
        "responses": [
            "Our pricing varies by product. Could you tell me which specific item you're interested in?",
            "We have flexible plans to suit every budget. Want me to walk you through our current offers and discounts?",
        ]
    },
    "account": {
        "patterns": ["account","login","password","sign in","register","signup","profile","email","username","forgot"],
        "responses": [
            "For account issues:\n• Forgot password? Click Reset Password on the login page\n• Can't log in? Clear your browser cache and try again\n• New account? Click Sign Up on our homepage\n\nWhat specific issue are you facing?",
            "I can help with account-related queries! Is this about login, registration, or profile settings?",
        ]
    },
    "hours": {
        "patterns": ["hours","open","close","timing","when","available","schedule","weekend","sunday","monday"],
        "responses": [
            "Our support team is available:\n• Mon-Fri: 9 AM - 8 PM\n• Sat-Sun: 10 AM - 6 PM\n\nFor 24/7 assistance, I'm always here!",
        ]
    },
    "contact": {
        "patterns": ["contact","phone","email","call","reach","talk to","human","agent","person","representative"],
        "responses": [
            "You can reach our team at:\n• Email: support@nexbot.ai\n• Phone: 1-800-NEX-CHAT\n• Live Chat: Available Mon-Fri 9AM-8PM\n\nWould you like me to connect you with a live agent?",
        ]
    },
    "joke": {
        "patterns": ["joke","funny","laugh","humor","entertain"],
        "responses": [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "I told my AI to be funny. It said: Error 404 - Humor not found.",
            "What do you call a robot who always takes the longest path? An algo-rhythm!",
        ]
    },
}

FALLBACK_RESPONSES = [
    "I'm not sure I understood that. Could you rephrase? I'm best at helping with orders, accounts, refunds, and support.",
    "Hmm, I didn't quite catch that. Try asking about orders, returns, pricing, or account issues!",
    "That's a bit outside my expertise. Could you ask something about our products or services?",
    "I want to help, but I need more context. What specifically can I assist you with today?",
]

def preprocess(text):
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    tokens = word_tokenize(text)
    return [lemmatizer.lemmatize(t) for t in tokens if t not in STOP_WORDS]

def classify_intent(text):
    tokens = set(preprocess(text))
    raw    = text.lower()
    best_intent = None
    best_score  = 0

    for intent, data in INTENTS.items():
        score = 0
        for pattern in data["patterns"]:
            if pattern in raw:
                score += 2
            pat_tokens = set(preprocess(pattern))
            score += len(tokens & pat_tokens)
        if score > best_score:
            best_score  = score
            best_intent = intent

    confidence = min(best_score / 4.0, 1.0)
    return (best_intent, confidence) if best_score > 0 else (None, 0.0)

def generate_response(user_input):
    intent, confidence = classify_intent(user_input)
    if intent and confidence >= 0.25:
        return random.choice(INTENTS[intent]["responses"]), intent
    return random.choice(FALLBACK_RESPONSES), "unknown"

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data       = request.get_json(silent=True) or {}
    user_msg   = (data.get("message") or "").strip()
    session_id = (data.get("session") or "anonymous")

    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    log_message(session_id, "user", user_msg)
    bot_reply, intent = generate_response(user_msg)
    log_message(session_id, "bot", bot_reply, intent)

    return jsonify({"reply": bot_reply, "intent": intent, "session": session_id})

@app.route("/history/<session_id>")
def history(session_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT role, message, intent, timestamp FROM conversations WHERE session=? ORDER BY id",
        (session_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/stats")
def stats():
    conn = get_db()
    total_msgs  = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    total_sess  = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    top_intents = conn.execute(
        "SELECT intent, COUNT(*) as c FROM conversations WHERE role='bot' AND intent IS NOT NULL "
        "GROUP BY intent ORDER BY c DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return jsonify({
        "total_messages": total_msgs,
        "total_sessions": total_sess,
        "top_intents":    [dict(r) for r in top_intents],
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
