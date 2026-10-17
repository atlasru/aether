// Copyright 2026 The Aether Authors
// SPDX-License-Identifier: GPL-3.0-only
#include "chrome/browser/aether/preferences.h"

#include <utility>
#include <limits>

#include "base/check.h"
#include "base/functional/bind.h"
#include "chrome/browser/browser_process.h"
#include "chrome/browser/profiles/profile.h"
#include "chrome/browser/themes/theme_service.h"
#include "chrome/browser/themes/theme_service_factory.h"
#include "chrome/common/pref_names.h"
#include "components/helium_services/pref_names.h"
#include "components/performance_manager/public/user_tuning/prefs.h"
#include "components/prefs/pref_service.h"
#include "third_party/skia/include/core/SkColor.h"

namespace aether {
namespace tuning = performance_manager::user_tuning::prefs;
namespace {
// Every mutation below first saves a single journal dictionary in Preferences.
// A pending journal is replayed after a crash; finished journals are never
// replayed, so subsequent edits in Chromium Settings remain authoritative.
bool CanUseState(const base::DictValue& state) {
  const auto* version = state.Find("version");
  return !version || (version->is_int() && CanReadSchema(version->GetInt()));
}

void FinishJournal(base::WeakPtr<Profile> profile, int generation,
                   ApplyCallback done) {
  if (!profile) {
    return;
  }
  auto* prefs = profile->GetPrefs();
  auto state = prefs->GetDict(kSetupPref).Clone();
  if (state.FindInt("generation").value_or(0) != generation ||
      !state.FindBool("pending").value_or(false)) {
    std::move(done).Run("Setup transaction was superseded.");
    return;
  }
  state.Set("pending", false);
  state.Set("completed", true);
  state.Set("editing", false);
  state.Set("step", kLastSetupStep);
  prefs->SetDict(kSetupPref, std::move(state));
  prefs->SetBoolean(prefs::kHeliumDidOnboarding, true);
  prefs->CommitPendingWrite(base::BindOnce(std::move(done), std::string()));
}

void ApplyJournal(base::WeakPtr<Profile> profile, int generation,
                  ApplyCallback done) {
  if (!profile) {
    return;
  }
  auto* preferences = profile->GetPrefs();
  const auto& state = preferences->GetDict(kSetupPref);
  if (state.FindInt("generation").value_or(0) != generation ||
      !state.FindBool("pending").value_or(false)) {
    std::move(done).Run("Setup transaction was superseded.");
    return;
  }
  const auto* value = state.FindDict("config");
  auto config = value ? ParseConfig(*value) : std::nullopt;
  if (!CanUseState(state) || !config) {
    std::move(done).Run("Unsupported pending setup configuration.");
    return;
  }
  auto error = ValidateApplication(profile.get(), *config, true);
  if (!error.empty()) {
    std::move(done).Run(error);
    return;  // Preserve the journal for inspection/retry; never partially apply.
  }
  const Config& c = *config;
  preferences->SetInteger(prefs::kHeliumLayout, c.layout);
  preferences->SetInteger(kDensityPref, c.density);
  const bool simple = c.experience == static_cast<int>(Experience::kSimplicity);
  preferences->SetBoolean(prefs::kShowHomeButton,
                          c.experience == static_cast<int>(Experience::kControl));
  preferences->SetBoolean(prefs::kShowAvatarButton, !simple);
  // Navigation, security indicators, extension access and menu remain available.
  auto* theme = ThemeServiceFactory::GetForProfile(profile.get());
  if (c.accent == 0) {
    theme->UseDefaultTheme();
  } else {
    theme->SetUserColor(SkColorSetRGB((c.accent >> 16) & 255,
                                     (c.accent >> 8) & 255, c.accent & 255));
  }
  theme->SetBrowserColorScheme(
      static_cast<ThemeService::BrowserColorScheme>(c.appearance));

  PrefService* local = g_browser_process->local_state();
  local->SetInteger(tuning::kMemorySaverModeState, MemoryState(c));
  local->SetInteger(tuning::kMemorySaverModeAggressiveness, MemoryAggressiveness(c));
  local->SetInteger(tuning::kBatterySaverModeState, BatteryState(c));
  local->SetBoolean(tuning::kTabFreezingEnabled, c.background_suspension);
  // Flush global performance settings BEFORE clearing the profile journal.
  local->CommitPendingWrite(base::BindOnce(&FinishJournal, profile, generation,
                                          std::move(done)));
}
}  // namespace

std::optional<Config> ParseConfig(const base::DictValue& value) {
  Config c;
  auto layout = value.FindInt("layout");
  auto experience = value.FindInt("experience");
  auto appearance = value.FindInt("appearance");
  auto density = value.FindInt("density");
  auto performance = value.FindInt("performance");
  auto accent = value.FindInt("accent");
  auto memory = value.FindBool("memorySaver");
  auto battery = value.FindBool("batterySaver");
  auto suspension = value.FindBool("backgroundSuspension");
  if (!layout || !experience || !appearance || !density || !performance ||
      !accent || !memory || !battery || !suspension || value.size() != 9) {
    return std::nullopt;
  }
  c = {*layout, *experience, *appearance, *density, *performance, *accent,
       *memory, *battery, *suspension};
  return IsValid(c) ? std::optional(c) : std::nullopt;
}

base::DictValue ToValue(const Config& c) {
  return base::DictValue().Set("layout", c.layout)
      .Set("experience", c.experience).Set("appearance", c.appearance)
      .Set("density", c.density).Set("performance", c.performance)
      .Set("accent", c.accent).Set("memorySaver", c.memory_saver)
      .Set("batterySaver", c.battery_saver)
      .Set("backgroundSuspension", c.background_suspension);
}

base::DictValue GetSetupState(Profile* profile) {
  const auto& state = profile->GetPrefs()->GetDict(kSetupPref);
  auto result = state.Clone();
  if (!CanUseState(state)) {
    result.Set("readOnly", true);
    return result;
  }
  // v0 is the empty, pre-Aether state. Its migration is additive and local.
  result.Set("version", kSchemaVersion);
  if (state.FindBool("completed").value_or(false) &&
      !state.FindBool("editing").value_or(false) &&
      !state.FindBool("pending").value_or(false)) {
    // Native Settings remain the source of truth when setup is reopened.
    Config current;
    auto* prefs = profile->GetPrefs();
    const auto* committed = state.FindDict("config");
    if (committed) {
      current = ParseConfig(*committed).value_or(Config());
    }
    const int layout = prefs->GetInteger(prefs::kHeliumLayout);
    current.layout = layout >= 0 && layout <= 2 ? layout : current.layout;
    current.density = prefs->GetInteger(kDensityPref);
    current.appearance = prefs->GetInteger(prefs::kBrowserColorScheme);
    current.accent = prefs->GetBoolean(prefs::kGrayscaleThemeEnabled) ? 0 :
                    prefs->GetInteger(prefs::kUserColor) & 0xffffff;
    current.experience = prefs->GetBoolean(prefs::kShowHomeButton) ? 2 :
                         prefs->GetBoolean(prefs::kShowAvatarButton) ? 1 : 0;
    auto* local = g_browser_process->local_state();
    current.memory_saver = local->GetInteger(tuning::kMemorySaverModeState) == 2;
    current.battery_saver = local->GetInteger(tuning::kBatterySaverModeState) != 0;
    current.background_suspension = local->GetBoolean(tuning::kTabFreezingEnabled);
    current.performance = local->GetInteger(tuning::kBatterySaverModeState) == 2 ? 2 :
                          local->GetInteger(tuning::kMemorySaverModeAggressiveness) == 2 ? 1 : 0;
    result.Set("draft", ToValue(IsValid(current) ? current : Config()));
  }
  if (!result.FindDict("draft")) {
    const auto* committed = result.FindDict("config");
    result.Set("draft", committed ? committed->Clone() : ToValue(Config()));
  }
  result.Set("step", IsValidStep(result.FindInt("step").value_or(0))
                         ? result.FindInt("step").value_or(0) : 0);
  return result;
}

bool SetupCompleted(Profile* profile) {
  const auto& state = profile->GetPrefs()->GetDict(kSetupPref);
  // A downgrade must not show a setup page that could overwrite newer settings.
  return !CanUseState(state) || state.FindBool("completed").value_or(false);
}

std::string ValidateApplication(Profile* profile, const Config& config,
                                bool allow_pending) {
  if (profile->IsOffTheRecord() || profile->IsGuestSession()) {
    return "Setup is available in a regular profile only.";
  }
  if (!IsValid(config) || !CanUseState(profile->GetPrefs()->GetDict(kSetupPref))) {
    return "Unsupported settings schema or configuration.";
  }
  if (!allow_pending && profile->GetPrefs()->GetDict(kSetupPref)
                            .FindBool("pending").value_or(false)) {
    return "Another setup transaction is pending. Restart Aether to recover it.";
  }
  const char* profile_keys[] = {kSetupPref, kDensityPref, prefs::kHeliumLayout,
      prefs::kShowHomeButton, prefs::kShowAvatarButton,
      prefs::kBrowserColorScheme, prefs::kUserColor,
      prefs::kCurrentThemeID, prefs::kGrayscaleThemeEnabled};
  for (const char* key : profile_keys) {
    const auto* pref = profile->GetPrefs()->FindPreference(key);
    if (!pref || !pref->IsUserModifiable()) {
      return std::string("Setting is unavailable or managed: ") + key;
    }
  }
  const char* global_keys[] = {tuning::kMemorySaverModeState,
      tuning::kMemorySaverModeAggressiveness, tuning::kBatterySaverModeState,
      tuning::kTabFreezingEnabled};
  for (const char* key : global_keys) {
    const auto* pref = g_browser_process->local_state()->FindPreference(key);
    if (!pref || !pref->IsUserModifiable()) {
      return std::string("Performance setting is unavailable or managed: ") + key;
    }
  }
  return {};
}

void SaveDraft(Profile* profile, const Config& config, int step) {
  CHECK(IsValid(config));
  CHECK(IsValidStep(step));
  auto state = GetSetupState(profile);
  state.Set("draft", ToValue(config));
  state.Set("step", step);
  state.Set("editing", true);
  profile->GetPrefs()->SetDict(kSetupPref, std::move(state));
}

void CommitConfiguration(Profile* profile, const Config& config,
                         ApplyCallback done) {
  CHECK(ValidateApplication(profile, config).empty());
  auto state = GetSetupState(profile);
  state.Set("config", ToValue(config));
  state.Set("draft", ToValue(config));
  state.Set("pending", true);
  const int previous = state.FindInt("generation").value_or(0);
  const int generation = previous >= std::numeric_limits<int>::max() ? 1 : previous + 1;
  state.Set("generation", generation);
  profile->GetPrefs()->SetDict(kSetupPref, std::move(state));
  // Persist intent before touching any live preference.
  profile->GetPrefs()->CommitPendingWrite(
      base::BindOnce(&ApplyJournal, profile->GetWeakPtr(), generation,
                     std::move(done)));
}

void RecoverPendingConfiguration(Profile* profile) {
  if (!profile->IsOffTheRecord() &&
      profile->GetPrefs()->GetDict(kSetupPref).FindBool("pending").value_or(false)) {
    ApplyJournal(profile->GetWeakPtr(), profile->GetPrefs()->GetDict(kSetupPref)
                                          .FindInt("generation").value_or(0),
                 base::BindOnce([](std::string) {}));
  }
}
}  // namespace aether
