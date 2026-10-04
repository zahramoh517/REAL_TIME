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

## TODO / things to clean up before I'd call this done

- **Flip `TESTING` back to `False` in watchdog.py** before any kind of real
  run -- right now it's reading the latest timestamp in the data instead of
  the actual clock, which only makes sense because I'm working against
  replayed historical data, not live.
- **Double check the sleep intervals are back to real values** --
  `REPLAY_DELAY_SECONDS` and `SWEEP_INTERVAL_SECONDS` get turned way down
  while testing so I'm not sitting around for an hour, easy to forget to
  put back.
- **Known issue: almost everything gets flagged "Late."** Traced this back
  to how the synthetic data was generated -- the route_reference table picks
  random intermediate hubs without checking if they're anywhere near the
  actual route (e.g. a Gatineau -> Montreal shipment got routed through
  Lethbridge, AB), and the expected arrival windows are random offsets that
  don't account for real travel distance at all. Meanwhile the actual event
  timestamps *are* based on real distance/speed math. So the two don't line
  up, and almost everything reads as behind schedule -- it's not a bug in
  the schedule-check logic itself, it's the test data being internally
  inconsistent. If I were doing this for real, the fix is to generate
  expected windows from the same distance/speed assumptions as the events,
  or just use a real routing API for the "expected" side.
- Add the XPENDING / XCLAIM sweep to the watchdog for reclaiming stuck
  Redis messages and logging them as `system_error` alerts -- designed this
  conceptually, never actually wired it in.
- The WebSocket in `api/main.py` polls Postgres every 2 seconds instead of
  getting pushed updates directly from the consumer/watchdog via Redis
  pub/sub. Works fine for a demo, but there's a built-in ~2s lag. Would
  switch this to pub/sub for anything real.
- Haven't stress-tested what happens if the consumer or watchdog crashes
  mid-run and gets restarted -- should revisit the pending-message handling
  once the XPENDING piece above is in.
