// Copyright 2026 The Aether Authors. SPDX-License-Identifier: GPL-3.0-only
#include "chrome/browser/aether/config.h"
#include <cassert>
#include <iostream>

int main() {
  using namespace aether;
  static_assert(IsValid(Config()));
  static_assert(Config().layout == static_cast<int>(Layout::kCompact));
  static_assert(CanReadSchema(0) && CanReadSchema(1));
  static_assert(!CanReadSchema(-1) && !CanReadSchema(2));
  // Exhaust every supported combination. Experience and appearance must never
  // change security-independent resource policy or implicitly disable a toggle.
  int configurations = 0;
  for (int layout = 0; layout <= 2; ++layout)
    for (int experience = 0; experience <= 2; ++experience)
      for (int appearance = 0; appearance <= 2; ++appearance)
        for (int density = 0; density <= 1; ++density)
          for (int profile = 0; profile <= 2; ++profile)
            for (int toggles = 0; toggles < 8; ++toggles) {
              Config c{layout, experience, appearance, density, profile, 0xffffff,
                       bool(toggles & 1), bool(toggles & 2), bool(toggles & 4)};
              assert(IsValid(c));
              assert(MemoryState(c) == ((toggles & 1) ? 2 : 0));
              assert(MemoryAggressiveness(c) == (profile == 1 ? 2 : 1));
              assert(BatteryState(c) == ((toggles & 2) ? (profile == 2 ? 2 : 1) : 0));
              ++configurations;
            }
  for (int Config::* member : {&Config::layout, &Config::experience,
                              &Config::appearance, &Config::density,
                              &Config::performance, &Config::accent}) {
    Config c;
    c.*member = -1;
    assert(!IsValid(c));
    c.*member = 0x1000000;
    assert(!IsValid(c));
  }
  assert(IsValidStep(0) && IsValidStep(5));
  assert(!IsValidStep(-1) && !IsValidStep(6));
  std::cout << "PASS: " << configurations << " valid configurations; range and schema rejection\n";
}
