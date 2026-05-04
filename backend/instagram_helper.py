import os
import instaloader
import re
import time

# Credentials
INSTA_USER = os.getenv('INSTA_USER', '')
INSTA_PASS = os.getenv('INSTA_PASS', '')

import browser_cookie3

from instagrapi import Client
import json

import random

def _generate_simulated_comments():
    """Generates random mock comments for offline/simulation mode."""
    simulated_texts = [
        "omg this is fire 🔥",
        "worst experience i've ever had. never buying again.",
        "can someone help me with a refund? urgent!",
        "the fabric is super soft, love the quality!",
        "it crashed immediately after I installed it :(",
        "10/10 would recommend to anyone seeing this",
        "you idiot, why is the support not responding??",
        "so comfortable! best purchase of the year.",
        "delivery was 3 days late, very unhappy.",
        "wait how do I use this feature?",
        "absolute trash 👎"
    ]
    comments = []
    # Generate random number of simulated comments
    for i in range(random.randint(5, 10)):
        comments.append({
            'text': random.choice(simulated_texts),
            'owner': f"simulated_user_{random.randint(100,999)}",
            'created_at': 'now'
        })
    return {
        'comments': comments,
        'shortcode': 'simulated_post',
        'simulated': True
    }


def fetch_instagram_comments(post_url):
    """
    PRODUCTION ENGINE: Includes Proxy support to bypass IP blacklists.
    Fully capable of falling back to SIMULATION/OFFLINE mode.
    """
    start_time = time.time()
    user = os.getenv('INSTA_USER', '').strip().replace('"', '')
    pw = os.getenv('INSTA_PASS', '').strip().replace('"', '')
    session_id = os.getenv('INSTA_SESSIONID', '').strip().replace('"', '')
    proxy = os.getenv('INSTA_PROXY', '').strip() 

    # --- SIMULATION MODE (No Credentials) ---
    if not user and not pw and not session_id:
        print(f"\n--- [SIMULATION] No Credentials Provided. Working Offline. ---")
        return _generate_simulated_comments()

    # Prevent infinite buffering/hanging if proxy points back to our own Flask app
    if proxy and ('127.0.0.1:5000' in proxy or 'localhost:5000' in proxy):
        print("--- [WARNING] Ignoring INSTA_PROXY because it points to the Flask app. This causes infinite buffering! ---")
        proxy = ""

    cl = Client()
    # Apply a hard limit on request wait times to prevent permanent buffering on dead network conditions
    cl.request_timeout = 15 

    if proxy:
        cl.set_proxy(proxy)
    
    # Clean URL
    post_url = post_url.split('?')[0].rstrip('/')
    print(f"\n--- [PRODUCTION] INTEGRATION START: {post_url} ---")

    try:
        authenticated = False
        
        # --- PHASE 0: DIRECT SESSION INJECTION (The Nuclear Option) ---
        if session_id:
            print("--- [AUTH] Attempting login via Session ID... ---")
            try:
                cl.login_by_sessionid(session_id)
                print("--- [AUTH SUCCESS] Production Session Active via ID ---")
                authenticated = True
            except Exception as session_err:
                print(f"--- [AUTH ERROR] Direct Session ID failed: {session_err} ---")
                print("--- [AUTH] Falling back to automated browser verification... ---")
        
        # --- PHASE 1: HYBRID LOGIN (Fallback) ---
        if not authenticated:
            if not user or not pw:
                return {'error': "Session ID in .env has expired and missing user/pass. Please get a new one from your browser cookies or provide INSTA_USER/PASS."}

            session_file = os.path.join(os.path.dirname(__file__), "..", f"settings_{user}.json")
            
            # --- Continue with previous Hybrid logic ---
        
            # 1. Authenticate with Hybrid Logic (Credentials -> Browser Fallback)
            try:
                if os.path.exists(session_file):
                    cl.load_settings(session_file)
                    try:
                        cl.login(user, pw)
                        print(f"--- [AUTH] Advanced Session Loaded for {user} ---")
                    except Exception:
                        pass # proceed to fallback below
                
                # Check if we are really logged in or not
                try:
                    user_id = cl.user_id_from_username(user)
                    if not user_id: raise Exception("Not logged in.")
                except Exception:
                    print(f"--- [AUTH] Initializing new session for {user}... ---")
                    try:
                        # Attempt standard login
                        cl.login(user, pw)
                        cl.dump_settings(session_file)
                        print("--- [AUTH] Standard Login Successful. ---")
                    except Exception as e:
                        # BLOCK DETECTED -> TRY DEEP BROWSER BYPASS
                        print(f"--- [AUTH] Standard Login Blocked... Attempting Deep Browser Bypass. ---")
                        try:
                            # Attempt to load from any available browser
                            old_proxy = proxy
                            cl.set_proxy("") 
                            success = False
                            
                            # List of browsers to check
                            browsers = ['chrome', 'edge', 'brave', 'opera', 'firefox']
                            for b_name in browsers:
                                try:
                                    print(f"--- [AUTH] Checking {b_name} for session... ---")
                                    if b_name == 'chrome': cj = browser_cookie3.chrome(domain_name='instagram.com')
                                    elif b_name == 'edge': cj = browser_cookie3.edge(domain_name='instagram.com')
                                    elif b_name == 'firefox': cj = browser_cookie3.firefox(domain_name='instagram.com')
                                    elif b_name == 'brave': cj = browser_cookie3.brave(domain_name='instagram.com')
                                    elif b_name == 'opera': cj = browser_cookie3.opera(domain_name='instagram.com')
                                    
                                    cookie_dict = cj.get_dict()
                                    if 'sessionid' in cookie_dict:
                                        cl.set_settings({})
                                        cl.set_cookies(cookie_dict)
                                        print(f"--- [AUTH SUCCESS] Found valid session in {b_name}! ---")
                                        success = True
                                        break
                                except Exception:
                                    continue
                            
                            if old_proxy: cl.set_proxy(old_proxy)
                            
                            if not success:
                                raise Exception("Could not find an active Instagram session in any of your browsers.")
                            
                            cl.dump_settings(session_file)
                        except Exception as bypass_err:
                            print(f"--- [AUTH BYPASS FAILED] {bypass_err} ---")
                            return {'error': f"Access Denied: Please log in to Instagram.com in Chrome or Edge, then REFRESH your feed before trying again."}
            except Exception as login_err:
                err_msg = str(login_err)
                print(f"--- [LOGIN FAILED] {err_msg} ---")
                if "challenge" in err_msg.lower():
                    return {'error': "Initial Setup Required: Instagram sent a security code to your email/phone. Please log in to Instagram.com once on this computer to confirm 'This was me'."}
                return {'error': f"Connection Failed: {err_msg}"}

        # 2. Convert URL to Media ID (Numeric PK)
        try:
            print(f"--- [DATA] Resolving Media ID for: {post_url} ---")
            # robustly extract shortcode if possible
            shortcode_match = re.search(r'(?:p|reel|tv|v)/([^/?#&]+)', post_url)
            if shortcode_match:
                shortcode = shortcode_match.group(1)
                media_pk = cl.media_pk_from_code(shortcode)
            else:
                media_pk = cl.media_pk_from_url(post_url)
        except Exception as id_err:
            print(f"--- [ID ERROR] {id_err} ---")
            return {'error': f"Could not find post. Please check the URL format."}

        # 3. Pull Data
        print(f"--- [DATA] Pulling real comments for ID: {media_pk} ---")
        try:
            comments = []
            try:
                # FAST MODE: Skip media_info and drop amount to 20 for single-request chunking
                insta_comments = cl.media_comments(media_pk, amount=20)
                for comment in insta_comments:
                    clean_text = comment.text.strip()
                    if not clean_text:
                        continue
                    
                    comments.append({
                        'text': clean_text,
                        'owner': comment.user.username,
                        'created_at': str(comment.created_at_utc)
                    })
            except Exception as comm_err:
                if "404" in str(comm_err) or "not found" in str(comm_err).lower():
                    print("--- [INFO] Comments are likely disabled or restricted on this post. ---")
                elif "login" in str(comm_err).lower():
                    raise comm_err
                else:
                    raise comm_err
                
            fetch_time = round(time.time() - start_time, 2)
            return {'comments': comments, 'shortcode': str(media_pk), 'fetch_time': fetch_time}
        except Exception as data_err:
            print(f"--- [DATA ERROR] {data_err} ---")
            err_msg = str(data_err).lower()
            if "login_required" in err_msg or "login" in err_msg:
                return {'error': "Session Expired: The automated login session has expired. Please log into Instagram on this browser manually to refresh it."}
            return {'error': f"Access restricted: Instagram is blocking access to this specific post's comments (it may be private or comments are disabled)."}
        
    except Exception as e:
        error_msg = str(e)
        print(f"--- [ENGINE ERROR] {error_msg} ---")
        # Check if the error is due to being completely offline or network timeout
        if any(err in error_msg.lower() for err in ['connection', 'timeout', 'resolve host', 'network', 'max retries exceeded']):
            print("\n--- [NETWORK ERROR] Completely offline. Failing gracefully to Simulation Mode. ---")
            return _generate_simulated_comments()
        return {'error': error_msg}
