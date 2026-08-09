/**
 * Command Center Ingestion & Payload Viewer Component
 */

import { state } from '../state.js';
import { CONFIG } from '../config.js';
import { fetchSamples, ingestIncident } from '../api.js';
import { logIncidentFeed } from './incidentFeed.js';

let audioCtx = null;
let analyser = null;
let animFrameId = null;
let pipelineTimer = null;

export function initCommandCenter() {
  ['text', 'audio', 'gcs'].forEach(tab => {
    const btn = document.getElementById(`tab-${tab}`);
    if (btn) btn.addEventListener('click', () => switchTab(tab));
  });

  const recordBtn = document.getElementById('record-btn');
  if (recordBtn) recordBtn.addEventListener('click', toggleRecording);

  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) submitBtn.addEventListener('click', submitIncident);

  const textArea = document.getElementById('incident-text');
  if (textArea) {
    textArea.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') submitIncident();
    });
  }

  loadDemoAssetWidget();
}

export async function loadDemoAssetWidget() {
  const grid = document.getElementById('demo-widget-grid');
  if (!grid) return;

  try {
    const data = await fetchSamples();
    const icons = {
      'Medical': '🚑',
      'Traffic': '🚗',
      'Crisis_Response': '☣️',
      'Weather': '🌊'
    };

    grid.innerHTML = data.samples.map(s => {
      const icon = icons[s.domain] || '⚡';
      return `
        <div class="demo-chip-card" data-uri="${s.uri}">
          <div class="demo-chip-icon">${icon}</div>
          <div class="demo-chip-details">
            <div class="demo-chip-label">${s.label}</div>
            <div class="demo-chip-tag">${s.domain} &bull; ${s.type.toUpperCase()}</div>
          </div>
        </div>
      `;
    }).join('');

    grid.querySelectorAll('.demo-chip-card').forEach(card => {
      card.addEventListener('click', () => {
        const uri = card.getAttribute('data-uri');
        const match = data.samples.find(x => x.uri === uri);
        if (match && match.content_preview) {
          switchTab('text');
          const txt = document.getElementById('incident-text');
          if (txt) {
            txt.value = match.content_preview;
            txt.focus();
          }
        }
      });
    });
  } catch (err) {
    grid.innerHTML = `<span style="font-size:11px;color:var(--text-secondary)">Demo widgets available in GCS Catalogue.</span>`;
  }
}

export function switchTab(tab) {
  state.activeInputTab = tab;
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
}

async function toggleRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state === 'recording') {
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
  state.audioChunks = [];
  state.recordedBlob = null;
  state.recordingSeconds = 0;

  state.mediaRecorder = new MediaRecorder(stream);
  state.mediaRecorder.ondataavailable = e => state.audioChunks.push(e.data);
  state.mediaRecorder.onstop = () => {
    state.recordedBlob = new Blob(state.audioChunks, { type: state.mediaRecorder.mimeType || 'audio/webm' });
    document.getElementById('audio-status').textContent =
      `Recording saved — ${(state.recordedBlob.size / 1024).toFixed(1)} KB. Click "Process Incident Payload" to analyse.`;
    stream.getTracks().forEach(t => t.stop());
    stopWaveform();
  };

  state.mediaRecorder.start(100);
  startWaveform(stream);

  const btn = document.getElementById('record-btn');
  btn.classList.add('recording');
  document.getElementById('record-label').textContent = 'Recording… click to stop';

  state.recordingInterval = setInterval(() => {
    state.recordingSeconds++;
    const m = String(Math.floor(state.recordingSeconds / 60)).padStart(2, '0');
    const s = String(state.recordingSeconds % 60).padStart(2, '0');
    document.getElementById('record-timer').textContent = `${m}:${s}`;
  }, 1000);

  document.getElementById('audio-status').textContent = 'Recording in progress…';
}

function stopRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') state.mediaRecorder.stop();
  clearInterval(state.recordingInterval);
  const btn = document.getElementById('record-btn');
  btn.classList.remove('recording');
  document.getElementById('record-label').textContent = 'Click to start recording';
  document.getElementById('record-timer').textContent = '00:00';
}

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
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

export function resetSteps() {
  for (let i = 0; i < 5; i++) {
    const dot = document.getElementById(`dot-${i}`);
    if (dot) {
      dot.className = 'step-dot';
      dot.textContent = `0${i + 1}`;
    }
  }
}

