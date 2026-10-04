"""
Replay producer.

Reads every event already sitting in Postgres (originally loaded from the
synthetic CSV) and re-plays it into the Redis stream, one at a time, in real chronological order.

Why make this? generating a realistic multi-day fleet simulation live,
in real time, would take days to watch unfold. This collapses it into a
much shorter window while still preserving per shipment ordering and true
global chronological interleaving (see merge_shipments below).
"""

import heapq
import time

from shared.db import conn, db_connection
from shared.redis_client import r

REPLAY_DELAY_SECONDS = 0.5  # time between XADD calls, LOWER this for a fast test run


def load_all_events():
    db_connection.execute("SELECT * FROM events;")
    return db_connection.fetchall()


def group_by_shipment(rows):
    """Buckets rows by shipment_id. Each bucket stays in its original order."""
    shipment_lists = {}
    for row in rows:
        shipment_id = row[1]
        shipment_lists.setdefault(shipment_id, []).append(row)
    return shipment_lists


def merge_shipments(shipment_lists):
    """
    K-way merge:
    """
    heap = []
    for shipment_id, entries in shipment_lists.items():
        heapq.heappush(heap, (entries[0][2], shipment_id))  # (timestamp, shipment_id)

    merged = []
    while heap:
        timestamp, shipment_id = heapq.heappop(heap)
        row = shipment_lists[shipment_id].pop(0)
        merged.append(row)

        if shipment_lists[shipment_id]:
            next_timestamp = shipment_lists[shipment_id][0][2]
            heapq.heappush(heap, (next_timestamp, shipment_id))

    return merged


def replay_to_redis(merged, redis_client):
    for row in merged:
        redis_client.xadd('events_stream', {
            'event_id': str(row[0]),
            'shipment_id': str(row[1]),
            'timestamp': row[2].strftime('%Y-%m-%d %H:%M:%S'), #Note!
            'lat': row[3],
            'lon': row[4],
            'hub_name': row[5] if row[5] is not None else ""
        })
        time.sleep(REPLAY_DELAY_SECONDS)


if __name__ == "__main__":
    rows = load_all_events()
    shipment_lists = group_by_shipment(rows)
    merged = merge_shipments(shipment_lists)
    replay_to_redis(merged, r)
