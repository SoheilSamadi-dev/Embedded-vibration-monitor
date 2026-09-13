# Synthetic offline example

`synthetic-cycle.txt` is generated demonstration data, not an actual sensor
recording or evidence of detection accuracy. Its dates, scores and sample counts
are invented. Original household recordings remain private.

The 280 one-second summaries contain 120 quiet seconds (score 2), 40 vibrating
seconds (score 12), and 120 quiet seconds. Each line follows the logger's
`YYYY-MM-DD HH:MM:SS VIB_RAW,uptime_ms,window_ms,sample_pairs,rms_delta_raw` format.

From the repository root, run:

```bash
python3 tools/replay.py examples/synthetic-cycle.txt --config examples/synthetic-config.json
```

Expected output:

```json
{"time": "2000-01-01 00:02:00", "state": "IDLE"}
{"time": "2000-01-01 00:02:12", "state": "ACTIVE"}
{"time": "2000-01-01 00:04:40", "state": "IDLE"}
```

Start occurs 12 seconds into vibration because the rolling 20-second window
already contains quiet history, and 12/20 meets the 60% criterion. Initial idle
is a state transition, not a notification.

The example has its own configuration so tuning the deployment configuration
does not change its expected results. Change the example configuration to
explore how the result changes.

Replay calls the same detector as the live service, using sensor uptime and
recorded wall-time gaps. It does not access USB, load Telegram credentials,
send messages, or change saved detector state. It prints state transitions, not
notification delivery outcomes. Live receipt delays, service restarts, stale-line
filtering and network behavior cannot be reconstructed by this replay.