export function animatePipeline() {
  let step = 0;
  function activateStep(i) {
    if (i > 0) {
      const prev = document.getElementById(`dot-${i - 1}`);
      if (prev) {
        prev.className = 'step-dot done';
        prev.textContent = '✓';
      }
    }
    const dot = document.getElementById(`dot-${i}`);
    if (dot) {
      dot.className = 'step-dot active';
      dot.textContent = CONFIG.STEP_LABELS[i];
    }
  }

  pipelineTimer = setTimeout(function tick() {
    activateStep(step);
    step++;
    if (step < 5) {
      pipelineTimer = setTimeout(tick, CONFIG.STEP_DELAYS[step - 1]);
    }
  }, 0);

  return {
    finish(hasWarning) {
      clearTimeout(pipelineTimer);
      for (let i = 0; i < 5; i++) {
        const dot = document.getElementById(`dot-${i}`);
        if (dot) {
          dot.textContent = i === 3 && hasWarning ? '!' : '✓';
          dot.className = `step-dot ${i === 3 && hasWarning ? 'warning' : 'done'}`;
        }
      }
    },
    error() {
      clearTimeout(pipelineTimer);
      for (let i = 0; i < 5; i++) {
        const dot = document.getElementById(`dot-${i}`);
        if (dot) dot.className = 'step-dot error';
      }
    },
  };
}

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

export function renderResult(data, latencyMs) {
  document.getElementById('empty-state').style.display = 'none';
  document.getElementById('json-output').style.display = 'block';

  const insightsPanel = document.getElementById('insights-panel');
  if (insightsPanel) {
    insightsPanel.style.display = 'block';
    
    document.getElementById('m-domain').textContent = data.domain_classification || 'General';
    document.getElementById('m-latency').textContent = latencyMs ? `${latencyMs}ms` : '--ms';
    document.getElementById('m-urgency').textContent = data.urgency_level || 'LOW';
    document.getElementById('m-verification').textContent = data.verification_flag || 'PASS';

    document.getElementById('insight-text').textContent = data.synthesized_context || "Pipeline executed cleanly.";

    const scoreValue = document.getElementById('score-value');
    const scoreFill = document.getElementById('score-fill');
    if (scoreValue && scoreFill) {
      let score = 95;
      if (data.verification_flag === 'PENDING_HITL') score = 70;
      if (data.verification_flag === 'FAILED') score = 35;
      const missingItems = data.extracted_entities?.missing_critical_data || [];
      score -= (missingItems.length * 6);
      score = Math.max(15, Math.min(100, score));
      
      scoreValue.textContent = `${score}%`;
      scoreFill.style.width = `${score}%`;
      scoreFill.style.background = score < 60 ? 'var(--critical)' : (score < 85 ? 'var(--moderate)' : 'var(--cyan)');
    }
  }

  const shortId = String(data.incident_id || '0000').split('-')[0].toUpperCase();
  document.getElementById('incident-id-badge').textContent = `INC-${shortId}`;

  document.getElementById('json-output').innerHTML = syntaxHighlight(data);
  document.getElementById('footer-latency').textContent = latencyMs ? `LATENCY: ${latencyMs}ms` : '';
}

export async function submitIncident() {
  const textVal = document.getElementById('incident-text').value.trim();

  if (state.activeInputTab === 'text' && !textVal) {
    alert('Please enter incident text before processing.');
    return;
  }
  if (state.activeInputTab === 'audio' && !state.recordedBlob) {
    alert('Please record audio before processing.');
    return;
  }

  resetSteps();
  const stepCtrl = animatePipeline();

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  document.getElementById('submit-label').textContent = '⏳ PROCESSING PAYLOAD…';
  setStatus('PROCESSING', true);

  const form = new FormData();
  if (state.activeInputTab === 'text' && textVal) {
    form.append('text', textVal);
  }
  if (state.activeInputTab === 'audio' && state.recordedBlob) {
    form.append('audio', state.recordedBlob, 'recording.webm');
    if (textVal) form.append('text', textVal);
  }

  const skills = [];
  if (document.getElementById('skill-security')?.checked) skills.push('security');
  if (document.getElementById('skill-memory')?.checked) skills.push('memory');

  const t0 = Date.now();
  try {
    const data = await ingestIncident(form, skills);
    const latencyMs = Date.now() - t0;
    const hasWarning = data.verification_flag !== 'PASS';

    stepCtrl.finish(hasWarning);
    renderResult(data, latencyMs);
    logIncidentFeed(data, latencyMs);
    setStatus('ONLINE', false);
  } catch (err) {
    stepCtrl.error();
    setStatus('ERROR', false);
    alert(`Pipeline execution error: ${err.message}`);
  } finally {
    btn.disabled = false;
    document.getElementById('submit-label').textContent = '▶ PROCESS INCIDENT PAYLOAD';
  }
}

export function setStatus(text, processing) {
  const dot = document.getElementById('status-dot');
  if (dot) dot.className = `status-dot${processing ? ' processing' : ''}`;
  const lbl = document.getElementById('status-label');
  if (lbl) lbl.textContent = text;
}
