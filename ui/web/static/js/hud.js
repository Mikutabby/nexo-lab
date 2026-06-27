/* ── Nexo UI HUD — JavaScript ────────────────────────────────────────── */

const STATE_URL = '/api/state';
const COMMAND_URL = '/api/command';
const WS_URL = 'ws://127.0.0.1:7071';

let lastState = {};
let historyLog = [];

// ── WebSocket ─────────────────────────────────────────────────────────
function connectWS() {
  const ws = new WebSocket(WS_URL);
  ws.onmessage = function(e) {
    try {
      const msg = JSON.parse(e.data);
      if (msg.type === 'state_update') {
        updateUI(msg.data);
      }
    } catch(err) {}
  };
  ws.onclose = function() {
    setTimeout(connectWS, 2000);
  };
  ws.onerror = function() {
    ws.close();
  };
}

// ── UI Update ─────────────────────────────────────────────────────────
function updateUI(s) {
  lastState = s;

  // Stats
  document.getElementById('cpu-val').textContent = s.cpu + '%';
  document.getElementById('cpu-bar').style.width = Math.min(s.cpu, 100) + '%';
  document.getElementById('ram-val').textContent = s.ram + '%';
  document.getElementById('ram-bar').style.width = Math.min(s.ram, 100) + '%';
  document.getElementById('temp-val').textContent = s.temp + '°C';

  // Color de temperatura
  const tempEl = document.getElementById('temp-bar');
  const temp = s.temp || 0;
  if (temp > 75) {
    tempEl.style.background = 'linear-gradient(90deg, #ff4444, #ff8800)';
  } else if (temp > 60) {
    tempEl.style.background = 'linear-gradient(90deg, #ffaa00, #ff8800)';
  } else {
    tempEl.style.background = 'linear-gradient(90deg, #00d4ff, #00aaff)';
  }
  tempEl.style.width = Math.min(temp * 1.2, 100) + '%';

  document.getElementById('disk-val').textContent = s.disk + '%';
  document.getElementById('disk-bar').style.width = Math.min(s.disk, 100) + '%';
  document.getElementById('uptime-val').textContent = s.uptime || '—';
  document.getElementById('host-val').textContent = s.hostname || '—';

  // Nexo status
  const status = s.nexo_status || 'idle';
  const statusEl = document.getElementById('nexo-status');
  const indicator = document.getElementById('status-indicator');
  const statusMap = {
    idle: ['INACTIVO', 'idle'],
    listening: ['ESCUCHANDO', 'listening'],
    thinking: ['PROCESANDO', 'thinking'],
    speaking: ['HABLANDO', 'speaking'],
    error: ['ERROR', 'error']
  };
  const [label, cls] = statusMap[status] || ['—', 'idle'];
  statusEl.textContent = label;
  statusEl.className = 'nexo-status ' + cls;
  indicator.className = 'status-indicator' + (status !== 'idle' ? ' active' : '');

  // Comando y respuesta
  if (s.last_command) {
    document.getElementById('command-display').textContent = '> ' + s.last_command;
    document.getElementById('command-display').style.color = '#88ccff';
  }
  if (s.last_response) {
    document.getElementById('response-display').textContent = s.last_response;
    document.getElementById('response-display').style.color = '#00ff88';
  }

  // Historial
  if (s.last_command && (!lastState.last_command || lastState.last_command !== s.last_command)) {
    addHistory(s.last_command, s.last_response || '');
  }
}

// ── History ───────────────────────────────────────────────────────────
function addHistory(cmd, resp) {
  const time = new Date().toLocaleTimeString();
  historyLog.unshift({ time, cmd, resp });
  if (historyLog.length > 50) historyLog.pop();

  const log = document.getElementById('history-log');
  if (historyLog.length === 0) {
    log.innerHTML = '<div class="history-empty">— Sin actividad —</div>';
    return;
  }

  log.innerHTML = historyLog.map(h => `
    <div class="history-item">
      <span class="time">${h.time}</span>
      <span class="cmd">&gt; ${escapeHtml(h.cmd)}</span>
      ${h.resp ? `<span class="resp">${escapeHtml(h.resp)}</span>` : ''}
    </div>
  `).join('');
}

function escapeHtml(t) {
  const div = document.createElement('div');
  div.textContent = t;
  return div.innerHTML;
}

// ── Send Command ──────────────────────────────────────────────────────
function sendCommand(cmd) {
  if (!cmd) {
    cmd = document.getElementById('command-input').value.trim();
    if (!cmd) return;
    document.getElementById('command-input').value = '';
  }

  // Mostrar inmediatamente
  document.getElementById('command-display').textContent = '> ' + cmd;
  document.getElementById('command-display').style.color = '#88ccff';
  document.getElementById('nexo-status').textContent = 'PROCESANDO';
  document.getElementById('nexo-status').className = 'nexo-status thinking';
  document.getElementById('status-indicator').className = 'status-indicator active';

  fetch(COMMAND_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: cmd })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status !== 'ok') {
      console.error('Error:', data);
    }
  })
  .catch(err => console.error('Error:', err));
}

// ── Keyboard ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  const input = document.getElementById('command-input');
  if (input) {
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') sendCommand();
    });
    input.focus();
  }
});

// ── Polling ───────────────────────────────────────────────────────────
function pollState() {
  fetch(STATE_URL)
    .then(r => r.json())
    .then(s => updateUI(s))
    .catch(() => {});
}

// ── Init ──────────────────────────────────────────────────────────────
connectWS();
setInterval(pollState, 2000);
pollState();
