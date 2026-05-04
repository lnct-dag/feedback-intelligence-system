from textblob import TextBlob
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from backend.utils import clean_text

# Initialize VADER
analyzer = SentimentIntensityAnalyzer()

URGENCY_KEYWORDS = [
    'refund', 'complaint', 'not working', 'broken', 'issue', 'fix',
    'urgent', 'error', 'wrong', 'fail', 'cancel', 'service', 'stopped',
    'slow', 'bad', 'worst', 'help', 'emergency', 'asap', 'broken', 'damage',
    'repair', 'stuck', 'waiting'
]

ABUSIVE_KEYWORDS = [
    'idiot', 'stupid', 'dumb', 'bevakuf', 'pagal', 'gadha', 
    'hate', 'kamine', 'dog', 'bastard', 'hell', 'shitty', 
    'fuck', 'fucker', 'motherfucker', 'motherfuker', 'sisterfucker',
    'bitch', 'asshole', 'dick', 'pussy', 'slut', 'bloody'
]

CATEGORY_KEYWORDS = {
    'Support': ['help', 'service', 'support', 'customer', 'assistance', 'working', 'broken', 'stopped', 'repair', 'refund'],
    'Bug': ['error', 'fail', 'bug', 'glitch', 'crash', 'issue', 'wrong', 'not working', 'fail', 'stuck'],
    'Product': ['product', 'quality', 'soft', 'comfortable', 'use', 'design', 'material', 'feature', 'fabric', 'item'],
    'Feedback': ['good', 'bad', 'excellent', 'poor', 'nice', 'improve', 'better', 'love', 'hate', 'suggestion', 'recommend']
}

EMOJI_SENTIMENT = {
    '😍': 1.0, '❤️': 1.0, '🔥': 1.0, '👍': 0.8, '✨': 0.8, '🙌': 0.9, '😂': 0.7, '✅': 0.9,
    '😡': -1.0, '😠': -0.9, '👎': -0.8, '🤮': -1.0, '😭': -0.5, '❌': -0.9, '💩': -1.0, '💔': -0.8,
    '🙄': -0.3, '😕': -0.4, '😫': -0.7, '😒': -0.5
}

EMOJI_URGENCY = ['🚨', '🛑', '⚠️', '🆘', '📍', '🔥', '📢', '⏰']

def analyze_comment(text):
    """
    Enhanced logic to analyze comment:
    - Sentiment (VADER + TextBlob + Emoji)
    - Abusive language detection
    - Urgency keyword + emoji detection
    - Priority scoring
    - Category detection
    """
    original_text = text
    cleaned = clean_text(text).lower()
    
    # 1. Detect Abusive Content (Highest Priority)
    is_abusive = any(word in cleaned for word in ABUSIVE_KEYWORDS)

    # 2. Extract Emojis and Calculate Emoji Sentiment
    emojis_found = [c for c in original_text if c in emoji.EMOJI_DATA]
    emoji_score = 0
    emoji_has_urgency = any(e in EMOJI_URGENCY for e in emojis_found)
    
    for e in emojis_found:
        if e in EMOJI_SENTIMENT:
            emoji_score += EMOJI_SENTIMENT[e]

    # Normalize emoji score
    if len(emojis_found) > 0:
        emoji_score = emoji_score / len(emojis_found)

    # 3. Sentiment Analysis (VADER + TextBlob)
    vs = analyzer.polarity_scores(original_text)
    vader_compound = vs['compound']
    
    blob = TextBlob(cleaned)
    blob_polarity = blob.sentiment.polarity
    
    # Combined Sentiment (Weighting VADER heavily for social media)
    # If emojis are present, they carry a lot of weight
    if len(emojis_found) > 0:
        combined_polarity = (vader_compound * 0.4) + (blob_polarity * 0.1) + (emoji_score * 0.5)
    else:
        combined_polarity = (vader_compound * 0.8) + (blob_polarity * 0.2)

    if is_abusive:
        sentiment = 'Negative'
    elif combined_polarity >= 0.05:
        sentiment = 'Positive'
    elif combined_polarity <= -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'

    # Detect urgency
    is_urgent = any(word in cleaned for word in URGENCY_KEYWORDS) or emoji_has_urgency

    # Priority Scoring
    # 1. User specified high-priority product feedback
    if any(word in cleaned for word in ['soft', 'comfortable', 'comfort', 'softness', 'wantthis', 'high priority']):
        priority = 'High'
    # 2. Abusive Content
    elif is_abusive:
        priority = 'High'
    # 3. Urgent Negative Feedback
    elif sentiment == 'Negative' and is_urgent:
        priority = 'High'
    # 4. Extreme Sentiment or Urgent Emojis
    elif priority_boost := (combined_polarity < -0.5 or (sentiment == 'Negative' and is_urgent) or emoji_has_urgency):
        priority = 'High' if emoji_has_urgency and sentiment == 'Negative' else 'Medium'
    # 5. Moderate Urgency
    elif (sentiment == 'Negative' and not is_urgent) or (sentiment == 'Neutral' and is_urgent):
        priority = 'Medium'
    # 6. Quality/Improvement Suggestions
    elif any(word in cleaned for word in ['improve', 'better', 'quality']):
        priority = 'Medium'
    else:
        priority = 'Low'

    # Category Detection
    category = 'General'
    if any(word in cleaned for word in ['soft', 'comfortable', 'comfort', 'softness', 'product']):
        category = 'Product'
    elif is_abusive:
        category = 'Abusive'
    else:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(word in cleaned for word in keywords):
                category = cat
                break

    return {
        'comment': text,
        'sentiment': sentiment,
        'priority': priority,
        'category': category
    }
