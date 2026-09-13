# Protocol and design

## Sensor node

`03_usb_vibration` requests 50 Hz acceleration from Arduino_BHY2. A packet
callback accumulates squared successive-vector differences so packets delivered
in the same update call are all included. The score is
`sqrt(mean(dx*dx + dy*dy + dz*dz))`. It depends on the sensor configuration,
mounting, and appliance; threshold 7 is not a universal calibration.

USB output at configured baud rate 115200:

```text
ACC_RAW,uptime_ms,x,y,z
VIB_RAW,uptime_ms,window_ms,sample_pairs,rms_delta_raw
```

`ACC_RAW` is emitted at approximately 5 Hz for inspection; detection uses only
the approximately one-second `VIB_RAW` summaries. The logger prepends Pi local
time as `YYYY-MM-DD HH:MM:SS ` to every line. This is processing time, not a
measurement of acquisition latency.

## Linux gateway

`logger.sh` configures the serial port and appends timestamped lines to disk.
`washer_monitor.py` follows new lines using `tail -n 0 -F`. It rejects stale
summaries, checks duration and pair counts, and maintains a duration-weighted
rolling activity window and a continuous quiet timer.

States are `UNKNOWN`, `ACTIVE`, and `IDLE`. A gap or sensor uptime discontinuity
resets evidence. Confirmed state survives in a separate JSON file; returning to
the same confirmed state does not send another message. Initial idle and unknown
do not notify. A later confirmed idle after an active state can notify even when
a gap occurred between them.

A background thread sends notifications with bounded retries. This avoids holding
up sampling during an HTTP request. State is saved before notification delivery;
it is not a durable delivery queue.

## Limits

- A full cycle missed during downtime cannot be reconstructed by the live follower.
- Sensor resets remain unexplained; power stability has not been established.
- Notification retries can duplicate delivery after ambiguous network timeouts;
  queued messages do not survive a process exit.
- `copytruncate` log rotation can lose lines during copying/truncation.
- Earlier boot journals were unavailable during validation; storage limits alone
  do not establish persistent journaling.
- Two washes do not establish performance across programs, appliances, and mounts.
