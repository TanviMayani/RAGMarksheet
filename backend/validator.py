from typing import List, Dict, Any
import re

# Common terms found in marksheets/transcripts
MARKSHEET_KEYWORDS = [
    "student", "name", "subject", "marks", "grade", "semester",
    "result", "examination", "sgpa", "cgpa", "university",
    "enrollment", "roll", "percentage", "total", "credit", "course",
    "transcript", "academic", "degree", "bachelor", "master"
]

def is_marksheet(pages_data: List[Dict[str, Any]]) -> bool:
    """
    Validate if the provided pages likely belong to a marksheet.
    Tolerates OCR errors by requiring only a small number of keyword matches.
    """
    full_text = " ".join([page.get("text", "").lower() for page in pages_data])
    
    # We want at least a few keywords to match to be somewhat confident
    match_count = 0
    for keyword in MARKSHEET_KEYWORDS:
        if keyword in full_text:
            match_count += 1
            
    # Require at least 2 distinct marksheet-related keywords
    if match_count >= 2:
        return True
        
    # Also check if it's densely packed with numbers (grades/marks)
    # A simple heuristic: if more than 5% of characters are digits
    total_chars = len(full_text)
    if total_chars > 0:
        digit_count = sum(c.isdigit() for c in full_text)
        if (digit_count / total_chars) > 0.05:
            return True
            
    return False
