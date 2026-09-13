# Check live sensor data

This manual check verifies that readings respond plausibly to stillness and
movement. It is not a calibrated accuracy test or validation of wash detection.
Use the `03_usb_vibration` firmware and the installed logger described in the
[setup guide](../linux/WASHER_SETUP.md).

## Watch readings on the Pi

Stop the detector during hand testing to avoid generating start/stop Telegram
messages. Keep the logger running to capture the sensor output:

```bash
sudo systemctl stop washer-monitor
sudo systemctl start nicla-logger
```

Follow the latest sensor lines as they arrive:

```bash
tail -n 20 -F ~/embedded-condition-monitor/nicla-timestamped.log
```

This reads the log file, not the USB port. Do not open a second serial monitor
while the logger owns that port. Press Ctrl+C to stop viewing; logging continues.

Each line begins with Pi local processing time, followed by one of these formats:

```text
ACC_RAW,uptime_ms,x,y,z
VIB_RAW,uptime_ms,window_ms,sample_pairs,rms_delta_raw
```

- `ACC_RAW`: approximately five displayed acceleration snapshots per second.
  X, Y and Z are raw counts; they include gravity and are not values in m/s².
- `VIB_RAW`: approximately one summary per second, calculated from the requested
  50 Hz acceleration stream. `window_ms` should be near 1000 and `sample_pairs`
  typically near 50 (50–51 were observed; the first window can contain fewer).
- `rms_delta_raw`: RMS magnitude of successive acceleration changes, in raw
  counts. This is the value used by the detector, not the magnitude of gravity.
- `uptime_ms`: milliseconds since the firmware started. It should increase;
  unexpectedly returning to a small value suggests a firmware restart. The
  counter also wraps after long continuous uptime, so this alone is not a reset
  diagnosis for a long-running device.

To view only vibration summaries, use this instead of the full-log command:

```bash
tail -n 20 -F ~/embedded-condition-monitor/nicla-timestamped.log | grep --line-buffered ' VIB_RAW,'
```

## Check whether the readings make sense

1. **Stillness:** place the board securely on a dry, stable surface for 30–60
   seconds. Acceleration axes should be relatively steady, but need not be zero
   because gravity is present. The vibration score should have a comparatively
   low, nonzero noise baseline.
2. **Orientation:** gently tilt the board and hold it still in a new orientation.
   The acceleration components should change as gravity projects onto different
   axes. The vibration score should rise during movement and settle again once
   held still.
3. **Movement:** gently move or tap the surface near the board. Expect changing
   acceleration readings and vibration scores above the stationary baseline.
   Avoid pulling on the USB connector. Stop moving it and confirm scores settle.
4. **Continuity:** watch for at least a few minutes. Summary times and uptime
   should advance steadily, with usable sample counts. Repeated zeros, persistent
   low pair counts, gaps or uptime resets need investigation. A zero score with
   zero pairs means no usable measurement, not verified stillness.
5. **Mounted appliance:** restore the intended mounting position and compare
   scores during idle and a normal wash. Record actual start/end times. The
   configured threshold must be assessed against those readings; a successful
   hand-motion check does not establish that the wash threshold is appropriate.

The detector accepts summary durations from 500 to 2000 ms and requires the
configured minimum pair rate (25 pairs/second in the original configuration).
For a one-second window that means at least 25 pairs. These are input-validity
checks, not guarantees of sensor quality. Inspect the actual configuration if it
has been tuned.

## If readings stop or look wrong

Inspect logger status and recent errors:

```bash
systemctl status nicla-logger --no-pager
journalctl -u nicla-logger -n 30 --no-pager
ls -l /dev/serial/by-id/
```

Check that the configured device matches the connected Nicla, the cable supports
data, and firmware `03_usb_vibration` is installed. If there are uptime resets,
record their times and inspect connections and power; the sensor log does not
identify the reset cause. Do not assume a silent stream means the appliance is
idle. Pi timestamps reflect processing time and may hide buffered delivery.

## Finish

Press Ctrl+C to exit the viewer. When ready to resume normal detection:

```bash
sudo systemctl start washer-monitor
```

The detector starts with fresh evidence and follows new log lines; it does not
replay the hand-test recording. Previously saved confirmed state still affects
notification selection. If you want the whole system paused instead, use:

```bash
sudo systemctl stop washer-monitor nicla-logger
```

These commands stop services without disabling their next-boot startup.
