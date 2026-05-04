# 🚀 Feedback Intelligence System (FIS)

An advanced, AI-powered full-stack dashboard designed to classify, prioritize, and manage user feedback with high precision. Built with a focus on modern aesthetics (Glassmorphism) and robust backend analysis.

---

## 🌟 Key Features

### 🤖 AI-Driven Intelligence
- **Deep Sentiment Analysis**: Uses NLP (Natural Language Processing) to classify comments into **Positive**, **Neutral**, or **Negative**.
- **Emoji Insight**: Analyzes emojis (e.g., 🔥, 😍, 😡, 🤮) to weigh sentiment more accurately for social media contexts.
- **Urgency Detection**: Detects critical keywords (e.g., *ASAP*, *refund*, *broken*) and urgency emojis (e.g., 🚨, 🆘) to flag burning issues.
- **Abusive Content Filtering**: Automatically detects profanity and abusive terms (including Hinglish/Hindi like *bevakuf*, *pagal*), flagging them as **High Priority** for review.
- **Auto-Categorization**: Dynamically tags feedback into categories like **Support**, **Bug**, **Product**, **Feedback**, or **Abusive**.

### 📱 Social Media Integration
- **Instagram Sync**: Import comments directly from public Instagram Reels or Posts by simply pasting the URL. No API setup required for public data.

### 📊 Management Dashboard
- **Analytics Summary**: Real-time cards showing total volume, sentiment distribution, and priority counts.
- **Advanced Filtering**: Search through comments by text and filter by specific sentiment or priority levels.
- **Data Export**: Download your entire analyzed dataset as a **CSV** file for external reporting.
- **CRUD Controls**: Delete individual comments or completely wipe the database using the **Clear All** feature.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask (REST API)
- **NLP/AI**: TextBlob, Emoji Python
- **Database**: SQLite (Relational Storage)
- **Frontend**: Vanilla JS (ES6+), Bootstrap 5 (Styling), FontAwesome (Icons)
- **Social Logic**: Instaloader (Scraping)

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8 or higher installed on your system.

### 2. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Initialize AI Models
Download the necessary NLP corpora and lexicons:
```bash
python -m textblob.download_corpora
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"
```

### 4. Configuration (.env)
Create a `.env` file in the root directory (you can copy `.env.example` as a template):

```bash
# Instagram Credentials
INSTA_USER="your_username"
INSTA_PASS="your_password"
INSTA_SESSIONID="your_session_id" # Optional
```

### 5. Running the Application
Launch the Flask development server from the root directory:
```bash
python app.py
```

### 6. Accessing the UI
Open your browser and visit:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📖 Usage Guide

### Manual Entry
1. Navigate to the **Manual Entry** tab.
2. Type in your comment or click "Load Sample" for a demonstration.
3. Click "Analyze & Store" to see it instantly appear in the dashboard.

### Instagram Import
1. Navigate to the **Instagram Sync** tab.
2. Paste the URL of a public Reel or Post (e.g., `https://www.instagram.com/reels/C5-zXXXXXXXX/`).
3. Click **Fetch & Analyze**. The system will grab the latest comments and run the AI engine on them.

### Priority Matrix
- **🔴 High**: Negative sentiments with detected urgency OR identified Abusive content.
- **🟡 Medium**: Negative feedback without urgency OR Neutral feedback with a suggestion or concern (e.g., "improvement").
- **🟢 Low**: Positive feedback or general neutral statements.

---

## 📂 Project Structure

- `backend/`: API routes (`app.py`), AI Logic (`model.py`), and helper functions.
- `frontend/`: UI files (`index.html`, `style.css`, `script.js`).
- `database/`: Database schema and persistence files.
- `requirements.txt`: List of Python dependencies.

---

### 🎓 Created By:
**Divyansh Agarwal** (LNCEBTC11079), **Heeral Bhadoria** (LNCEBTC11089)  
*LNCT University, Bhopal*

&copy; 2026 Feedback Intelligence System