#pragma once
#include <math.h>

// Hardware-independent calculation shared by firmware and host tests.
class VibrationAccumulator {
public:
  void add(int x, int y, int z) {
    if (hasPrevious_) {
      const double dx = double(x) - px_;
      const double dy = double(y) - py_;
      const double dz = double(z) - pz_;
      sumSquares_ += dx * dx + dy * dy + dz * dz;
      pairs_++;
    }
    px_ = x; py_ = y; pz_ = z;
    hasPrevious_ = true;
  }

  unsigned long pairs() const { return pairs_; }
  double rms() const { return pairs_ ? sqrt(sumSquares_ / pairs_) : 0; }

  // Keep the last sample: the next pair spans the summary boundary,
  // matching the original continuous-stream calculation.
  void clearWindow() {
    sumSquares_ = 0;
    pairs_ = 0;
  }

private:
  double sumSquares_ = 0;
  unsigned long pairs_ = 0;
  bool hasPrevious_ = false;
  int px_ = 0, py_ = 0, pz_ = 0;
};
