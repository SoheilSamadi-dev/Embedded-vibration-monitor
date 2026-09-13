# Copyright (c) 2026 Soheil Samadi
# SPDX-License-Identifier: AGPL-3.0-only
# Licensed under the GNU AGPL v3; see LICENSE in the repository root.

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Import production modules without requiring package installation or PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'linux'))

from washer_monitor import Detector, parse_line, transition_message
from telegram_notify import send_message


# Deliberately independent of deployment tuning in washer-config.json.
# These controlled inputs define the scenarios being tested.
TEST_CONFIG = {
    'threshold_raw': 10.0,
    'start_seconds': 5,
    'start_fraction': 0.6,
    'stop_seconds': 8,
    'max_gap_seconds': 3,
    'min_pairs_per_second': 25,
}


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.d = Detector(TEST_CONFIG.copy())
        self.ms = 0

    def feed(self, score=100, seconds=1):
        transitions = []
        for _ in range(seconds):
            self.ms += 1000
            transition = self.d.feed(self.ms, 1000, 50, score)
            if transition:
                transitions.append(transition)
        return transitions

    def test_exact_start_and_stop_delays(self):
        self.assertEqual(self.feed(seconds=4), [])
        self.assertEqual(self.d.state, 'UNKNOWN')
        self.assertEqual(self.feed(), ['ACTIVE'])
        self.assertEqual(self.feed(score=0, seconds=7), [])
        self.assertEqual(self.d.state, 'ACTIVE')
        self.assertEqual(self.feed(score=0), ['IDLE'])

    def test_detector_honors_different_settings(self):
        # Explicit expected boundaries for two independent input scenarios.
        cases = [
            dict(threshold_raw=2.0, start_seconds=4, start_fraction=0.5,
                 stop_seconds=6, max_gap_seconds=3, min_pairs_per_second=10),
            dict(threshold_raw=35.0, start_seconds=8, start_fraction=0.75,
                 stop_seconds=12, max_gap_seconds=3, min_pairs_per_second=40),
        ]
        for config in cases:
            with self.subTest(config=config):
                self.d = Detector(config)
                self.ms = 0
                threshold = config['threshold_raw']
                self.assertEqual(self.feed(score=threshold,
                                           seconds=config['start_seconds'] - 1), [])
                self.assertEqual(self.feed(score=threshold), ['ACTIVE'])
                self.assertEqual(self.feed(score=threshold - 0.1,
                                           seconds=config['stop_seconds'] - 1), [])
                self.assertEqual(self.feed(score=threshold - 0.1), ['IDLE'])

    def test_small_pauses_allow_mostly_active_start(self):
        for i in range(5):
            self.feed(score=0 if i % 5 < 2 else 10)
        self.assertEqual(self.d.state, 'ACTIVE')

    def test_insufficient_vibration_does_not_start(self):
        # One moving second in three: at most two in any five-second window.
        for i in range(30):
            self.assertNotIn('ACTIVE', self.feed(score=100 if i % 3 == 0 else 0))
            self.assertNotEqual(self.d.state, 'ACTIVE')

    def test_one_bump_does_not_start(self):
        self.feed(score=0, seconds=8)
        self.assertEqual(self.feed(score=10000), [])
        self.assertEqual(self.d.state, 'IDLE')
        self.assertEqual(self.feed(score=0, seconds=8), [])
        self.assertEqual(self.d.state, 'IDLE')

    def test_vibration_resets_stop_timer(self):
        self.feed(seconds=8)
        self.feed(score=0, seconds=7)
        self.feed()
        self.feed(score=0, seconds=7)
        self.assertEqual(self.d.state, 'ACTIVE')
        self.assertEqual(self.feed(score=0), ['IDLE'])

    def test_gap_is_unknown_and_requires_new_evidence(self):
        self.feed(seconds=4)
        self.ms += 10000
        self.feed()
        self.assertEqual(self.d.state, 'UNKNOWN')
        self.feed(seconds=3)
        self.assertEqual(self.d.state, 'UNKNOWN')
        self.assertEqual(self.feed(), ['ACTIVE'])
        self.d.reset()
        self.assertEqual(self.d.state, 'UNKNOWN')
        self.assertEqual(self.d.quiet, 0)

    def test_sensor_reboot_and_duplicate_reset_evidence(self):
        self.feed(seconds=4)
        self.ms = 0
        self.feed()
        self.assertEqual(self.d.state, 'UNKNOWN')
        self.d.feed(self.ms, 1000, 50, 100)
        self.assertEqual(len(self.d.history), 1)

    def test_bad_samples_do_not_count_as_quiet(self):
        self.feed(seconds=8)
        for duration, pairs, score in [(1000, 0, 0), (1000, 50, float('nan')),
                                        (1000, 50, float('inf')), (5000, 50, 0)]:
            self.d.feed(self.ms + 1000, duration, pairs, score)
            self.assertEqual(self.d.state, 'UNKNOWN')

    def test_parse_and_ignore_raw(self):
        self.assertIsNone(parse_line('2026-09-06 12:00:00 ACC_RAW,1,2,3,4'))
        self.assertEqual(parse_line('2026-09-06 12:00:00 VIB_RAW,1000,1000,49,12.5')[1:],
                         (1000, 1000, 49, 12.5))
        with self.assertRaises(ValueError):
            parse_line('2026-09-06 12:00:00 VIB_RAW,broken')

    def test_transition_notifications(self):
        self.assertIsNone(transition_message(None, 'IDLE', TEST_CONFIG))
        self.assertIsNone(transition_message('IDLE', 'IDLE', TEST_CONFIG))
        self.assertIsNone(transition_message('ACTIVE', 'UNKNOWN', TEST_CONFIG))
        self.assertIsNone(transition_message('ACTIVE', 'ACTIVE', TEST_CONFIG))
        start = transition_message('IDLE', 'ACTIVE', TEST_CONFIG)
        self.assertIn('60%', start)
        self.assertIn('5 seconds', start)
        self.assertIn('stopped vibrating', transition_message('ACTIVE', 'IDLE', TEST_CONFIG))
        self.assertIn('8 seconds', transition_message('ACTIVE', 'IDLE', TEST_CONFIG))

    def test_notification_targets_configured_chat(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'telegram.json'
            path.write_text(json.dumps({'token': 'dummy', 'chat_id': '123'}))
            with patch('telegram_notify.api') as api:
                send_message(path, 'test')
            api.assert_called_once_with('dummy', 'sendMessage', {'chat_id': '123', 'text': 'test'})


if __name__ == '__main__':
    unittest.main()
