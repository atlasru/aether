// Copyright 2026 The Aether Authors. SPDX-License-Identifier: GPL-3.0-only
export const DEFAULTS = Object.freeze({layout: 1, experience: 1, appearance: 0,
  density: 0, performance: 0, accent: 0, memorySaver: true, batterySaver: true,
  backgroundSuspension: true});
export const SCHEMA = 1;

export function validConfig(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      Object.keys(value).length !== Object.keys(DEFAULTS).length) return false;
  for (const key of ['layout', 'experience', 'appearance', 'performance']) {
    if (!Number.isInteger(value[key]) || value[key] < 0 || value[key] > 2) return false;
  }
  return Number.isInteger(value.density) && value.density >= 0 && value.density <= 1 &&
    Number.isInteger(value.accent) && value.accent >= 0 && value.accent <= 0xffffff &&
    ['memorySaver', 'batterySaver', 'backgroundSuspension'].every(k => typeof value[k] === 'boolean');
}

export class SetupModel {
  constructor(state = {}) {
    const version = state.version ?? 0;
    this.readOnly = !Number.isInteger(version) || version < 0 || version > SCHEMA || !!state.readOnly;
    this.config = {...(validConfig(state.draft) ? state.draft : DEFAULTS)};
    this.step = (!state.completed || state.editing) && Number.isInteger(state.step) && state.step >= 0 &&
      state.step <= 5 ? state.step : 0;
  }
  update(key, value) {
    if (this.readOnly) throw new Error('Settings were created by a newer Aether build.');
    const next = {...this.config, [key]: value};
    if (!validConfig(next)) throw new Error('Invalid setup selection.');
    this.config = next;
  }
  go(step) {
    if (!Number.isInteger(step) || step < 0 || step > 5) throw new Error('Invalid setup step.');
    this.step = step;
  }
  snapshot() { return {version: SCHEMA, draft: {...this.config}, step: this.step}; }
}
