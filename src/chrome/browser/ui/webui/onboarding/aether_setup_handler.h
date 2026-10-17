// Copyright 2026 The Aether Authors
// SPDX-License-Identifier: GPL-3.0-only
#ifndef CHROME_BROWSER_UI_WEBUI_ONBOARDING_AETHER_SETUP_HANDLER_H_
#define CHROME_BROWSER_UI_WEBUI_ONBOARDING_AETHER_SETUP_HANDLER_H_

#include <string>

#include "base/memory/weak_ptr.h"
#include "content/public/browser/web_ui_message_handler.h"

class AetherSetupHandler : public content::WebUIMessageHandler {
 public:
  AetherSetupHandler();
  ~AetherSetupHandler() override;
  void RegisterMessages() override;

 private:
  void HandleGet(const base::ListValue& args);
  void HandleSave(const base::ListValue& args);
  void HandleApply(const base::ListValue& args);
  void OnApplied(base::Value callback, std::string error);
  bool applying_ = false;
  base::WeakPtrFactory<AetherSetupHandler> weak_factory_{this};
};
#endif  // CHROME_BROWSER_UI_WEBUI_ONBOARDING_AETHER_SETUP_HANDLER_H_
