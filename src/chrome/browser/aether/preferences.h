// Copyright 2026 The Aether Authors
// SPDX-License-Identifier: GPL-3.0-only
#ifndef CHROME_BROWSER_AETHER_PREFERENCES_H_
#define CHROME_BROWSER_AETHER_PREFERENCES_H_

#include <optional>
#include <string>

#include "base/functional/callback_forward.h"
#include "base/values.h"
#include "chrome/browser/aether/config.h"

class Profile;
namespace aether {
std::optional<Config> ParseConfig(const base::DictValue& value);
base::DictValue ToValue(const Config& config);
base::DictValue GetSetupState(Profile* profile);
bool SetupCompleted(Profile* profile);
// Reject managed preferences before making any change.
std::string ValidateApplication(Profile* profile, const Config& config,
                                bool allow_pending = false);
void SaveDraft(Profile* profile, const Config& config, int step);
void CommitConfiguration(Profile* profile, const Config& config,
                         base::OnceClosure done);
void RecoverPendingConfiguration(Profile* profile);
}  // namespace aether
#endif  // CHROME_BROWSER_AETHER_PREFERENCES_H_
