// Copyright 2026 The Aether Authors. SPDX-License-Identifier: GPL-3.0-only
import test from 'node:test';
import assert from 'node:assert/strict';
import {DEFAULTS, SetupModel, validConfig} from '../src/components/helium_onboarding/state.mjs';

test('first run and v0 migration select safe defaults', () => {
  for (const state of [{}, {version: 0}]) {
    const model = new SetupModel(state);
    assert.deepEqual(model.config, DEFAULTS);
    assert.equal(model.step, 0);
    assert.equal(model.readOnly, false);
  }
});
test('saved choices and back navigation survive reload', () => {
  let model = new SetupModel();
  model.update('layout', 2);
  model.update('appearance', 2);
  model.go(4);
  model.go(3);
  model = new SetupModel(model.snapshot());
  assert.equal(model.config.layout, 2);
  assert.equal(model.config.appearance, 2);
  assert.equal(model.step, 3);
});
test('newer or malformed schema cannot overwrite preferences', () => {
  for (const version of [-1, 2, '1', null, NaN]) {
    // null is an absent legacy version and is intentionally migrated.
    if (version === null) continue;
    const model = new SetupModel({version, draft: {...DEFAULTS, layout: 0}});
    assert.equal(model.readOnly, true);
    assert.throws(() => model.update('layout', 2));
  }
});
test('corrupt drafts recover without inventing selections', () => {
  for (const draft of [null, [], {layout: 2}, {...DEFAULTS, density: 2},
    {...DEFAULTS, accent: 0x1000000}, {...DEFAULTS, memorySaver: 1},
    {...DEFAULTS, unexpected: true}]) {
    assert.equal(validConfig(draft), false);
    assert.deepEqual(new SetupModel({draft}).config, DEFAULTS);
  }
});
test('unsupported input is rejected without modifying the last valid state', () => {
  const model = new SetupModel();
  for (const [key, value] of [['layout', 3], ['appearance', -1], ['density', .5],
    ['accent', '#ffffff'], ['memorySaver', 'true'], ['sandbox', false], ['performance', NaN]]) {
    assert.throws(() => model.update(key, value));
    assert.deepEqual(model.config, DEFAULTS);
  }
});
test('all interface presets preserve independent resource choices', () => {
  const model = new SetupModel();
  model.update('memorySaver', false);
  model.update('batterySaver', false);
  for (const experience of [0, 1, 2]) {
    model.update('experience', experience);
    assert.equal(model.config.memorySaver, false);
    assert.equal(model.config.batterySaver, false);
    assert.equal(model.config.backgroundSuspension, true);
  }
});
test('snapshots own their data; queued saves cannot change under later edits', () => {
  const model = new SetupModel();
  const pending = model.snapshot();
  model.update('layout', 0);
  assert.equal(pending.draft.layout, 1);
  pending.draft.appearance = 2;
  assert.equal(model.config.appearance, 0);
});
test('reopening completed setup starts at welcome with saved selections', () => {
  const model = new SetupModel({completed: true, step: 5, draft: {...DEFAULTS, layout: 2}});
  assert.equal(model.step, 0);
  assert.equal(model.config.layout, 2);
});
test('step limits hold under malformed persisted state and navigation', () => {
  for (const step of [-1, 6, '3', NaN, 1.5]) {
    assert.equal(new SetupModel({step}).step, 0);
    assert.throws(() => new SetupModel().go(step));
  }
});
