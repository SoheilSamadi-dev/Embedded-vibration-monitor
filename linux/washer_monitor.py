#!/usr/bin/env python3
# Copyright (c) 2026 Soheil Samadi
# SPDX-License-Identifier: AGPL-3.0-only
# Licensed under the GNU AGPL v3; see LICENSE in the repository root.

"""Follow the existing log; never open the Nicla serial device a second time."""
import argparse
from collections import deque
from datetime import datetime
import json
import math
from pathlib import Path
import queue
import selectors
import subprocess
import threading
import time

from telegram_notify import send_message


class Detector:
    def __init__(self, config):
        self.c = config
        for key in ('threshold_raw', 'start_seconds', 'stop_seconds',
                    'max_gap_seconds', 'min_pairs_per_second'):
            if not math.isfinite(config[key]) or config[key] <= 0:
                raise ValueError('Invalid setting: ' + key)
        if not 0 < config['start_fraction'] <= 1:
            raise ValueError('start_fraction must be in (0, 1]')
        self.state = 'UNKNOWN'
        self.reset()

    def reset(self):
        self.state = 'UNKNOWN'
        self.history = deque()
        self.quiet = 0.0
        self.last_ms = None

    def feed(self, ms, duration_ms, pairs, score):
        if (not math.isfinite(score) or score < 0 or ms < 0
                or not 500 <= duration_ms <= 2000
                or pairs < self.c['min_pairs_per_second'] * duration_ms / 1000):
            self.reset()
            return None
        if self.last_ms is not None:
            delta = ms - self.last_ms
            if delta <= 0 or delta > self.c['max_gap_seconds'] * 1000 or abs(delta - duration_ms) > 250:
                self.reset()
        self.last_ms = ms
        duration = duration_ms / 1000
        moving = score >= self.c['threshold_raw']
        self.history.append([duration, moving])
        total = sum(item[0] for item in self.history)
        excess = total - self.c['start_seconds']
        while excess > 1e-9:
            removed = min(excess, self.history[0][0])
            self.history[0][0] -= removed
            excess -= removed
            if self.history[0][0] <= 1e-9:
                self.history.popleft()
        self.quiet = 0 if moving else self.quiet + duration
        total = sum(item[0] for item in self.history)
        active = sum(d for d, m in self.history if m)
        before = self.state
        if self.state != 'ACTIVE' and moving and total >= self.c['start_seconds'] - 1e-6 and active / total >= self.c['start_fraction']:
            self.state = 'ACTIVE'
        elif self.quiet >= self.c['stop_seconds']:
            self.state = 'IDLE'
        return self.state if before != self.state else None


def transition_message(previous, current, config):
    """Notify new starts and confirmed stops, never initial idle or data loss."""
    if current == previous:
        return None
    if current == 'ACTIVE':
        return (f"Washing machine started: vibration detected for at least "
                f"{config['start_fraction']:.0%} of the last "
                f"{config['start_seconds']:g} seconds.")
    if previous == 'ACTIVE' and current == 'IDLE':
        return (f"Washing machine stopped vibrating: below the vibration threshold "
                f"for {config['stop_seconds']:g} seconds.")
    return None


def parse_line(line):
    stamp, payload = line[:19], line[20:].strip()
    if not payload.startswith('VIB_RAW,'):
        return None
    fields = payload.split(',')
    if len(fields) != 5:
        raise ValueError('Invalid summary')
    return (datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S').timestamp(),
            int(fields[1]), int(fields[2]), int(fields[3]), float(fields[4]))


def emit(**values):
    print(json.dumps({'time': datetime.now().astimezone().isoformat(), **values}), flush=True)


def notification_worker(messages, credentials):
    while True:
        message = messages.get()
        # Bounded retries off the sampling thread. Delivery is best effort;
        # a timeout after server acceptance can cause a duplicate on retry.
        for attempt in range(3):
            try:
                send_message(credentials, message)
                emit(event='notification_sent')
                break
            except Exception:
                emit(event='notification_failed', attempt=attempt + 1)
                if attempt < 2:
                    time.sleep(5)


def run(args):
    detector = Detector(json.loads(args.config.read_text()))
    confirmed = None
    if args.state_file.exists():
        try:
            confirmed = json.loads(args.state_file.read_text()).get('confirmed')
        except (ValueError, OSError):
            emit(event='state_file_unreadable')
    messages = queue.Queue(maxsize=10)
    if args.telegram.exists():
        threading.Thread(target=notification_worker, args=(messages, args.telegram), daemon=True).start()
    else:
        emit(event='notifications_disabled', reason='No Telegram credentials configured')
    proc = subprocess.Popen(['tail', '-n', '0', '-F', str(args.log)], stdout=subprocess.PIPE)
    last_received = time.monotonic()
    pending = b''
    emit(event='monitor_started', state='UNKNOWN', settings=detector.c)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ)
            while True:
                if time.monotonic() - last_received > detector.c['max_gap_seconds']:
                    if detector.last_ms is not None:
                        detector.reset()
                        emit(event='sensor_gap', state='UNKNOWN')
                for key, _ in selector.select(timeout=1):
                    chunk = key.fileobj.read1(65536)
                    if not chunk:
                        raise RuntimeError('Log follower exited')
                    pending += chunk
                    while b'\n' in pending:
                        raw, pending = pending.split(b'\n', 1)
                        try:
                            sample = parse_line(raw.decode('utf-8'))
                            if sample is None:
                                continue
                            stamp, ms, duration, pairs, score = sample
                            # Ignore old queued log lines; timestamps are Pi processing time,
                            # not proof of sensor acquisition time.
                            if not -2 <= time.time() - stamp <= detector.c['max_gap_seconds']:
                                detector.reset()
                                continue
                            last_received = time.monotonic()
                            transition = detector.feed(ms, duration, pairs, score)
                        except (ValueError, UnicodeError):
                            detector.reset()
                            emit(event='invalid_summary', state='UNKNOWN')
                            continue
                        emit(event='measurement', score=score, pairs=pairs, state=detector.state)
                        if transition:
                            emit(event='state_change', state=transition)
                            if transition != confirmed:
                                message = transition_message(confirmed, transition, detector.c)
                                confirmed = transition
                                args.state_file.parent.mkdir(parents=True, exist_ok=True)
                                temporary = args.state_file.with_suffix('.tmp')
                                temporary.write_text(json.dumps({'confirmed': confirmed}))
                                temporary.replace(args.state_file)
                                if message and args.telegram.exists():
                                    try:
                                        messages.put_nowait(message)
                                    except queue.Full:
                                        emit(event='notification_queue_full')
                if len(pending) > 65536:
                    pending = b''
                    detector.reset()
                    emit(event='oversized_line', state='UNKNOWN')
    finally:
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == '__main__':
    base = Path.home() / 'embedded-condition-monitor'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, default=base / 'nicla-timestamped.log')
    parser.add_argument('--config', type=Path, default=base / 'washer-config.json')
    parser.add_argument('--state-file', type=Path, default=base / 'washer-state.json')
    parser.add_argument('--telegram', type=Path, default=Path.home() / '.config/condition-monitor/telegram.json')
    try:
        run(parser.parse_args())
    except KeyboardInterrupt:
        pass
