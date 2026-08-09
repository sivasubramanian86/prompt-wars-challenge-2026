/**
 * Navigation Bar Component
 */

import { state } from '../state.js';
import { loadGcsSamples } from './gcsSamples.js';

export function initNavigation() {
  ['command', 'samples', 'feed', 'hitl', 'analytics'].forEach(view => {
    const btn = document.getElementById(`nav-${view}`);
    if (btn) {
      btn.addEventListener('click', () => switchMainView(view));
    }
  });
}

export function switchMainView(view) {
  state.activeMainView = view;
  ['command', 'samples', 'feed', 'hitl', 'analytics'].forEach(v => {
    const btn = document.getElementById(`nav-${v}`);
    const sec = document.getElementById(`view-${v}`);
    if (btn) btn.classList.toggle('active', v === view);
    if (sec) sec.classList.toggle('active', v === view);
  });

  if (view === 'samples' && !state.gcsSamplesLoaded) {
    loadGcsSamples();
  }
}
