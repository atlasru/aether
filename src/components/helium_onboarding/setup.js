// Copyright 2026 The Aether Authors. SPDX-License-Identifier: GPL-3.0-only
import {sendWithPromise} from 'chrome://resources/js/cr.js';
import {DEFAULTS, SetupModel} from './state.mjs';

const $ = selector => document.querySelector(selector);
let model;
let busy = true;
let pending = Promise.resolve();

function error(reason) {
  $('#error').textContent = String(reason?.message ?? reason);
  $('#error').hidden = false;
}

function enqueueSave() {
  const state = model.snapshot();
  // Preserve input order even if writes finish on different event-loop turns.
  const operation = pending.then(() => sendWithPromise('aetherSaveDraft', state.draft, state.step));
  pending = operation.catch(reason => { error(reason); });
  return operation;
}

function setBusy(value) {
  busy = value;
  $('#shell').setAttribute('aria-busy', String(value));
  for (const button of document.querySelectorAll('button')) button.disabled = value || !!model?.readOnly;
  for (const input of document.querySelectorAll('input')) input.disabled = value || !!model?.readOnly;
}

function render(focus = false) {
  for (const section of document.querySelectorAll('[data-step]')) {
    section.hidden = Number(section.dataset.step) !== model.step;
  }
  $('#progress').textContent = `${model.step + 1} of 6`;
  $('#back').hidden = model.step === 0;
  $('#next').textContent = model.step === 0 ? 'Get started' : model.step === 5 ? 'Start browsing' : 'Continue';
  for (const input of document.querySelectorAll('input[name]')) {
    input.checked = input.type === 'checkbox' ? model.config[input.name] : Number(input.value) === model.config[input.name];
  }
  const c = model.config;
  document.documentElement.dataset.appearance = ['system', 'light', 'dark'][c.appearance];
  const accent = c.accent ? `#${c.accent.toString(16).padStart(6, '0')}` : '#6d53d5';
  document.documentElement.style.setProperty('--user-accent', accent);
  $('#custom-accent').value = accent;
  $('#live-preview').dataset.layout = String(c.layout);
  $('#live-preview').dataset.density = String(c.density);
  $('#profile-detail').textContent = [
    'Balanced keeps moderate memory reclamation and saves energy when battery is low.',
    'Memory Saver uses Chromium’s aggressive mode when Memory Saver is enabled. Inactive pages may reload more often.',
    'Battery Saver activates whenever running on battery, when enabled. Animations and some background activity may slow down.'
  ][c.performance];
  $('#summary').replaceChildren();
  const rows = [['Layout', ['Classic', 'Compact', 'Vertical'][c.layout]],
    ['Interface', ['Simplicity', 'Balanced', 'Control'][c.experience]],
    ['Appearance', ['Follow system', 'Light', 'Dark'][c.appearance]],
    ['Density', ['Comfortable', 'Compact'][c.density]],
    ['Resource profile', ['Balanced', 'Memory Saver', 'Battery Saver'][c.performance]],
    ['Memory Saver', c.memorySaver ? 'On' : 'Off'], ['Battery Saver', c.batterySaver ? 'On' : 'Off'],
    ['Background suspension', c.backgroundSuspension ? 'On' : 'Off']];
  for (const [label, value] of rows) {
    const dt = document.createElement('dt'); dt.textContent = label;
    const dd = document.createElement('dd'); dd.textContent = value;
    $('#summary').append(dt, dd);
  }
  if (focus) $(`#title-${model.step}`).focus();
}

async function changeStep(step) {
  if (busy || model.readOnly) return;
  model.go(step);
  render(true);
  try { await enqueueSave(); } catch (reason) { error(reason); }
}

async function apply(skip = false) {
  if (busy || model.readOnly) return;
  setBusy(true);
  $('#error').hidden = true;
  try {
    await pending;
    // Skip uses safe defaults on first run. Reopening setup never resets an
    // existing configuration merely because the user leaves it.
    const configuration = skip && !model.completed ? {...DEFAULTS} : {...model.config};
    await sendWithPromise('aetherApplySetup', configuration);
    window.location.replace('chrome://newtab/');
  } catch (reason) {
    error(reason);
    setBusy(false);
  }
}

document.addEventListener('change', event => {
  const input = event.target;
  if (!(input instanceof HTMLInputElement) || busy || model?.readOnly) return;
  try {
    if (input.id === 'custom-accent') model.update('accent', Number.parseInt(input.value.slice(1), 16));
    else if (input.name) model.update(input.name, input.type === 'checkbox' ? input.checked : Number(input.value));
    render();
    enqueueSave().catch(error);
  } catch (reason) { error(reason); }
});
$('#next').addEventListener('click', () => model.step === 5 ? apply() : changeStep(model.step + 1));
$('#back').addEventListener('click', () => changeStep(model.step - 1));
$('#change').addEventListener('click', () => changeStep(1));
$('#skip').addEventListener('click', () => model.completed ? window.location.replace('chrome://newtab/') : apply(true));
document.addEventListener('keydown', event => {
  if (event.altKey && event.key === 'ArrowLeft' && model?.step > 0) {
    event.preventDefault(); changeStep(model.step - 1);
  }
});

try {
  const state = await sendWithPromise('aetherGetSetup');
  model = new SetupModel(state);
  model.completed = !!state.completed;
  if (model.completed) $('#skip').textContent = 'Keep current settings';
  render();
  setBusy(false);
  if (model.readOnly) error('These settings belong to a newer Aether version. Use that version to change them.');
} catch (reason) { error(reason); }
