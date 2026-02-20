import streamlit as st
import streamlit as st
import openai
import smtplib
import pandas as pd
import json
import os
import time
import tempfile
import smtplib
from email.message import EmailMessage
from openai import OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# ================== CONFIG ==================
openai.api_key = st.secrets["OPENAI_API_KEY"]
SMTP_EMAIL = "intelligentsystems512@gmail.com"
SMTP_PASSWORD = "ztetdzmejhxjjcfi"

LOG_FILE = "feedback_logs.json"


# ================== UI THEME ==================
st.set_page_config(page_title="AI Feedback Agent", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #fde7e7;
}
button {
    background-color: black !important;
    color: white !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ================== HELPERS ==================
def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

from email.message import EmailMessage
import smtplib

def send_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = st.secrets["SMTP_EMAIL"]
        msg["To"] = to_email
        msg["Subject"] = subject

        # THIS enables UTF-8 safely
        msg.set_content(body, charset="utf-8")

        with smtplib.SMTP_SSL(
            st.secrets["SMTP_HOST"],
            st.secrets["SMTP_PORT"],
            timeout=20
        ) as server:
            server.login(
                st.secrets["SMTP_EMAIL"],
                st.secrets["SMTP_PASSWORD"]
            )
            server.send_message(msg)

        return "Sent"

    except Exception as e:
        return f"Failed: {e}"

def transcribe_audio(path):
    with open(path, "rb") as f:
        return client.audio.transcriptions.create(
            file=f,
            model="whisper-1"
        ).text

def analyze_sentiment(text):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify sentiment as Positive or Negative."},
            {"role": "user", "content": text}
        ],
        max_tokens=5
    )
    return resp.choices[0].message.content.strip()

# ================== SESSION ==================
if "page" not in st.session_state:
    st.session_state.page = "home"

# ================== NAV ==================
col1, col2 = st.columns([6, 2])
with col2:
    if st.button("Customer Feedback"):
        st.session_state.page = "customer"
    if st.button("Operator Login"):
        st.session_state.page = "operator_login"

# ================== LANDING ==================
if st.session_state.page == "home":
    st.markdown("## 📡 Welcome to SmartCare AI")

    st.markdown("""
### Experience the future of customer feedback 🚀

**SmartCare AI** is an intelligent, voice-driven customer feedback platform designed for modern telecom providers.

We help organizations **listen**, **understand**, and **act** on customer emotions in real time — not just numbers, but real voices.

---

### 🔍 What SmartCare AI does

🎙️ **Voice-Based Feedback**  
Customers can simply speak their experience — no forms, no typing, no friction.

🧠 **AI-Powered Sentiment Analysis**  
Our AI analyzes the feedback instantly to detect:
- Positive sentiment 😊  
- Negative sentiment 😟  
- Churn risk indicators ⚠️  

📩 **Automated Customer Communication**  
Based on sentiment:
- Positive feedback → Thank-you acknowledgement email  
- Negative feedback → Retention / offer email sent instantly  

📊 **Operator Dashboard**  
Operators get a clear, structured view of:
- Customer email
- Sentiment
- Full transcription
- Email status
- Resolution status (In Progress / Yes / No)
- Historical logs for audit & follow-up

---

### 💡 Why telecom teams love this

✔ Faster issue identification  
✔ Reduced churn  
✔ Better customer satisfaction  
✔ No manual call reviews  
✔ Actionable insights, not raw data  

---

### 🧭 How to get started

👉 **Customer Feedback**  
Record your feedback in under 10 seconds — our AI handles the rest.

👉 **Operator Login**  
Monitor feedback, track resolution status, and manage customer issues efficiently.

---

💬 *“Because every customer voice matters.”*  
""")

# ================== CUSTOMER ==================
elif st.session_state.page == "customer":
    st.header("🎤 Customer Feedback")

    email = st.text_input("Enter your email")

    if email:
        audio = st.audio_input("Record feedback (auto-stops at 10 seconds)")

        if audio:
            with st.spinner("Processing..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio.read())
                    tmp_path = tmp.name

                text = transcribe_audio(tmp_path)
                sentiment = analyze_sentiment(text)

                if sentiment.lower() == "negative":
                    mail_status = send_email(
                        email,
                        "We’d love to make this right",
                        "Thanks for your feedback. Here’s a special offer for you - 10 percent discount on your next bill",
                        "Incase of any service issues we will be working on it proactively...."
                    )
                else:
                    mail_status = send_email(
                        email,
                        "Thank you!",
                        "We appreciate your positive feedback."
                    )

                logs = load_logs()
                logs.append({
                    "email": email,
                    "sentiment": sentiment,
                    "transcription": text,              # ✅ NEW
                    "mail_status": mail_status,
                    "resolved_status": "In Progress",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                save_logs(logs)

                st.success(f"Feedback submitted")

    if st.button("⬅ Back"):
        st.session_state.page = "home"

# ================== OPERATOR LOGIN ==================
elif st.session_state.page == "operator_login":
    st.header("🔐 Operator Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == "admin" and p == "admin":
            st.session_state.page = "operator"
        else:
            st.error("Invalid credentials")

    if st.button("⬅ Back"):
        st.session_state.page = "home"

# ================== OPERATOR DASHBOARD ==================
elif st.session_state.page == "operator":
    st.header("🛠 Operator Dashboard")

    logs = load_logs()
    if not logs:
        st.info("No feedback yet.")
    else:
        df = pd.DataFrame(logs)

        for col in ["email", "sentiment", "transcription", "mail_status", "resolved_status", "timestamp"]:
            if col not in df.columns:
                df[col] = ""

        df["resolved_status"] = df["resolved_status"].fillna("In Progress")
        df["mail_status"] = df["mail_status"].fillna("Not Sent")

        edited_df = st.data_editor(
            df[[
                "email",
                "sentiment",
                "transcription",     # ✅ SHOWN IN TABLE
                "mail_status",
                "resolved_status",
                "timestamp"
            ]],
            column_config={
                "resolved_status": st.column_config.SelectboxColumn(
                    "Resolved",
                    options=["In Progress", "Yes", "No"],
                    required=True
                )
            },
            disabled=["email", "sentiment", "transcription", "mail_status", "timestamp"],
            use_container_width=True,
            key="operator_table"
        )

        for i in range(len(logs)):
            logs[i]["resolved_status"] = edited_df.loc[i, "resolved_status"]

        save_logs(logs)

    if st.button("⬅ Logout"):
        st.session_state.page = "home"
