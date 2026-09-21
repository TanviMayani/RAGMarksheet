import re
from typing import List, Dict, Any

# Primary marksheet indicators (Performance, scoring, and grading terms)
PRIMARY_MARKSHEET_PATTERNS = [
    r'\bmarksheet\b', r'\bmark\s*sheet\b', r'\bgrade\s*sheet\b', r'\bgradesheet\b',
    r'\bgrade\s*card\b', r'\bstatement\s+of\s+marks\b', r'\bacademic\s+transcript\b',
    r'\btranscript\s+of\s+records\b', r'\bsgpa\b', r'\bcgpa\b', r'\bgpa\b',
    r'\bgrade\s*points?\b', r'\bcredit\s*points?\b', r'\bmarks\s*obtained\b',
    r'\bmax(imum)?\s*marks\b', r'\btotal\s*marks\b', r'\bpassing\s*marks\b',
    r'\btheory\s*marks\b', r'\bpractical\s*marks\b', r'\bgrades?\b', r'\bmarks\b'
]

# Secondary academic context patterns
SECONDARY_PATTERNS = [
    r'\bsemester\b', r'\bsem\b', r'\bsubject\b', r'\bcourse\s*code\b',
    r'\bcourse\s*title\b', r'\benrollment\s*no\b', r'\broll\s*no\b',
    r'\bseat\s*no\b', r'\bexamination\b', r'\bcredits?\b', r'\bbacklog\b',
    r'\btheory\b', r'\bpractical\b'
]

# Patterns strongly indicative of non-marksheet documents (CVs, Resumes, Reports, etc.)
DISQUALIFYING_PATTERNS = [
    r'\bcurriculum\s+vitae\b', r'\bresume\b', r'\bwork\s+experience\b',
    r'\bemployment\s+history\b', r'\bprofessional\s+summary\b',
    r'\bcareer\s+objective\b', r'\btechnical\s+skills\b',
    r'\bskills\s*(&|and)?\s*abilities\b', r'\binternship\s+report\b',
    r'\btraining\s+report\b', r'\bproject\s+report\b', r'\btable\s+of\s+contents\b',
    r'\bdeclaration\b', r'\backnowledg(e)?ment\b', r'\bpersonal\s+details\b',
    r'\blinkedin\.com\b', r'\bgithub\.com\b', r'\bportfolio\b'
]

def is_marksheet(pages_data: List[Dict[str, Any]]) -> bool:
    """
    Strictly validate if the provided pages belong to an actual marksheet or transcript.
    Rejects CVs, Resumes, internship/project reports, and arbitrary PDFs.
    """
    if not pages_data:
        return False

    full_text = " ".join([page.get("text", "").lower() for page in pages_data])
    
    # 1. Reject immediately if document contains CV or Report sections
    for pattern in DISQUALIFYING_PATTERNS:
        if re.search(pattern, full_text):
            return False

    # 2. Check for explicit marksheet title
    explicit_title_patterns = [
        r'\bmarksheet\b', r'\bmark\s*sheet\b', r'\bgrade\s*sheet\b',
        r'\bgradesheet\b', r'\bgrade\s*card\b', r'\bstatement\s+of\s+marks\b',
        r'\bacademic\s+transcript\b', r'\btranscript\s+of\s+records\b'
    ]
    has_explicit_title = any(re.search(p, full_text) for p in explicit_title_patterns)

    # 3. Check primary score/grade keywords (count distinct matches)
    primary_matches = sum(1 for p in PRIMARY_MARKSHEET_PATTERNS if re.search(p, full_text))
    
    # 4. Check secondary academic context keywords
    secondary_matches = sum(1 for p in SECONDARY_PATTERNS if re.search(p, full_text))

    # Verification rules:
    # Rule A: Has an explicit marksheet title AND at least one primary or secondary keyword
    if has_explicit_title and (primary_matches >= 1 or secondary_matches >= 1):
        return True

    # Rule B: Must have at least 2 primary evaluation keywords AND at least 2 secondary academic keywords
    if primary_matches >= 2 and secondary_matches >= 2:
        return True

    return False
