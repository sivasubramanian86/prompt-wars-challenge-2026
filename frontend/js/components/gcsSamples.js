/**
 * GCS Sample Catalogue Discovery Component
 */

import { state } from '../state.js';
import { fetchSamples, ingestGcsSample } from '../api.js';
import { switchMainView } from './nav.js';
import { resetSteps, animatePipeline, renderResult, setStatus } from './commandCenter.js';
import { logIncidentFeed } from './incidentFeed.js';

export async function loadGcsSamples() {
  const grid = document.getElementById('gcs-grid');
  const catGrid = document.getElementById('gcs-catalogue-grid');
  const loading = document.getElementById('gcs-loading');
  try {
    const data = await fetchSamples();
    state.gcsSamplesLoaded = true;

    if (loading) loading.style.display = 'none';

    const cardsHtml = data.samples.map(s => `
      <div class="gcs-card" data-domain="${s.domain}" data-uri="${s.uri}"
           title="${s.uri}">
        <div class="gcs-card-label">${s.label}</div>
        <div class="gcs-card-meta">
          <span class="gcs-card-type ${s.type}">${s.type}</span>
          <span class="gcs-card-domain" style="margin-left:auto;font-size:10px;color:var(--text-secondary)">${s.domain}</span>
        </div>
      </div>
    `).join('');

    if (grid) {
      grid.innerHTML = cardsHtml;
      attachCardListeners(grid);
    }
    if (catGrid) {
      catGrid.innerHTML = cardsHtml;
      attachCardListeners(catGrid);
    }
  } catch (err) {
    if (loading) loading.textContent = `Failed to load samples: ${err.message}`;
  }
}

function attachCardListeners(container) {
  container.querySelectorAll('.gcs-card').forEach(card => {
    card.addEventListener('click', () => {
      const uri = card.getAttribute('data-uri');
      const label = card.querySelector('.gcs-card-label')?.textContent || '';
      processGcsSample(uri, label);
    });
  });
}

export async function processGcsSample(gcsUri, label) {
  switchMainView('command');
  resetSteps();
  const stepCtrl = animatePipeline();

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  document.getElementById('submit-label').textContent = '⏳ PROCESSING GCS SAMPLE…';
  setStatus('PROCESSING', true);

  document.querySelectorAll('.gcs-card').forEach(c => c.style.outline = 'none');
  const selected = document.querySelectorAll(`.gcs-card[data-uri="${gcsUri}"]`);
  selected.forEach(s => s.style.outline = '1px solid var(--cyan)');

  const t0 = Date.now();
  try {
    const skills = [];
    if (document.getElementById('skill-security')?.checked) skills.push('security');
    if (document.getElementById('skill-memory')?.checked) skills.push('memory');

    const data = await ingestGcsSample(gcsUri, skills);
    const latencyMs = Date.now() - t0;
    const hasWarning = data.verification_flag !== 'PASS';

    stepCtrl.finish(hasWarning);
    renderResult(data, latencyMs);
    logIncidentFeed(data, latencyMs);
    setStatus('ONLINE', false);
  } catch (err) {
    stepCtrl.error();
    setStatus('ERROR', false);
    alert(`GCS pipeline error: ${err.message}`);
  } finally {
    btn.disabled = false;
    document.getElementById('submit-label').textContent = '▶ PROCESS INCIDENT PAYLOAD';
    document.querySelectorAll('.gcs-card').forEach(c => c.style.outline = 'none');
  }
}
