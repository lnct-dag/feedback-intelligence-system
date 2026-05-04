========================================================================
FEEDBACK INTELLIGENCE SYSTEM (FIS) - IMPLEMENTATION GUIDE
========================================================================

This document provides step-by-step instructions on how to set up and
run the Feedback Intelligence System on your local machine.

------------------------------------------------------------------------
1. PREREQUISITES
------------------------------------------------------------------------
- Python 3.8 or higher installed.
- Internet connection (for installing dependencies and NLP models).

------------------------------------------------------------------------
2. INSTALLATION STEPS
------------------------------------------------------------------------
Step 1: Open your terminal/command prompt in the project folder.

Step 2: Install required Python libraries:
   pip install -r requirements.txt

Step 3: Download NLP data (Required for AI analysis):
   python -m textblob.download_corpora
   python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"

------------------------------------------------------------------------
3. CONFIGURING ENVIRONMENT (.env)
------------------------------------------------------------------------
The system uses an '.env' file to store sensitive information like 
Instagram credentials.

1. Locate the file named '.env' in the root directory.
2. Open it with a text editor (Notepad, VS Code, etc.).
3. Update the following fields:
   - INSTA_USER: Your Instagram username.
   - INSTA_PASS: Your Instagram password.
   - INSTA_SESSIONID: (Optional) Your browser session ID to avoid login 
     checks.

Note: If you don't provide Instagram credentials, the "Instagram Sync" 
feature will not work, but the rest of the dashboard will function.

------------------------------------------------------------------------
4. RUNNING THE SYSTEM
------------------------------------------------------------------------
Step 1: Start the Flask Backend:
   python app.py

Step 2: Access the Dashboard:
   Open your web browser and go to: http://127.0.0.1:5000

------------------------------------------------------------------------
5. USAGE TIPS
------------------------------------------------------------------------
- Manual Entry: Use this to test individual comments.
- Instagram Sync: Paste a public Reel URL to fetch live comments.
- Dashboard: View analytics, filter by sentiment, and export data to CSV.

------------------------------------------------------------------------
CONTACT / SUPPORT
------------------------------------------------------------------------
Created By: 
- Divyansh Agarwal
- Heeral Bhadoria
(LNCT University, Bhopal)

Copyright (c) 2026 Feedback Intelligence System
========================================================================
