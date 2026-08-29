from typing import List, Dict, Any
import re

def calculate_average(values: List[float]) -> float:
    """Safely calculate average of a list of numbers."""
    if not values:
        return 0.0
    return sum(values) / len(values)

def calculate_percentage(obtained: float, total: float) -> float:
    """Safely calculate percentage."""
    if total <= 0:
        return 0.0
    return (obtained / total) * 100.0

def extract_numbers(text: str) -> List[float]:
    """Helper to extract numbers from text for calculation."""
    # Find all numbers (integers or decimals)
    matches = re.findall(r'-?\d+\.?\d*', text)
    return [float(m) for m in matches]
