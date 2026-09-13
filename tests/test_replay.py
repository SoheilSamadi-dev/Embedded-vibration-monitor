# Copyright (c) 2026 Soheil Samadi
# SPDX-License-Identifier: AGPL-3.0-only
# Licensed under the GNU AGPL v3; see LICENSE in the repository root.

"""Check the documented example through the replay command-line interface."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReplayTests(unittest.TestCase):
    def test_synthetic_example_transitions(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'tools/replay.py'),
             str(ROOT / 'examples/synthetic-cycle.txt'), '--config',
             str(ROOT / 'examples/synthetic-config.json')],
            capture_output=True, text=True, check=True)
        events = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(events, [
            {'time': '2000-01-01 00:02:00', 'state': 'IDLE'},
            {'time': '2000-01-01 00:02:12', 'state': 'ACTIVE'},
            {'time': '2000-01-01 00:04:40', 'state': 'IDLE'},
        ])


if __name__ == '__main__':
    unittest.main()
