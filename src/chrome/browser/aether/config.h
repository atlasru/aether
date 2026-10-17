// Copyright 2026 The Aether Authors
// SPDX-License-Identifier: GPL-3.0-only
#ifndef CHROME_BROWSER_AETHER_CONFIG_H_
#define CHROME_BROWSER_AETHER_CONFIG_H_

#include <cstdint>

namespace aether {
inline constexpr int kSchemaVersion = 1;
inline constexpr int kLastSetupStep = 5;
inline constexpr char kSetupPref[] = "aether.setup";
inline constexpr char kDensityPref[] = "aether.ui.density";

// Numeric layout values deliberately match HeliumLayoutType.
enum class Layout { kClassic = 0, kCompact = 1, kVertical = 2 };
enum class Experience { kSimplicity = 0, kBalanced = 1, kControl = 2 };
// Numeric appearance values deliberately match ThemeService::BrowserColorScheme.
enum class Appearance { kSystem = 0, kLight = 1, kDark = 2 };
enum class Density { kComfortable = 0, kCompact = 1 };
enum class Performance { kBalanced = 0, kMemorySaver = 1, kBatterySaver = 2 };

struct Config {
  int layout = static_cast<int>(Layout::kCompact);
  int experience = static_cast<int>(Experience::kBalanced);
  int appearance = static_cast<int>(Appearance::kSystem);
  int density = static_cast<int>(Density::kComfortable);
  int performance = static_cast<int>(Performance::kBalanced);
  // Zero selects the neutral default theme. Other values are opaque RGB.
  int accent = 0;
  bool memory_saver = true;
  bool battery_saver = true;
  bool background_suspension = true;
  bool operator==(const Config&) const = default;
};

constexpr bool IsValid(const Config& c) {
  return c.layout >= 0 && c.layout <= 2 && c.experience >= 0 &&
         c.experience <= 2 && c.appearance >= 0 && c.appearance <= 2 &&
         c.density >= 0 && c.density <= 1 && c.performance >= 0 &&
         c.performance <= 2 && c.accent >= 0 && c.accent <= 0xffffff;
}

constexpr int MemoryState(const Config& c) { return c.memory_saver ? 2 : 0; }
constexpr int MemoryAggressiveness(const Config& c) {
  return c.performance == static_cast<int>(Performance::kMemorySaver) ? 2 : 1;
}
constexpr int BatteryState(const Config& c) {
  return !c.battery_saver ? 0 :
         c.performance == static_cast<int>(Performance::kBatterySaver) ? 2 : 1;
}

// Settings from a newer build must remain untouched on downgrade.
constexpr bool CanReadSchema(int version) {
  return version >= 0 && version <= kSchemaVersion;
}
constexpr bool IsValidStep(int step) {
  return step >= 0 && step <= kLastSetupStep;
}
}  // namespace aether
#endif  // CHROME_BROWSER_AETHER_CONFIG_H_
