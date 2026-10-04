# Real-Time Shipment Tracking & Alerting System

Simulates a fleet of trucks reporting GPS pings in real time, streams those
events through Redis, and detects anomalies (off-schedule, stalled in
transit, stalled at a hub) as they happen.

## Architecture

```
replay_producer.py --> Redis Stream --> consumer.py --> Postgres --> alerts
                                              ^
                                     watchdog.py (periodic, separate process)
```

- **Producer** (`producer/replay_producer.py`): reads pre-generated synthetic
  shipment data and replays it into a Redis stream, globally interleaved by
  timestamp across all shipments (k-way merge, min-heap).
- **Consumer** (`consumer/consumer.py`): event-driven. Reads new stream
  entries via a Redis consumer group, writes each one to Postgres, checks it
  against the planned route, and raises an `off_schedule` alert if it's
  running late. Only acknowledges a message after everything succeeds.
- **Watchdog** (`watchdog/watchdog.py`): periodic, not event-driven. Sweeps
  every shipment on a timer and catches the two anomaly types the consumer
  can never see on its own -- a stalled shipment is, by definition, not
  sending new events.

## Setup

```bash
brew install postgresql@16 redis
# or: docker run -d --name redis -p 6379:6379 redis

createdb postgres  # or adjust shared/db.py to match your setup
psql -d postgres -f db/schema.sql
```

Install Python deps:
```bash
pip install psycopg redis
```

## Running

Three separate processes, each in its own terminal tab:

```bash
python -m producer.replay_producer
python -m consumer.consumer
python -m watchdog.watchdog
```

## Notes

- `watchdog.py` has a `TESTING` flag -- set `True` while working against
  replayed/historical data (compares against the latest timestamp in the
  dataset rather than real time, since replayed data is always in the past).
  Set to `False` for a real live run.
- `producer/replay_producer.py` has `REPLAY_DELAY_SECONDS` -- lower this for
  a fast test run instead of waiting for a realistic-speed replay.
