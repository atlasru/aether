// Copyright 2026 The Aether Authors
// SPDX-License-Identifier: GPL-3.0-only
#include "chrome/browser/ui/webui/onboarding/aether_setup_handler.h"

#include "base/functional/bind.h"
#include "chrome/browser/aether/preferences.h"
#include "chrome/browser/profiles/profile.h"
#include "components/prefs/pref_service.h"
#include "content/public/browser/web_ui.h"

AetherSetupHandler::AetherSetupHandler() = default;
AetherSetupHandler::~AetherSetupHandler() = default;

void AetherSetupHandler::RegisterMessages() {
  web_ui()->RegisterMessageCallback("aetherGetSetup",
      base::BindRepeating(&AetherSetupHandler::HandleGet, base::Unretained(this)));
  web_ui()->RegisterMessageCallback("aetherSaveDraft",
      base::BindRepeating(&AetherSetupHandler::HandleSave, base::Unretained(this)));
  web_ui()->RegisterMessageCallback("aetherApplySetup",
      base::BindRepeating(&AetherSetupHandler::HandleApply, base::Unretained(this)));
}

void AetherSetupHandler::HandleGet(const base::ListValue& args) {
  if (args.size() != 1 || !args[0].is_string()) {
    return;
  }
  AllowJavascript();
  ResolveJavascriptCallback(args[0],
      aether::GetSetupState(Profile::FromWebUI(web_ui())));
}

void AetherSetupHandler::HandleSave(const base::ListValue& args) {
  if (args.empty() || !args[0].is_string()) {
    return;
  }
  AllowJavascript();
  auto* profile = Profile::FromWebUI(web_ui());
  if (args.size() != 3 || !args[1].is_dict() || !args[2].is_int() ||
      !aether::IsValidStep(args[2].GetInt()) || applying_) {
    RejectJavascriptCallback(args[0], base::Value("Invalid draft or setup is busy."));
    return;
  }
  auto config = aether::ParseConfig(args[1].GetDict());
  const auto error = config ? aether::ValidateApplication(profile, *config)
                            : "Invalid configuration.";
  if (!error.empty()) {
    RejectJavascriptCallback(args[0], base::Value(error));
    return;
  }
  aether::SaveDraft(profile, *config, args[2].GetInt());
  // Acknowledge only after the draft has reached the preference writer.
  profile->GetPrefs()->CommitPendingWrite(base::BindOnce(
      [](base::WeakPtr<AetherSetupHandler> handler, base::Value callback) {
        if (handler && handler->IsJavascriptAllowed()) {
          handler->ResolveJavascriptCallback(callback, base::Value(true));
        }
      }, weak_factory_.GetWeakPtr(), args[0].Clone()));
}

void AetherSetupHandler::HandleApply(const base::ListValue& args) {
  if (args.empty() || !args[0].is_string()) {
    return;
  }
  AllowJavascript();
  auto* profile = Profile::FromWebUI(web_ui());
  if (args.size() != 2 || !args[1].is_dict() || applying_) {
    RejectJavascriptCallback(args[0], base::Value("Invalid configuration or setup is busy."));
    return;
  }
  auto config = aether::ParseConfig(args[1].GetDict());
  const auto error = config ? aether::ValidateApplication(profile, *config)
                            : "Invalid configuration.";
  if (!error.empty()) {
    RejectJavascriptCallback(args[0], base::Value(error));
    return;
  }
  applying_ = true;
  aether::CommitConfiguration(profile, *config,
      base::BindOnce(&AetherSetupHandler::OnApplied, weak_factory_.GetWeakPtr(),
                     args[0].Clone()));
}

void AetherSetupHandler::OnApplied(base::Value callback) {
  applying_ = false;
  if (IsJavascriptAllowed()) {
    ResolveJavascriptCallback(callback, base::Value(true));
  }
}
