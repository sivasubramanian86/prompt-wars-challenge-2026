/**
 * Real-Time Processed Incident Feed Component
 */

import { state } from '../state.js';

export function logIncidentFeed(data, latencyMs) {
  const shortId = String(data.incident_id || '0000').split('-')[0].toUpperCase();
  const timeStr = new Date().toLocaleTimeString();

  state.sessionFeed.unshift({
    timestamp: timeStr,
    id: `INC-${shortId}`,
    domain: data.domain_classification || 'General',
    urgency: data.urgency_level || 'LOW',
    flag: data.verification_flag || 'PASS',
    latency: `${latencyMs}ms`,
    target: data.target_system || 'Emergency_Dispatch'
  });

  renderFeedTable();
  updateHitlStats(data, timeStr, shortId);
}

function renderFeedTable() {
  const tbody = document.getElementById('feed-tbody');
  if (!tbody) return;

  if (state.sessionFeed.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-table">No incidents processed in this session yet. Submit an incident from Command Center.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.sessionFeed.map(item => `
    <tr>
      <td style="font-family:var(--font-mono)">${item.timestamp}</td>
      <td style="font-family:var(--font-mono);color:var(--cyan)">${item.id}</td>
      <td><strong>${item.domain}</strong></td>
      <td><span class="gcs-card-type ${item.urgency.toLowerCase()}">${item.urgency}</span></td>
      <td><span class="gcs-card-type ${item.flag === 'PASS' ? 'text' : 'image'}">${item.flag}</span></td>
      <td style="font-family:var(--font-mono)">${item.latency}</td>
      <td style="color:var(--text-secondary)">${item.target}</td>
    </tr>
  `).join('');

  const feedBadge = document.getElementById('feed-count-badge');
  if (feedBadge) feedBadge.textContent = `${state.sessionFeed.length} RECORDED`;
}

function updateHitlStats(data, timeStr, shortId) {
  if (data.verification_flag === 'PENDING_HITL') {
    state.hitlPendingCount++;
    const pendingEl = document.getElementById('hitl-pending-count');
    if (pendingEl) pendingEl.textContent = state.hitlPendingCount;

    const hitlList = document.getElementById('hitl-item-list');
    if (hitlList) {
      if (state.hitlPendingCount === 1) hitlList.innerHTML = '';
      hitlList.innerHTML += `
        <div class="hitl-banner" style="margin-top:10px">
          <div>
            <strong>[${timeStr}] Escalated ${shortId}</strong> &bull; Domain: ${data.domain_classification} &bull; Urgency: ${data.urgency_level}
            <p style="font-size:11px;color:var(--text-secondary)">Reason: Missing critical parameters or verification gate requirement.</p>
          </div>
        </div>
      `;
    }
  } else {
    state.hitlVerifiedCount++;
    const verifiedEl = document.getElementById('hitl-verified-count');
    if (verifiedEl) verifiedEl.textContent = state.hitlVerifiedCount;
  }
}
