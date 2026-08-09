/**
 * Human-In-The-Loop (HITL) Pub/Sub Queue Monitor Component
 */

import { state } from '../state.js';

export function initHitlMonitor() {
  const pendingEl = document.getElementById('hitl-pending-count');
  if (pendingEl) pendingEl.textContent = state.hitlPendingCount;

  const verifiedEl = document.getElementById('hitl-verified-count');
  if (verifiedEl) verifiedEl.textContent = state.hitlVerifiedCount;
}
