// ── Session ID ──
const SESSION_ID = 'sess_' + Math.random().toString(36).slice(2, 10);
document.getElementById('sessionLabel').textContent = 'ID: ' + SESSION_ID;

const messagesEl = document.getElementById('messages');
const inputEl    = document.getElementById('msgInput');
const sendBtn    = document.getElementById('sendBtn');

// ── Panel switching ──
function showPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  event.currentTarget.classList.add('active');

  if (name === 'logs')  loadLogs();
  if (name === 'stats') loadStats();
}

// ── Send message ──
async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = '';
  autoResize();

  appendMessage('user', text);
  const typing = appendTyping();
  sendBtn.disabled = true;

  try {
    const res  = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session: SESSION_ID })
    });
    const data = await res.json();

    removeTyping(typing);
    if (data.error) {
      appendMessage('bot', 'Sorry, something went wrong. Please try again.', 'error');
    } else {
      appendMessage('bot', data.reply, data.intent);
    }
  } catch (err) {
    removeTyping(typing);
    appendMessage('bot', 'Connection error. Is the server running?', 'error');
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

function sendQuick(text) {
  inputEl.value = text;
  sendMessage();
  // Switch to chat panel
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-chat').classList.add('active');
  document.querySelector('.nav-btn').classList.add('active');
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
  autoResize();
}

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
}
inputEl.addEventListener('input', autoResize);

// ── Message rendering ──
function appendMessage(role, text, intent) {
  const wrap = document.createElement('div');
  wrap.className = 'message ' + role;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'bot' ? 'N' : 'U';

  const body = document.createElement('div');
  body.className = 'msg-body';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  const meta = document.createElement('div');
  meta.className = 'msg-meta';
  const now = new Date();
  meta.textContent = (role === 'bot' ? 'NexBot' : 'You') + ' · ' + now.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});

  body.appendChild(bubble);

  if (intent && intent !== 'unknown' && role === 'bot') {
    const badge = document.createElement('div');
    badge.className = 'intent-badge';
    badge.textContent = '⚡ ' + intent;
    body.appendChild(badge);
  }

  body.appendChild(meta);
  wrap.appendChild(avatar);
  wrap.appendChild(body);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

function appendTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'message bot typing';
  wrap.innerHTML = `
    <div class="msg-avatar">N</div>
    <div class="msg-body">
      <div class="bubble"><div class="dots"><span></span><span></span><span></span></div></div>
    </div>`;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

function removeTyping(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
}

function clearChat() {
  messagesEl.innerHTML = '';
  appendMessage('bot', 'Chat cleared! How can I help you?');
}

// ── Logs ──
async function loadLogs() {
  const body = document.getElementById('logsBody');
  body.innerHTML = '<div class="empty-state">Loading…</div>';
  try {
    const res  = await fetch('/history/' + SESSION_ID);
    const rows = await res.json();
    if (!rows.length) {
      body.innerHTML = '<div class="empty-state">No messages logged yet. Start chatting!</div>';
      return;
    }
    body.innerHTML = '';
    rows.forEach(r => {
      const row = document.createElement('div');
      row.className = 'log-row';
      const time = new Date(r.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
      row.innerHTML = `
        <span class="log-role ${r.role}">${r.role}</span>
        <span class="log-msg">${escHtml(r.message)}</span>
        ${r.intent ? `<span class="log-intent">${r.intent}</span>` : ''}
        <span class="log-time">${time}</span>`;
      body.appendChild(row);
    });
  } catch {
    body.innerHTML = '<div class="empty-state">Failed to load logs.</div>';
  }
}

// ── Stats ──
async function loadStats() {
  const body = document.getElementById('statsBody');
  body.innerHTML = '<div class="empty-state">Loading…</div>';
  try {
    const res  = await fetch('/stats');
    const data = await res.json();
    const maxCount = data.top_intents.length ? Math.max(...data.top_intents.map(i => i.c)) : 1;

    body.innerHTML = `
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-value">${data.total_messages}</div>
          <div class="stat-label">Total messages</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${data.total_sessions}</div>
          <div class="stat-label">Unique sessions</div>
        </div>
      </div>
      <div class="intents-card">
        <div class="intents-title">Top Intents Detected</div>
        ${data.top_intents.length
          ? data.top_intents.map(i => `
              <div class="intent-row">
                <div class="intent-name">${i.intent}</div>
                <div class="intent-bar-track">
                  <div class="intent-bar-fill" style="width:${Math.round(i.c/maxCount*100)}%"></div>
                </div>
                <div class="intent-count">${i.c}</div>
              </div>`).join('')
          : '<div class="empty-state" style="padding:1rem">No data yet.</div>'
        }
      </div>`;
  } catch {
    body.innerHTML = '<div class="empty-state">Failed to load stats.</div>';
  }
}

function escHtml(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
