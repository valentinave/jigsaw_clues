const state = {
  timer: '00:00:00',
  running: false,
  puzzles: {},
  rooms: {},
  devices: {},
  log: [],
};

const timerDisplay = document.getElementById('timer-display');
const timerStatus = document.getElementById('timer-status');
const wsStatus = document.getElementById('ws-status');
const mqttHost = document.getElementById('mqtt-host');
const logStream = document.getElementById('log-stream');
const roomsContainer = document.getElementById('rooms-container');
const deviceCheckboxes = document.getElementById('device-checkboxes');

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json().catch(() => ({}));
}

function updateTimerDisplay(formatted, running) {
  state.timer = formatted;
  state.running = !!running;
  timerDisplay.textContent = formatted;
  timerStatus.textContent = running ? 'Running' : 'Paused';
  timerStatus.classList.toggle('text-success', !!running);
  timerStatus.classList.toggle('text-secondary', !running);
}

function renderDevices(devices) {
  deviceCheckboxes.innerHTML = '';
  Object.entries(devices).forEach(([key, info]) => {
    const pill = document.createElement('label');
    pill.className = 'device-pill';

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.value = key;
    input.checked = true;
    pill.appendChild(input);

    const span = document.createElement('span');
    span.textContent = info.label || key;
    pill.appendChild(span);

    deviceCheckboxes.appendChild(pill);
  });
}

function groupPuzzles() {
  const grouped = {};
  Object.values(state.puzzles).forEach((puzzle) => {
    const key = puzzle.room_key;
    if (!grouped[key]) {
      grouped[key] = [];
    }
    grouped[key].push(puzzle);
  });
  return grouped;
}

function renderRooms() {
  roomsContainer.innerHTML = '';
  const grouped = groupPuzzles();

  Object.entries(state.rooms).forEach(([key, roomInfo]) => {
    const puzzles = grouped[key] || [];
    const card = document.createElement('div');
    card.className = 'puzzle-card';

    const header = document.createElement('div');
    header.className = 'd-flex justify-content-between align-items-start gap-3';
    const title = document.createElement('h3');
    title.className = 'mb-0 text-accent';
    title.textContent = roomInfo.label || key;
    header.appendChild(title);

    const targets = document.createElement('div');
    targets.className = 'text-secondary small';
    const targetLabels = (roomInfo.targets || [])
      .map((t) => state.devices[t]?.label || t)
      .join(', ');
    targets.textContent = targetLabels ? `Targets: ${targetLabels}` : '';
    header.appendChild(targets);
    card.appendChild(header);

    const table = document.createElement('table');
    table.className = 'puzzle-table';
    const tbody = document.createElement('tbody');

    puzzles.forEach((puzzle) => {
      const tr = document.createElement('tr');

      const nameTd = document.createElement('td');
      const name = document.createElement('div');
      name.className = 'fw-semibold';
      name.textContent = puzzle.label;
      nameTd.appendChild(name);
      const hintBadge = document.createElement('div');
      hintBadge.className = 'badge-soft info mt-1 d-inline-flex align-items-center gap-2';
      const hintIcon = document.createElement('span');
      hintIcon.textContent = '💡';
      hintBadge.appendChild(hintIcon);
      const hintText = document.createElement('span');
      hintText.textContent = `Hints: ${puzzle.hints_used}`;
      hintBadge.appendChild(hintText);
      nameTd.appendChild(hintBadge);
      tr.appendChild(nameTd);

      const statusTd = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = `badge-soft ${puzzle.solved ? 'success' : 'danger'}`;
      badge.textContent = puzzle.solved ? 'Solved' : 'Pending';
      statusTd.appendChild(badge);
      tr.appendChild(statusTd);

      const actionsTd = document.createElement('td');
      actionsTd.className = 'room-actions text-end';
      const playBtn = document.createElement('button');
      playBtn.className = 'btn btn-sm btn-outline-info me-2';
      playBtn.textContent = 'Play clue';
      playBtn.addEventListener('click', () => triggerVideo(puzzle.id));

      const solvedBtn = document.createElement('button');
      solvedBtn.className = `btn btn-sm ${puzzle.solved ? 'btn-success' : 'btn-outline-success'} me-2`;
      solvedBtn.textContent = puzzle.solved ? 'Mark unsolved' : 'Mark solved';
      solvedBtn.addEventListener('click', () => toggleSolved(puzzle));

      const hintGroup = document.createElement('div');
      hintGroup.className = 'btn-group btn-group-sm';
      const hintMinus = document.createElement('button');
      hintMinus.className = 'btn btn-outline-light';
      hintMinus.textContent = '-';
      hintMinus.addEventListener('click', () => adjustHints(puzzle, -1));
      const hintPlus = document.createElement('button');
      hintPlus.className = 'btn btn-outline-light';
      hintPlus.textContent = '+';
      hintPlus.addEventListener('click', () => adjustHints(puzzle, 1));
      hintGroup.appendChild(hintMinus);
      hintGroup.appendChild(hintPlus);

      actionsTd.appendChild(playBtn);
      actionsTd.appendChild(solvedBtn);
      actionsTd.appendChild(hintGroup);
      tr.appendChild(actionsTd);

      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    card.appendChild(table);
    roomsContainer.appendChild(card);
  });
}

function renderLog(entries) {
  logStream.innerHTML = '';
  entries.forEach((entry) => appendLog(entry, false));
  logStream.scrollTop = logStream.scrollHeight;
}

function appendLog(entry, pushState = true) {
  if (pushState) {
    state.log.push(entry);
    state.log = state.log.slice(-400);
  }
  const row = document.createElement('div');
  row.className = 'log-entry';
  const ts = document.createElement('span');
  ts.className = 'ts';
  ts.textContent = formatTimestamp(entry.ts);
  const msg = document.createElement('span');
  msg.textContent = entry.message || entry.msg || '';
  row.appendChild(ts);
  row.appendChild(msg);
  logStream.appendChild(row);
  logStream.scrollTop = logStream.scrollHeight;
}

function formatTimestamp(ts) {
  if (!ts) return '';
  const date = new Date(ts * 1000);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

async function triggerVideo(puzzleId) {
  try {
    await postJSON('/api/video', { game_id: puzzleId });
  } catch (error) {
    console.error('Failed to trigger video', error);
  }
}

async function toggleSolved(puzzle) {
  try {
    await postJSON(`/api/puzzles/${puzzle.id}/solve`, { solved: !puzzle.solved });
  } catch (error) {
    console.error('Failed to update puzzle', error);
  }
}

async function adjustHints(puzzle, delta) {
  try {
    await postJSON(`/api/puzzles/${puzzle.id}/hints`, { delta });
  } catch (error) {
    console.error('Failed to update hints', error);
  }
}

async function sendTimerAction(action, value = null) {
  try {
    await postJSON('/api/timer/control', { action, value });
  } catch (error) {
    console.error('Timer action failed', error);
  }
}

function parseTimeInput(value) {
  if (!value) return null;
  const parts = value.split(':').map((p) => p.trim());
  if (parts.length === 3) {
    const [h, m, s] = parts.map((p) => Number(p));
    if ([h, m, s].some((n) => Number.isNaN(n))) return null;
    return h * 3600 + m * 60 + s;
  }
  if (parts.length === 2) {
    const [m, s] = parts.map((p) => Number(p));
    if ([m, s].some((n) => Number.isNaN(n))) return null;
    return m * 60 + s;
  }
  const asNumber = Number(value);
  return Number.isNaN(asNumber) ? null : asNumber;
}

function getSelectedDevices() {
  const selected = Array.from(deviceCheckboxes.querySelectorAll('input[type="checkbox"]:checked')).map((el) => el.value);
  return selected;
}

async function sendClue() {
  const textArea = document.getElementById('clue-text');
  const text = textArea.value.trim();
  if (!text) return;
  const targets = getSelectedDevices();
  try {
    await postJSON('/api/messages', { text, targets });
    textArea.value = '';
  } catch (error) {
    console.error('Failed to send message', error);
  }
}

function attachEventHandlers() {
  document.querySelectorAll('[data-action]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action;
      if (action === 'reset') {
        sendTimerAction('reset', 0);
      } else {
        sendTimerAction(action);
      }
    });
  });

  document.querySelectorAll('[data-adjust]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const delta = Number(btn.dataset.adjust || '0');
      sendTimerAction('add', delta);
    });
  });

  document.getElementById('timer-set-btn').addEventListener('click', () => {
    const inputValue = document.getElementById('timer-set').value.trim();
    const seconds = parseTimeInput(inputValue);
    if (seconds != null) {
      sendTimerAction('set', seconds);
    }
  });

  document.getElementById('send-clue-btn').addEventListener('click', sendClue);
  document.getElementById('clear-log').addEventListener('click', () => {
    state.log = [];
    renderLog([]);
  });
}

