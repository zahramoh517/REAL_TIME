
from shared.db import conn


def create_alert(shipment_id, alert_type, triggering_event_id, db_connection):
    query = """
        INSERT INTO alerts (shipment_id, alert_type, triggering_event_id, status)
        VALUES (%s, %s, %s, 'active');
    """
    db_connection.execute(query, (shipment_id, alert_type, triggering_event_id))
    conn.commit()
