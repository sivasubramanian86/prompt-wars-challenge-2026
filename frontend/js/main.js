/**
 * Main Application Initializer & Orchestrator
 */

import { initNavigation, switchMainView } from './components/nav.js';
import { initCommandCenter, switchTab } from './components/commandCenter.js';
import { initHitlMonitor } from './components/hitlMonitor.js';
import { initAnalyticsView } from './components/analyticsView.js';

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initCommandCenter();
  initHitlMonitor();
  initAnalyticsView();

  switchMainView('command');
  switchTab('text');
});
