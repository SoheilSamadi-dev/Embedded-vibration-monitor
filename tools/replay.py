#!/usr/bin/env python3
"""Replay a timestamped sensor log offline; never send notifications."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'linux'))
from washer_monitor import Detector, parse_line


def replay(log, config):
    detector = Detector(config)
    previous_stamp = None
    for number, line in enumerate(log, 1):
        try:
            sample = parse_line(line)
        except ValueError as error:
            raise ValueError(f'Invalid summary at line {number}') from error
        if sample is None:
            continue
        stamp, ms, duration, pairs, score = sample
        if previous_stamp is not None and (
                stamp < previous_stamp or
                stamp - previous_stamp > config['max_gap_seconds']):
            detector.reset()
        previous_stamp = stamp
        transition = detector.feed(ms, duration, pairs, score)
        if transition:
            yield {'time': line[:19], 'state': transition}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording', type=Path)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text())
        with args.recording.open(encoding='utf-8') as log:
            for event in replay(log, config):
                print(json.dumps(event))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Replay failed: {error}\n')


if __name__ == '__main__':
    main()
