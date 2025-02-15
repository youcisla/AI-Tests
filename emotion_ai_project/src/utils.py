import re

def clean_text(text):
    """
    Lowercase the text and remove URLs and non-alphabetic characters.
    """
    text = text.lower()
    text = re.sub(r'http\S+', '', text)  # Remove URLs
    text = re.sub(r'[^a-z\s]', '', text)  # Remove punctuation and numbers
    return text.strip()
