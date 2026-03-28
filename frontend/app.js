/**
 * Omni-Bridge Core Orchestrator — Frontend JS
 *
 * Responsibilities:
 *  - Tab switching (text / audio)
 *  - Audio recording via MediaRecorder + waveform visualisation
 *  - POST /v1/incident/ingest (multipart form)
 *  - Pipeline step animation (simulated progress during API call)
 *  - JSON syntax highlighting
 *  - DEFCON urgency indicator
 *  - Verification flag display
 *  - Missing data warnings
 */

'use strict';

/* ── State ────────────────────────────────────────────────────────────────── */
let activeTab = 'text';
let mediaRecorder = null;
let audioChunks = [];
let recordedBlob = null;
let recordingInterval = null;
let recordingSeconds = 0;
let audioCtx = null;
let analyser = null;
let animFrameId = null;
let pipelineTimer = null;

/* ── Tab switching ────────────────────────────────────────────────────────── */
function switchTab(tab) {
  activeTab = tab;
  ['text', 'audio', 'gcs'].forEach(t => {
    const btn = document.getElementById(`tab-${t}`);
    if (btn) {
      btn.classList.toggle('active', t === tab);
      btn.setAttribute('aria-selected', t === tab);
    }
  });
  document.getElementById('text-panel').style.display  = tab === 'text'  ? 'block' : 'none';
  document.getElementById('audio-panel').style.display = tab === 'audio' ? 'block' : 'none';
  document.getElementById('gcs-panel').style.display   = tab === 'gcs'   ? 'block' : 'none';

  // Lazy-load the sample catalogue the first time
  if (tab === 'gcs' && !window._gcsSamplesLoaded) loadGcsSamples();
}

