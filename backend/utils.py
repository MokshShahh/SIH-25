def time_to_minutes(t: str, allow_midnight=True) -> int:
    """
    Convert HH:MM:SS or HH:MM string to minutes since midnight.
    """
    if not t:
        return -1

    t = str(t).strip().upper()
    if t in {"NA", "N/A", "", "NULL", "NONE"}:
        return -1

    try:
        parts = t.split(":")
        if len(parts) == 2:  # HH:MM
            h, m = map(int, parts)
        elif len(parts) >= 3:  # HH:MM:SS
            h, m = map(int, parts[:2])
        else:
            return -1

        if not (0 <= h <= 23 and 0 <= m <= 59):
            return -1
        
        if h == 0 and m == 0 and not allow_midnight:
            return -1

        return h * 60 + m

    except (ValueError, TypeError):
        return -1