function applyState(data) {
  state.rooms = data.rooms || {};
  state.devices = data.devices || {};
  state.puzzles = {};
  (data.puzzles || []).forEach((p) => {
    state.puzzles[p.id] = p;
  });
  state.log = data.log || [];
  updateTimerDisplay(data.timer || '00:00:00', data.timer_running);
  renderDevices(state.devices);
  renderRooms();
  renderLog(state.log);
  if (data.mqtt_host) {
    mqttHost.textContent = data.mqtt_host;
  }
}

async function loadInitialState() {
  try {
    const data = await fetch('/api/state').then((res) => res.json());
    applyState(data);
  } catch (error) {
    console.error('Failed to load state', error);
  }
}

function handleSocketMessage(message) {
  const { type, data } = message;
  switch (type) {
    case 'state':
      applyState(data);
      break;
    case 'timer':
      updateTimerDisplay(data.formatted, data.running);
      break;
    case 'puzzle':
      state.puzzles[data.id] = data;
      renderRooms();
      break;
    case 'log':
      appendLog(data);
      break;
    default:
      break;
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${protocol}://${window.location.host}/ws`;
  let reconnectDelay = 1000;

  function establish() {
    const ws = new WebSocket(wsUrl);
    wsStatus.textContent = 'Connecting…';
    wsStatus.className = 'badge rounded-pill bg-secondary';

    ws.onopen = () => {
      wsStatus.textContent = 'Connected';
      wsStatus.className = 'badge rounded-pill bg-success';
      reconnectDelay = 1000;
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleSocketMessage(payload);
      } catch (error) {
        console.error('Invalid WS payload', error);
      }
    };

    ws.onclose = () => {
      wsStatus.textContent = 'Disconnected';
      wsStatus.className = 'badge rounded-pill bg-danger';
      setTimeout(establish, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 1.5, 10000);
    };

    ws.onerror = () => {
      wsStatus.textContent = 'Error';
      wsStatus.className = 'badge rounded-pill bg-danger';
    };
  }

  establish();
}

attachEventHandlers();
loadInitialState();
connectWebSocket();
