import re

def clean_text(text):
    """
    Basic text cleaning while preserving emojis:
    - Lowercasing
    - Stripping extra whitespace
    - Removing excessive punctuation but keeping characters and emojis
    """
    text = text.lower()
    # Remove some special characters but keep emojis and alphanumeric
    # This is a bit tricky with regex, so we'll just strip some noise
    text = re.sub(r'[^\w\s\u00A9\u00AE\u2000-\u3300\ud83c\ud000-\udbff\udfff\ud83d\ud000-\udbff\udfff\ud83e\ud000-\udbff\udfff]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize(text):
    """
    Simple whitespace tokenization
    """
    return text.split()
