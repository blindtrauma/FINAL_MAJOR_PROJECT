# app/utils/helpers.py - General utility functions

import time
import datetime

def generate_timestamp() -> float:
    """Generates a current timestamp (seconds since epoch)."""
    return time.time()

def format_timestamp(timestamp: float, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Formats a timestamp into a human-readable string."""
    dt_object = datetime.datetime.fromtimestamp(timestamp)
    return dt_object.strftime(format_string)

# Add other helper functions as needed, e.g., for string manipulation, data validation helpers, etc.

# def clean_text(text: str) -> str:
#     """Basic text cleaning (remove excessive whitespace, etc.)."""
#     import re
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text