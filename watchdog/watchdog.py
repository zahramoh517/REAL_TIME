"""
Periodic watchdog. Unlike the consumer, this isn't event-driven -- it wakes
up on a timer and sweeps every still-active shipment, checking for the two
kinds of 'stalled' that the consumer, by design, would never notice on its
own (since a stalled shipment is, by definition, not sending new events).

TODO: fold in the XPENDING / XCLAIM sweep for stuck Redis messages here too,
logging them as a 'system_error' alert type -- kept conceptually separate
from real shipment problems so an active alert always points at one or the
other, not both at once.
"""

import time
from datetime import datetime

from shared.db import db_connection
from shared.geo_utils import get_latest_system_timestamp
from consumer.schedule_check import get_last_reached_hub, get_next_expected_stop
from watchdog.stall_detection import check_stalled_hub, check_stalled_in_transit

SWEEP_INTERVAL_SECONDS = 15 * 60  # matches the ping interval 

# While testing against replayed/historical data, real time has drifted weeks
# ahead of the dataset, so "now" needs to come from the data itself instead


def get_all_active_shipment_ids(db_connection):
    db_connection.execute("SELECT DISTINCT shipment_id FROM events;")
    return [row[0] for row in db_connection.fetchall()]


def run_watchdog(db_connection):
    while True:
        curr = datetime.now()

        for shipment_id in get_all_active_shipment_ids(db_connection):
            last_hub = get_last_reached_hub(shipment_id, db_connection)
            next_stop = get_next_expected_stop(shipment_id, last_hub, db_connection)

            if next_stop is None:
                continue  

            check_stalled_hub(shipment_id, curr, db_connection)
            check_stalled_in_transit(shipment_id, curr, db_connection)

        time.sleep(SWEEP_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_watchdog(db_connection)
