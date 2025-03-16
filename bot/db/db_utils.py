def streak_to_points(streak: str) -> int:
    """
    Calculates points for a streak based on:
    - A streak is broken by two consecutive '0's.
    - Streaks are evaluated in 2-day windows (only one '1' needed per 2 days).
    - A consecutive '1' does not add extra points.

    Args:
        streak (str): A string of '1's and '0's representing user activity.

    Returns:
        int: Total streak points.
    """
    segments = streak.split("00")
    total_points = 0
    
    for segment in segments:
        if not segment:  # Skip empty segments.
            continue
        # Calculate the number of 2-day windows in this segment.
        # Using ceiling division: (len(segment) + 1) // 2
        windows = (len(segment) + 1) // 2
        
        # The points for this segment is the triangular number T(windows)
        segment_points = windows * (windows + 1) // 2
        
        total_points += segment_points
    
    return total_points