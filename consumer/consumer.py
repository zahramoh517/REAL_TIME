"""
Main consumer: reads live events off the Redis stream, writes them to
Postgres, checks each one against schedule, and raises an off_schedule
alert when it's running late. Only acknowledges a message once all of
that has actually succeeded -- if something crashes mid-way, the message
stays pending and gets picked up again (at-least-once delivery).
"""

from datetime import datetime

from shared.db import conn, db_connection
from shared.redis_client import r
from shared.alerts import create_alert
from consumer.schedule_check import check_schedule

GROUP_NAME = "my_consumer_group"
CONSUMER_NAME = "consumer_1"
STREAM_NAME = "events_stream"


def insert_event(event, db_connection):
    query = """
        INSERT INTO events (event_id, shipment_id, timestamp, lat, lon, hub_name)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    timestamp = datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S') #string must change, redis has issues with timedates??
    db_connection.execute(query, (
        event['event_id'], event['shipment_id'], timestamp,
        float(event['lat']), float(event['lon']), event['hub_name']
    ))
    conn.commit() 


def run_consumer(db_connection, redis_client):
    while True:
        response = redis_client.xreadgroup(
            GROUP_NAME, CONSUMER_NAME, {STREAM_NAME: '>'}, count=1, block=0 #> is for events not proceseed yet, 0 for all 
        )
        _, messages = response[0]
        msg_id, event = messages[0]

        insert_event(event, db_connection)

        status = check_schedule(event, db_connection)
        if status == "Late":
            create_alert(event['shipment_id'], 'off_schedule', event['event_id'], db_connection)

        redis_client.xack(STREAM_NAME, GROUP_NAME, msg_id)
        print(f"Processed event {event['event_id']} for shipment {event['shipment_id']} -- status: {status}")


if __name__ == "__main__":
    run_consumer(db_connection, r)
