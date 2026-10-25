"""
AIAG & VDA FMEA Handbook 1st Edition (2019)
Action Priority (AP) calculation engine.
Table DFMEA AP (Action Priority) Table B.
"""

def calculate_rpn(severity: int, occurrence: int, detection: int) -> int:
    """Calculate traditional Risk Priority Number (RPN = S * O * D)."""
    if not (1 <= severity <= 10 and 1 <= occurrence <= 10 and 1 <= detection <= 10):
        raise ValueError(f"S, O, D must be between 1 and 10. Got S={severity}, O={occurrence}, D={detection}")
    return severity * occurrence * detection

def calculate_action_priority(severity: int, occurrence: int, detection: int) -> str:
    """
    Calculate Action Priority (AP: 'High', 'Medium', 'Low') strictly based on
    AIAG & VDA FMEA 1st Edition (2019) Standard Table B.
    Validates range 1-10 for Severity, Occurrence, Detection.
    """
    if not (isinstance(severity, int) and isinstance(occurrence, int) and isinstance(detection, int)):
        raise TypeError("Severity, Occurrence, and Detection must be integers.")
    if not (1 <= severity <= 10 and 1 <= occurrence <= 10 and 1 <= detection <= 10):
        raise ValueError(f"S, O, D must be integers in range [1, 10]. Got S={severity}, O={occurrence}, D={detection}")

    s, o, d = severity, occurrence, detection

    # 1. Severity 9-10 (Very High - Safety / Regulatory)
    if s in (9, 10):
        if o in (8, 9, 10):
            return "High"
        elif o in (6, 7):
            return "High"
        elif o in (4, 5):
            if d >= 7:
                return "High"
            elif d >= 2:
                return "Medium"
            else:  # d == 1
                return "Low"
        elif o in (2, 3):
            if d >= 5:
                return "Medium"
            else:  # d <= 4
                return "Low"
        else:  # o == 1
            return "Low"

    # 2. Severity 7-8 (High - Loss of primary vehicle function)
    elif s in (7, 8):
        if o in (8, 9, 10):
            return "High"
        elif o in (6, 7):
            if d >= 5:
                return "High"
            else:  # d <= 4
                return "Medium"
        elif o in (4, 5):
            if d >= 7:
                return "High"
            elif d >= 2:
                return "Medium"
            else:  # d == 1
                return "Low"
        elif o in (2, 3):
            if d >= 7:
                return "Medium"
            else:  # d <= 6
                return "Low"
        else:  # o == 1
            return "Low"

    # 3. Severity 4-6 (Moderate - Degraded primary function)
    elif s in (4, 5, 6):
        if o in (8, 9, 10):
            if d >= 7:
                return "High"
            else:  # d <= 6
                return "Medium"
        elif o in (6, 7):
            if d >= 5:
                return "Medium"
            else:  # d <= 4
                return "Low"
        elif o in (4, 5):
            if d >= 7:
                return "Medium"
            else:  # d <= 6
                return "Low"
        else:  # o <= 3
            return "Low"

    # 4. Severity 2-3 (Low - Minor defect noticeable by most customers)
    elif s in (2, 3):
        if o in (8, 9, 10) and d >= 7:
            return "Medium"
        return "Low"

    # 5. Severity 1 (Very Low - No discernible effect)
    else:  # s == 1
        return "Low"
