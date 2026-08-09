/**
 * Omni-Bridge API Service Client
 */

import { CONFIG } from './config.js';

export async function fetchSamples() {
  const resp = await fetch(`${CONFIG.API_BASE}/v1/samples`);
  if (!resp.ok) {
    throw new Error(`Failed to load samples: ${resp.statusText}`);
  }
  return await resp.json();
}

export async function ingestIncident(formData, skills = []) {
  const resp = await fetch(`${CONFIG.API_BASE}/v1/incident/ingest`, {
    method: 'POST',
    headers: { 'X-Omni-Skills': skills.join(',') },
    body: formData,
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return await resp.json();
}

export async function ingestGcsSample(gcsUri, skills = []) {
  const resp = await fetch(`${CONFIG.API_BASE}/v1/incident/ingest-gcs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Omni-Skills': skills.join(',')
    },
    body: JSON.stringify({ gcs_uri: gcsUri }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return await resp.json();
}
