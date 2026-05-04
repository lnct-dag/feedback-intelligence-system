import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from backend.model import analyze_comment
from backend.instagram_helper import fetch_instagram_comments

app = Flask(__name__, static_folder='../frontend')

@app.errorhandler(500)
def handle_500_error(e):
    return jsonify({"error": "Internal Server Error: Check if all requirements (instagrapi, etc.) are installed and the backend is restarted."}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": f"Backend Crash: {str(e)}"}), 500

# Define database path relative to workspace
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../database/comments.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '../database/schema.sql')

import threading
import time

def init_db():
    """
    Initialize SQLite database from schema.sql
    """
    if not os.path.exists(DATABASE_PATH):
        # Create database file if it doesn't exist
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        with sqlite3.connect(DATABASE_PATH) as conn:
            with open(SCHEMA_PATH, 'r') as f:
                conn.executescript(f.read())
            conn.commit()
    
    # Always ensure tracked_urls exists
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tracked_urls (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE NOT NULL, last_sync DATETIME DEFAULT CURRENT_TIMESTAMP)")
        
        # Check if user_handle column exists in comments, if not, add it
        cursor = conn.execute("PRAGMA table_info(comments)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'user_handle' not in columns:
            print("--- MIGRATING: Adding 'user_handle' to comments table ---")
            conn.execute("ALTER TABLE comments ADD COLUMN user_handle TEXT DEFAULT 'Anonymous'")
        
        conn.commit()
    print(f"Database initialized at: {DATABASE_PATH}")

# Call init_db immediately to ensure DB exists during registration or first boot
init_db()

# Serve Frontend
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('../frontend', path)

# API Endpoints
@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Analyze comment and store in database
    """
    data = request.json
    comment_text = data.get('comment_text')
    if not comment_text:
        return jsonify({'error': 'Comment text is required'}), 400

    # Perform analysis
    result = analyze_comment(comment_text)

    # Store in DB
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comments (user_handle, comment_text, sentiment, priority, category) VALUES (?, ?, ?, ?, ?)",
                ('Direct Entry', result['comment'], result['sentiment'], result['priority'], result['category'])
            )
            conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
        return jsonify({'error': 'Failed to save to database'}), 500

    return jsonify(result)

@app.route('/api/comments', methods=['GET'])
def get_comments():
    """
    Fetch all comments from database
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comments ORDER BY timestamp DESC")
            rows = cursor.fetchall()

            comments = []
            for row in rows:
                row_dict = dict(row)
                comments.append({
                    'id': row_dict['id'],
                    'user_handle': row_dict.get('user_handle', 'Anonymous'),
                    'comment_text': row_dict['comment_text'],
                    'sentiment': row_dict['sentiment'],
                    'priority': row_dict['priority'],
                    'category': row_dict.get('category', 'General'),
                    'timestamp': row_dict['timestamp']
                })
        return jsonify(comments)
    except Exception as e:
        print(f"DB Error: {e}")
        return jsonify({'error': 'Failed to fetch from database'}), 500

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """
    Delete a comment by ID
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({'error': 'Comment not found'}), 404
        return jsonify({'message': 'Comment deleted successfully'})
    except Exception as e:
        print(f"DB Error: {e}")
        return jsonify({'error': 'Failed to delete from database'}), 500

@app.route('/api/comments/clear', methods=['DELETE'])
def clear_comments():
    """
    Delete all comments from the database
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM comments")
            conn.commit()
        return jsonify({'message': 'All comments cleared successfully'})
    except Exception as e:
        print(f"DB Error: {e}")
        return jsonify({'error': 'Failed to clear database'}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """
    Fetch summary stats
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            stats = {
                'total': 0,
                'sentiments': {'Positive': 0, 'Neutral': 0, 'Negative': 0},
                'priorities': {'High': 0, 'Medium': 0, 'Low': 0},
                'categories': {}
            }

            cursor.execute("SELECT sentiment, priority, category, count(*) as count FROM comments GROUP BY sentiment, priority, category")
            rows = cursor.fetchall()
            
            for row in rows:
                count = row['count']
                stats['total'] += count
                stats['sentiments'][row['sentiment']] = stats['sentiments'].get(row['sentiment'], 0) + count
                stats['priorities'][row['priority']] = stats['priorities'].get(row['priority'], 0) + count
                cat = row['category'] if row['category'] else 'General'
                stats['categories'][cat] = stats['categories'].get(cat, 0) + count

        return jsonify(stats)
    except Exception as e:
        print(f"DB Error: {e}")
        return jsonify({'error': 'Failed to fetch analytics'}), 500

@app.route('/api/import/instagram', methods=['POST'])
def import_instagram():
    """
    Import comments from a public Instagram post/reel
    """
    data = request.json
    post_url = data.get('post_url')
    if not post_url:
        return jsonify({'error': 'Instagram URL is required'}), 400

    result = fetch_instagram_comments(post_url)
    
    if 'error' in result and 'comments' not in result:
        return jsonify({'error': f"Could not fetch: {result['error']}"}), 500

    comments_data = result['comments']
    imported_count = 0
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            # Register URL for tracking if not exists
            cursor.execute("INSERT OR IGNORE INTO tracked_urls (url) VALUES (?)", (post_url,))
            
            if not comments_data:
                return jsonify({
                    'message': 'No comments found on this post. It might be private or require login credentials.',
                    'count': 0,
                    'simulated': result.get('simulated', False)
                })

            for c in comments_data:
                # Check for duplicate
                cursor.execute("SELECT id FROM comments WHERE user_handle = ? AND comment_text = ?", (c['owner'], c['text']))
                if cursor.fetchone():
                    continue

                # Analyze and Store
                analysis = analyze_comment(c['text'])
                cursor.execute(
                    "INSERT INTO comments (user_handle, comment_text, sentiment, priority, category) VALUES (?, ?, ?, ?, ?)",
                    (c['owner'], analysis['comment'], analysis['sentiment'], analysis['priority'], analysis['category'])
                )
                imported_count += 1
            conn.commit()
            
        status_msg = f'Successfully synced {imported_count} new comments'
        if result.get('simulated'):
            status_msg += " (Simulation Mode Active)"
        elif imported_count == 0 and len(comments_data) > 0:
            status_msg = "All fetched comments were already in the database."

        return jsonify({
            'message': status_msg,
            'count': imported_count,
            'total_fetched': len(comments_data),
            'fetch_time': result.get('fetch_time', 0),
            'simulated': result.get('simulated', False)
        })
    except Exception as e:
        print(f"Import Error: {e}")
        return jsonify({'error': 'Failed to save imported comments'}), 500

# Global variable to track last sync time
last_sync_time = None

@app.route('/api/sync/status', methods=['GET'])
def get_sync_status():
    """
    Returns the status of the background sync worker
    """
    return jsonify({
        'last_sync': last_sync_time,
        'status': 'Running' if last_sync_time else 'Waiting'
    })

def sync_worker():
    """
    Background worker that refreshes all tracked Instagram URLs every 2 minutes.
    """
    global last_sync_time
    print("--- Background Sync Worker Started ---")
    while True:
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM tracked_urls")
                urls = [row[0] for row in cursor.fetchall()]
            
            if urls:
                print(f"--- Auto-syncing {len(urls)} Instagram URLs ---")
                for url in urls:
                    res = fetch_instagram_comments(url)
                    if 'comments' in res:
                        with sqlite3.connect(DATABASE_PATH) as conn:
                            cursor = conn.cursor()
                            new_count = 0
                            for c in res['comments']:
                                cursor.execute("SELECT id FROM comments WHERE user_handle = ? AND comment_text = ?", (c['owner'], c['text']))
                                if cursor.fetchone(): continue
                                
                                analysis = analyze_comment(c['text'])
                                cursor.execute(
                                    "INSERT INTO comments (user_handle, comment_text, sentiment, priority, category) VALUES (?, ?, ?, ?, ?)",
                                    (c['owner'], analysis['comment'], analysis['sentiment'], analysis['priority'], analysis['category'])
                                )
                                new_count += 1
                            
                            # Update last sync timestamp in DB
                            cursor.execute("UPDATE tracked_urls SET last_sync = CURRENT_TIMESTAMP WHERE url = ?", (url,))
                            conn.commit()
                            if new_count > 0:
                                print(f"--- Synced {new_count} new comments from {url} ---")
            
            last_sync_time = time.strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            print(f"Sync Worker Error: {e}")
        
        time.sleep(120) # Wait 2 minutes

if __name__ == '__main__':
    # Initialize DB during main startup as well just in case
    init_db()
    
    # Start background sync thread
    daemon = threading.Thread(target=sync_worker, daemon=True)
    daemon.start()
    
    app.run(debug=True, port=5000, use_reloader=False) # Disable reloader to prevent double thread

