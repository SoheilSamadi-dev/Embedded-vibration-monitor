# Validation

## Method

A first normal wash was recorded and used for offline threshold/window tuning.
The selected settings were then installed before a second normal wash. The
second recording was replayed with the same detector configuration and compared
with received Telegram messages and the user's approximate observations.

| Cycle | Purpose | Replay start | Replay stop | Observation |
|---|---|---|---|---|
| September 6, 2026 | Tuning | 20:17:18 | 21:55:31 | Approximately 20:17–21:55 reported |
| September 7, 2026 | Subsequent-cycle check | 22:16:44 | 22:56:52 | Messages at 22:16/22:56; user confirmed approximate match |

Times are recorded local wall times. Exact seconds come from replay, not from
recovered live journal transitions. The original first-cycle detector used a
higher threshold and detected activity late; the first row reports the tuned
configuration applied retrospectively.

## Second recording

There were 5,698 vibration summaries between 21:43:50 and 23:19:19, with no
malformed vibration summaries. Replay produced two notification intents and no
intermediate idle during the detected wash.

Two sensor uptime resets occurred during activity:

| Last summary | Next summary | Gap | ACTIVE reconfirmed in replay |
|---|---|---|---|
| 22:28:55 | 22:29:01 | 6 seconds | 22:29:20 |
| 22:36:28 | 22:36:34 | 6 seconds | 22:36:53 |

Raw acceleration resumed after about five seconds. Second-resolution processing
timestamps do not measure exact hardware reset duration. Retained confirmed state
suppressed duplicate start intents. Four further resets occurred outside the
active interval; causes were not recorded.

## Interpretation

The outcome supports the intended prototype behavior on these two cycles. It
does not establish an error rate, precise notification latency, or reliability
across other appliances. The live journal for the second wash was unavailable;
replay cannot reconstruct service scheduling, restarts, or network retries.

Raw household recordings and personal session notes are retained locally rather
than published. Consequently these observations are documented results, not a
publicly reproducible dataset. The repository's unit tests are independently
runnable and do not require those recordings.
