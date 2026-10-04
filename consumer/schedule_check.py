"""
Figures out whether a shipment is on schedule, by comparing a live event
against the route_reference table.

Approach: find the last hub this shipment actually reached (from its own
event history), look up the next stop after that in the route plan, then
compare the event's timestamp against that stop's expected window.
"""

from datetime import datetime, timedelta

EARLY_TOLERANCE = timedelta(hours=1)
LATE_TOLERANCE = timedelta(hours=3)  # looser than early grace period for human error


def get_last_reached_hub(shipment_id, db_connection):
    """Most recent hub this shipment actually arrived at, or None if it hasn't reached one yet."""
    query = """
        SELECT hub_name
        FROM events
        WHERE hub_name != '' AND shipment_id = %s
        ORDER BY timestamp DESC
        LIMIT 1;
    """
    db_connection.execute(query, (shipment_id,))
    row = db_connection.fetchone()
    return row[0] if row else None


def get_next_expected_stop(shipment_id, last_hub, db_connection): 
    """
    Returns (expected_arrival_start, expected_arrival_end, hub_name, sequence_order)
    for the stop this shipment is currently heading toward.
    Returns None if the shipment hasn't reached any hub yet and has no first stop
    on record, or if it already reached its final destination.
    """
    if last_hub is None:
        query = """
            SELECT expected_arrival_start, expected_arrival_end, hub_name, sequence_order
            FROM route_reference
            WHERE shipment_id = %s AND sequence_order = 1;
        """
        db_connection.execute(query, (shipment_id,))
        row = db_connection.fetchone()
        return row if row else None

    lookup_query = """
        SELECT sequence_order
        FROM route_reference
        WHERE shipment_id = %s AND hub_name = %s;
    """
    db_connection.execute(lookup_query, (shipment_id, last_hub))
    current = db_connection.fetchone()
    if current is None:
        return None

    current_order = current[0]

    next_query = """
        SELECT expected_arrival_start, expected_arrival_end, hub_name, sequence_order
        FROM route_reference
        WHERE shipment_id = %s AND sequence_order = %s;
    """
    db_connection.execute(next_query, (shipment_id, current_order + 1))
    row = db_connection.fetchone()
    return row if row else None  #None if ARRIVEDDDD


def check_schedule(event, db_connection):
    """Returns 'Early', 'On Time', 'Late', or note if the route's done."""
    shipment_id = event['shipment_id']
    last_hub = get_last_reached_hub(shipment_id, db_connection)
    next_stop = get_next_expected_stop(shipment_id, last_hub, db_connection)

    if next_stop is None:
        return "reached final destination or no further stops scheduled"

    timestamp = datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S')
    expected_start, expected_end = next_stop[0], next_stop[1]

    if timestamp + EARLY_TOLERANCE < expected_start:
        return "Early"
    elif timestamp - LATE_TOLERANCE > expected_end:
        return "Late"
    else:
        return "On Time"
