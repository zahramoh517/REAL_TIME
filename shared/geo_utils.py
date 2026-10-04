"""
Small geo/time helpers shared across the pipeline.
"""

from math import radians, sin, cos, sqrt, atan2


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in kilometers."""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def get_latest_system_timestamp(db_connection):
    """
    Returns the most recent event timestamp across the whole system.
    """
    query = "SELECT MAX(timestamp) FROM events;"
    db_connection.execute(query)
    row = db_connection.fetchone()
    return row[0]