/* ── GCS sample catalogue ─────────────────────────────────────────────────── */
async function loadGcsSamples() {
  const grid    = document.getElementById('gcs-grid');
  const loading = document.getElementById('gcs-loading');
  try {
    const resp  = await fetch('/v1/samples');
    const data  = await resp.json();
    window._gcsSamplesLoaded = true;

    loading.style.display = 'none';
    grid.innerHTML = data.samples.map(s => `
      <div class="gcs-card" data-domain="${s.domain}" data-uri="${s.uri}"
           onclick="processGcsSample('${s.uri}', '${s.label}')"
           title="${s.uri}">
        <div class="gcs-card-label">${s.label}</div>
        <div class="gcs-card-meta">
          <span class="gcs-card-type ${s.type}">${s.type}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    loading.textContent = `Failed to load samples: ${err.message}`;
  }
}

async function processGcsSample(gcsUri, label) {
  resetSteps();
  const stepCtrl = animatePipeline();

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  document.getElementById('submit-label').textContent = '⏳ PROCESSING…';
  setStatus('PROCESSING', true);

  // Highlight selected card
  document.querySelectorAll('.gcs-card').forEach(c => c.style.outline = 'none');
  const selected = document.querySelector(`.gcs-card[data-uri="${gcsUri}"]`);
  if (selected) selected.style.outline = '1px solid var(--cyan)';

  const t0 = Date.now();
  try {
    const skills = [];
    if (document.getElementById('skill-security')?.checked) skills.push('security');
    if (document.getElementById('skill-memory')?.checked) skills.push('memory');

    const resp = await fetch('/v1/incident/ingest-gcs', {
      method:  'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-Omni-Skills': skills.join(',')
      },
      body:    JSON.stringify({ gcs_uri: gcsUri }),
    });

    const latencyMs = Date.now() - t0;
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    const hasWarning = data.verification_flag !== 'PASS';
    stepCtrl.finish(hasWarning);
    renderResult(data, latencyMs);
    setStatus('READY', false);
  } catch (err) {
    stepCtrl.error();
    setStatus('ERROR', false);
    
    const emptyState = document.getElementById('empty-state');
    if (emptyState) emptyState.style.display = 'block';
    const jsonOutput = document.getElementById('json-output');
    if (jsonOutput) jsonOutput.style.display = 'none';
    
    const defconBar = document.getElementById('defcon-bar');
    if (defconBar) defconBar.style.display = 'none';
    const vflagContainer = document.getElementById('vflag-container');
    if (vflagContainer) vflagContainer.style.display = 'none';
    const missingList = document.getElementById('missing-list');
    if (missingList) missingList.style.display = 'none';

    alert(`GCS pipeline error: ${err.message}`);
  } finally {
    btn.disabled = false;
    document.getElementById('submit-label').textContent = '▶ PROCESS INCIDENT';
    document.querySelectorAll('.gcs-card').forEach(c => c.style.outline = 'none');
  }
}


/* ── Audio recording ──────────────────────────────────────────────────────── */
async function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    stopRecording();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    startRecording(stream);
  } catch (err) {
    document.getElementById('audio-status').textContent = `Microphone error: ${err.message}`;
  }
}

function startRecording(stream) {
  audioChunks = [];
  recordedBlob = null;
  recordingSeconds = 0;

  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  mediaRecorder.onstop = () => {
    recordedBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
    document.getElementById('audio-status').textContent =
      `Recording saved — ${(recordedBlob.size / 1024).toFixed(1)} KB. Click "Process Incident" to analyse.`;
    stream.getTracks().forEach(t => t.stop());
    stopWaveform();
  };

  mediaRecorder.start(100);
  startWaveform(stream);

  const btn = document.getElementById('record-btn');
  btn.classList.add('recording');
  document.getElementById('record-label').textContent = 'Recording… click to stop';

  recordingInterval = setInterval(() => {
    recordingSeconds++;
    const m = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
    const s = String(recordingSeconds % 60).padStart(2, '0');
    document.getElementById('record-timer').textContent = `${m}:${s}`;
  }, 1000);

  document.getElementById('audio-status').textContent = 'Recording in progress…';
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
  clearInterval(recordingInterval);
  const btn = document.getElementById('record-btn');
  btn.classList.remove('recording');
  document.getElementById('record-label').textContent = 'Click to start recording';
  document.getElementById('record-timer').textContent = '00:00';
}

/* ── Waveform ─────────────────────────────────────────────────────────────── */
function startWaveform(stream) {
  audioCtx = new AudioContext();
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  audioCtx.createMediaStreamSource(stream).connect(analyser);

  const canvas = document.getElementById('waveform');
  const ctx = canvas.getContext('2d');
  const buf = new Uint8Array(analyser.frequencyBinCount);

  function draw() {
    animFrameId = requestAnimationFrame(draw);
    analyser.getByteFrequencyData(buf);
    canvas.width = canvas.offsetWidth;
    canvas.height = 48;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const barW = (canvas.width / buf.length) * 2.2;
    let x = 0;
    buf.forEach(val => {
      const h = (val / 255) * canvas.height;
      const pct = val / 255;
      ctx.fillStyle = `rgba(${Math.round(255 * pct)}, ${Math.round(212 * (1 - pct))}, 255, 0.85)`;
      ctx.fillRect(x, canvas.height - h, barW, h);
      x += barW + 1;
    });
  }
  draw();
}

function stopWaveform() {
  if (animFrameId) cancelAnimationFrame(animFrameId);
  if (audioCtx) audioCtx.close();
  const canvas = document.getElementById('waveform');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

/* ── Pipeline step animation ──────────────────────────────────────────────── */
function resetSteps() {
  for (let i = 0; i < 5; i++) {
    const dot = document.getElementById(`dot-${i}`);
    dot.className = 'step-dot';
    dot.textContent = `0${i + 1}`;
  }
}

function animatePipeline(onDone) {
  let step = 0;
  const labels = ['01', '02', '03', '04', '05'];
  const delays = [400, 700, 900, 1100, 1300]; // progressive delays

  function activateStep(i) {
    if (i > 0) {
      const prev = document.getElementById(`dot-${i - 1}`);
      prev.className = 'step-dot done';
      prev.textContent = '✓';
    }
    const dot = document.getElementById(`dot-${i}`);
    dot.className = 'step-dot active';
    dot.textContent = labels[i];
  }

  pipelineTimer = setTimeout(function tick() {
    activateStep(step);
    step++;
    if (step < 5) {
      pipelineTimer = setTimeout(tick, delays[step - 1]);
    }
  }, 0);

  // Caller resolves steps to done when API returns
  return {
    finish(hasWarning) {
      clearTimeout(pipelineTimer);
      for (let i = 0; i < 5; i++) {
        const dot = document.getElementById(`dot-${i}`);
        dot.textContent = i === 3 && hasWarning ? '!' : '✓';
        dot.className = `step-dot ${i === 3 && hasWarning ? 'warn' : 'done'}`;
      }
    },
    error() {
      clearTimeout(pipelineTimer);
      for (let i = 0; i < 5; i++) {
        document.getElementById(`dot-${i}`).className = 'step-dot error';
      }
    },
  };
}

/* ── JSON syntax highlighting ─────────────────────────────────────────────── */
function syntaxHighlight(obj) {
  const str = JSON.stringify(obj, null, 2);
  return str.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    match => {
      let cls = 'json-number';
      if (/^"/.test(match)) {
        cls = /:$/.test(match) ? 'json-key' : 'json-string';
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean';
      } else if (/null/.test(match)) {
        cls = 'json-null';
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

/* ── Render output ────────────────────────────────────────────────────────── */
function renderResult(data, latencyMs) {
  // Hide empty state, show output
  document.getElementById('empty-state').style.display = 'none';
  document.getElementById('json-output').style.display = 'block';

  // Incident ID badge
  const shortId = String(data.incident_id).split('-')[0].toUpperCase();
  document.getElementById('incident-id-badge').textContent = `INC-${shortId}`;

  // DEFCON bar
  const defcon = document.getElementById('defcon-bar');
  if (defcon) {
    defcon.style.display = 'flex';
    defcon.setAttribute('data-level', data.urgency_level);
  }
  const defconVal = document.getElementById('defcon-value');
  if (defconVal) defconVal.textContent = data.urgency_level;

  // Verification flag
  const vContainer = document.getElementById('vflag-container');
  if (vContainer) {
    vContainer.style.display = 'block';
    const flag = data.verification_flag;
    const cls = flag === 'PASS' ? 'pass' : (typeof flag === 'string' && flag.includes('HUMAN')) ? 'hitl' : 'fail';
    const icon = flag === 'PASS' ? '✓' : (typeof flag === 'string' && flag.includes('HUMAN')) ? '⚡' : '✕';
    vContainer.innerHTML = `<div class="vflag ${cls}"><span class="vflag-icon">${icon}</span>${flag}</div>`;
  }

  // Missing data warnings
  const missing = data.extracted_entities?.missing_critical_data || [];
  const missingList = document.getElementById('missing-list');
  if (missingList) {
    if (missing.length > 0) {
      missingList.style.display = 'flex';
      missingList.innerHTML = missing
        .map(m => `<li>&#9650; ${m.replace(/_/g, ' ').toUpperCase()}</li>`)
        .join('');
    } else {
      missingList.style.display = 'none';
    }
  }

  // JSON viewer
  document.getElementById('json-output').innerHTML = syntaxHighlight(data);

  // Footer latency
  document.getElementById('footer-latency').textContent =
    latencyMs ? `PIPELINE: ${latencyMs}ms` : '';
}

