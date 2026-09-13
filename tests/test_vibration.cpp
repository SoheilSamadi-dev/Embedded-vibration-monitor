// Copyright (c) 2026 Soheil Samadi
// SPDX-License-Identifier: AGPL-3.0-only
// Licensed under the GNU AGPL v3; see LICENSE in the repository root.

#include "../nicla-firmware/03_usb_vibration/VibrationAccumulator.h"
#include <cmath>
#include <cstdlib>
#include <iostream>

void check(bool passed, const char* description) {
  if (!passed) {
    std::cerr << "FAIL: " << description << '\n';
    std::exit(EXIT_FAILURE);
  }
}

void near(double actual, double expected, const char* description) {
  check(std::abs(actual - expected) < 1e-9, description);
}

int main() {
  VibrationAccumulator v;
  check(v.pairs() == 0, "empty accumulator has no pairs");
  near(v.rms(), 0, "empty accumulator returns zero");
  v.add(100, -200, 4000);
  check(v.pairs() == 0, "first sample establishes baseline only");
  near(v.rms(), 0, "first sample has no vibration score");
  for (int i = 0; i < 5; ++i) v.add(100, -200, 4000);
  check(v.pairs() == 5, "N samples produce N-1 pairs");
  near(v.rms(), 0, "constant nonzero acceleration produces zero vibration");

  VibrationAccumulator known;
  known.add(0, 0, 0);
  known.add(3, 4, 12); // Squared vector difference = 169; magnitude = 13.
  check(known.pairs() == 1, "one vector difference counted");
  near(known.rms(), 13, "all three axes contribute");
  known.add(3, 4, 12); // Zero difference: RMS is sqrt((169+0)/2).
  check(known.pairs() == 2, "zero differences are included in the mean");
  near(known.rms(), std::sqrt(84.5), "RMS averages squared magnitudes");
  near(known.rms(), std::sqrt(84.5), "reading the score does not consume data");

  known.clearWindow();
  check(known.pairs() == 0, "window clear resets pair count");
  near(known.rms(), 0, "window clear resets score");
  known.add(0, 0, 0); // Previous sample (3,4,12) must survive the clear.
  check(known.pairs() == 1, "pair spanning window boundary is preserved");
  near(known.rms(), 13, "previous window sum is discarded; signed deltas work");

  VibrationAccumulator extremes;
  extremes.add(-32768, 0, 0);
  extremes.add(32767, 0, 0);
  near(extremes.rms(), 65535, "large signed sample difference does not overflow");
  std::cout << "All vibration calculation checks passed.\n";
}