/* ── Status helpers ───────────────────────────────────────────────────────── */
function setStatus(text, processing) {
  document.getElementById('status-dot').className =
    `status-dot${processing ? ' processing' : ''}`;
  document.getElementById('status-label').textContent = text;
}

/* ── Submit ───────────────────────────────────────────────────────────────── */
async function submitIncident() {
  const textVal = document.getElementById('incident-text').value.trim();

  if (activeTab === 'text' && !textVal) {
    alert('Please enter incident text before processing.');
    return;
  }
  if (activeTab === 'audio' && !recordedBlob) {
    alert('Please record audio before processing.');
    return;
  }

  resetSteps();
  const stepCtrl = animatePipeline();

  // UI: processing state
  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  document.getElementById('submit-label').textContent = '⏳ PROCESSING…';
  setStatus('PROCESSING', true);

  const form = new FormData();
  if (activeTab === 'text' && textVal) {
    form.append('text', textVal);
  }
  if (activeTab === 'audio' && recordedBlob) {
    form.append('audio', recordedBlob, 'recording.webm');
    if (textVal) form.append('text', textVal);  // optional context alongside audio
  }

  const skills = [];
  if (document.getElementById('skill-security')?.checked) skills.push('security');
  if (document.getElementById('skill-memory')?.checked) skills.push('memory');

  const t0 = Date.now();
  try {
    const resp = await fetch('/v1/incident/ingest', {
      method: 'POST',
      headers: { 'X-Omni-Skills': skills.join(',') },
      body: form,
    });

    const latencyMs = Date.now() - t0;

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    const hasWarning = data.verification_flag !== 'PASS';
    stepCtrl.finish(hasWarning);
    renderResult(data, latencyMs);
    setStatus('READY', false);
  } catch (err) {
    stepCtrl.error();
    setStatus('ERROR', false);
    const emptyState = document.getElementById('empty-state');
    if (emptyState) emptyState.style.display = 'block';
    const jsonOutput = document.getElementById('json-output');
    if (jsonOutput) jsonOutput.style.display = 'none';
    
    const defconBar = document.getElementById('defcon-bar');
    if (defconBar) defconBar.style.display = 'none';
    const vflagContainer = document.getElementById('vflag-container');
    if (vflagContainer) vflagContainer.style.display = 'none';
    const missingList = document.getElementById('missing-list');
    if (missingList) missingList.style.display = 'none';

    alert(`Pipeline error: ${err.message}`);
  } finally {
    btn.disabled = false;
    document.getElementById('submit-label').textContent = '▶ PROCESS INCIDENT';
  }
}

/* ── Authentication Handlers (Google Identity Services) ────────────────────────── */
function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => 
      '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

window.handleCredentialResponse = function(response) {
  const jwt = parseJwt(response.credential);
  if (jwt && jwt.name) {
    const signinDiv = document.querySelector('.g_id_signin');
    if (signinDiv) signinDiv.style.display = 'none';

    document.getElementById('status-label').textContent = `AUTHED: ${jwt.name.toUpperCase()}`;
    document.getElementById('status-dot').style.background = 'var(--cyan)';
    document.getElementById('status-dot').style.boxShadow = '0 0 10px var(--cyan)';
    
    // Log auth event to analytics
    if (typeof gtag === 'function') {
      gtag('event', 'login', { method: 'Google' });
    }
  }
};

/* ── Init ─────────────────────────────────────────────────────────────────── */
(function init() {
  switchTab('text');

  // Allow Ctrl+Enter to submit
  document.getElementById('incident-text').addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') submitIncident();
  });
})();
