import { h, render, Component } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

// API helpers
const api = {
  get: (url) => fetch(url).then(r => r.json()),
  post: (url, data) => fetch(url, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
  }).then(r => r.json()),
  put: (url, data) => fetch(url, {
    method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
  }).then(r => r.json()),
  del: (url) => fetch(url, { method: 'DELETE' }),
};

// --- Winlink Tab ---
function WinlinkTab() {
  const [messages, setMessages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [composing, setComposing] = useState(false);
  const [form, setForm] = useState({ to: '', subject: '', body: '' });

  const load = () => api.get('/api/winlink/messages').then(setMessages);
  useEffect(() => { load(); }, []);

  const send = () => {
    api.post('/api/winlink/compose', form).then(() => {
      setForm({ to: '', subject: '', body: '' });
      setComposing(false);
      load();
    });
  };

  const doSend = () => api.post('/api/winlink/send').then(load);
  const doReceive = () => api.post('/api/winlink/receive').then(load);

  return html`
    <div class="panel">
      <h2>Winlink Messages</h2>
      <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem">
        <button class="btn" onClick=${() => setComposing(!composing)}>Compose</button>
        <button class="btn" onClick=${doSend}>Send Queued</button>
        <button class="btn" onClick=${doReceive}>Check Mail</button>
      </div>
      ${composing && html`
        <div style="margin-bottom:0.75rem">
          <div class="form-row">
            <div><label>To</label><input value=${form.to} onInput=${e => setForm({...form, to: e.target.value})} /></div>
            <div><label>Subject</label><input value=${form.subject} onInput=${e => setForm({...form, subject: e.target.value})} /></div>
          </div>
          <label>Body</label>
          <textarea value=${form.body} onInput=${e => setForm({...form, body: e.target.value})}></textarea>
          <button class="btn" onClick=${send} style="margin-top:0.5rem">Queue Message</button>
        </div>
      `}
      <div class="msg-list">
        ${messages.map(m => html`
          <div class="msg-item" onClick=${() => setSelected(m)}>
            <span class="from">${m.direction === 'inbound' ? m.from_addr : m.to_addr}</span>
            <span class="subject"> - ${m.subject}</span>
            <span class="date"> [${m.status}] ${m.created_at}</span>
          </div>
        `)}
        ${messages.length === 0 && html`<div style="color:var(--text-dim);padding:1rem">No messages</div>`}
      </div>
      ${selected && html`
        <div class="panel" style="margin-top:0.75rem">
          <h2>${selected.subject}</h2>
          <div style="color:var(--text-dim);margin-bottom:0.5rem">
            From: ${selected.from_addr} | To: ${selected.to_addr} | ${selected.created_at}
          </div>
          <pre style="white-space:pre-wrap">${selected.body}</pre>
          <button class="btn" onClick=${() => setSelected(null)} style="margin-top:0.5rem">Close</button>
        </div>
      `}
    </div>
  `;
}

// --- JS8Call Tab ---
function JS8CallTab() {
  const [status, setStatus] = useState({ connected: false });
  const [messages, setMessages] = useState([]);
  const [form, setForm] = useState({ to_call: '', message: '' });

  const loadStatus = () => api.get('/api/js8call/status').then(setStatus);
  const loadMsgs = () => api.get('/api/js8call/messages').then(setMessages);
  useEffect(() => { loadStatus(); loadMsgs(); }, []);

  const send = () => {
    api.post('/api/js8call/send', form).then(() => {
      setForm({ to_call: '', message: '' });
      loadMsgs();
    });
  };

  return html`
    <div class="panel">
      <h2>JS8Call <span class="status-dot ${status.connected ? 'ok' : 'err'}"></span></h2>
      <div style="margin-bottom:0.75rem;color:var(--text-dim)">
        Status: ${status.connected ? 'Connected' : 'Disconnected'}
      </div>
      <div class="form-row">
        <div><label>To Callsign</label><input value=${form.to_call} onInput=${e => setForm({...form, to_call: e.target.value})} /></div>
        <div><label>Message</label><input value=${form.message} onInput=${e => setForm({...form, message: e.target.value})} /></div>
        <div style="display:flex;align-items:flex-end"><button class="btn" onClick=${send}>Send</button></div>
      </div>
      <table>
        <thead><tr><th>Dir</th><th>From</th><th>To</th><th>Message</th><th>Time</th></tr></thead>
        <tbody>
          ${messages.map(m => html`
            <tr>
              <td>${m.direction}</td>
              <td>${m.from_call}</td>
              <td>${m.to_call}</td>
              <td>${m.message}</td>
              <td>${m.created_at}</td>
            </tr>
          `)}
        </tbody>
      </table>
      ${messages.length === 0 && html`<div style="color:var(--text-dim);padding:0.5rem">No messages logged</div>`}
    </div>
  `;
}

// --- Frequencies Tab ---
function FrequenciesTab() {
  const [freqs, setFreqs] = useState([]);
  const [filter, setFilter] = useState({ band: '', mode: '', usage: '' });
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ freq_mhz: '', name: '', band: '', mode: '', usage: 'general', notes: '' });

  const load = () => {
    let url = '/api/frequencies?';
    if (filter.band) url += 'band=' + filter.band + '&';
    if (filter.mode) url += 'mode=' + filter.mode + '&';
    if (filter.usage) url += 'usage=' + filter.usage + '&';
    api.get(url).then(setFreqs);
  };
  useEffect(() => { load(); }, [filter]);

  const addFreq = () => {
    api.post('/api/frequencies', { ...form, freq_mhz: parseFloat(form.freq_mhz) }).then(() => {
      setAdding(false);
      setForm({ freq_mhz: '', name: '', band: '', mode: '', usage: 'general', notes: '' });
      load();
    });
  };

  const usageBadge = (u) => {
    const cls = ['emergency','simplex','net','digital','winlink','weather'].includes(u) ? u : '';
    return html`<span class="badge ${cls}">${u}</span>`;
  };

  return html`
    <div class="panel">
      <h2>Frequency Database (${freqs.length})</h2>
      <div class="form-row" style="margin-bottom:0.75rem">
        <div><label>Band</label><input placeholder="e.g. 2m" value=${filter.band} onInput=${e => setFilter({...filter, band: e.target.value})} /></div>
        <div><label>Mode</label><input placeholder="e.g. FM" value=${filter.mode} onInput=${e => setFilter({...filter, mode: e.target.value})} /></div>
        <div><label>Usage</label><input placeholder="e.g. emergency" value=${filter.usage} onInput=${e => setFilter({...filter, usage: e.target.value})} /></div>
        <div style="display:flex;align-items:flex-end"><button class="btn" onClick=${() => setAdding(!adding)}>+ Add</button></div>
      </div>
      ${adding && html`
        <div style="margin-bottom:0.75rem">
          <div class="form-row">
            <div><label>Frequency (MHz)</label><input value=${form.freq_mhz} onInput=${e => setForm({...form, freq_mhz: e.target.value})} /></div>
            <div><label>Name</label><input value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} /></div>
            <div><label>Band</label><input value=${form.band} onInput=${e => setForm({...form, band: e.target.value})} /></div>
            <div><label>Mode</label><input value=${form.mode} onInput=${e => setForm({...form, mode: e.target.value})} /></div>
          </div>
          <div class="form-row">
            <div><label>Usage</label><input value=${form.usage} onInput=${e => setForm({...form, usage: e.target.value})} /></div>
            <div><label>Notes</label><input value=${form.notes} onInput=${e => setForm({...form, notes: e.target.value})} /></div>
            <div style="display:flex;align-items:flex-end"><button class="btn" onClick=${addFreq}>Save</button></div>
          </div>
        </div>
      `}
      <table>
        <thead><tr><th>MHz</th><th>Name</th><th>Band</th><th>Mode</th><th>Usage</th><th>Notes</th></tr></thead>
        <tbody>
          ${freqs.map(f => html`
            <tr>
              <td>${f.freq_mhz}</td>
              <td>${f.name}</td>
              <td>${f.band}</td>
              <td>${f.mode}</td>
              <td>${usageBadge(f.usage)}</td>
              <td style="color:var(--text-dim)">${f.notes}</td>
            </tr>
          `)}
        </tbody>
      </table>
    </div>
  `;
}

// --- Scheduler Tab ---
function SchedulerTab() {
  const [contacts, setContacts] = useState([]);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({
    title: '', callsign: '', freq_mhz: '', mode: '',
    scheduled_at: '', duration_minutes: '30', notes: '', recurring: 'none'
  });

  const load = () => api.get('/api/contacts?upcoming=true').then(setContacts);
  useEffect(() => { load(); }, []);

  const add = () => {
    const data = { ...form, duration_minutes: parseInt(form.duration_minutes) || 30 };
    if (data.freq_mhz) data.freq_mhz = parseFloat(data.freq_mhz);
    else delete data.freq_mhz;
    api.post('/api/contacts', data).then(() => {
      setAdding(false);
      setForm({ title: '', callsign: '', freq_mhz: '', mode: '', scheduled_at: '', duration_minutes: '30', notes: '', recurring: 'none' });
      load();
    });
  };

  const remove = (id) => api.del('/api/contacts/' + id).then(load);

  return html`
    <div class="panel">
      <h2>Scheduled Contacts</h2>
      <button class="btn" onClick=${() => setAdding(!adding)} style="margin-bottom:0.75rem">+ Schedule Contact</button>
      ${adding && html`
        <div style="margin-bottom:0.75rem">
          <div class="form-row">
            <div><label>Title</label><input value=${form.title} onInput=${e => setForm({...form, title: e.target.value})} /></div>
            <div><label>Callsign</label><input value=${form.callsign} onInput=${e => setForm({...form, callsign: e.target.value})} /></div>
          </div>
          <div class="form-row">
            <div><label>Freq (MHz)</label><input value=${form.freq_mhz} onInput=${e => setForm({...form, freq_mhz: e.target.value})} /></div>
            <div><label>Mode</label><input value=${form.mode} onInput=${e => setForm({...form, mode: e.target.value})} /></div>
            <div><label>Duration (min)</label><input type="number" value=${form.duration_minutes} onInput=${e => setForm({...form, duration_minutes: e.target.value})} /></div>
          </div>
          <div class="form-row">
            <div><label>Date/Time</label><input type="datetime-local" value=${form.scheduled_at} onInput=${e => setForm({...form, scheduled_at: e.target.value})} /></div>
            <div><label>Recurring</label>
              <select value=${form.recurring} onChange=${e => setForm({...form, recurring: e.target.value})}>
                <option value="none">None</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
          </div>
          <label>Notes</label>
          <input value=${form.notes} onInput=${e => setForm({...form, notes: e.target.value})} />
          <button class="btn" onClick=${add} style="margin-top:0.5rem">Save</button>
        </div>
      `}
      <div class="calendar">
        ${contacts.map(c => html`
          <div class="cal-entry">
            <div class="time">${c.scheduled_at} (${c.duration_minutes}min)</div>
            <div class="title">${c.title} ${c.callsign && html`- <strong>${c.callsign}</strong>`}</div>
            <div class="meta">
              ${c.freq_mhz ? c.freq_mhz + ' MHz ' : ''}${c.mode} ${c.recurring !== 'none' ? '[' + c.recurring + ']' : ''}
              ${c.notes && html` - ${c.notes}`}
              <button class="btn danger" onClick=${() => remove(c.id)} style="margin-left:0.5rem;padding:0.1rem 0.4rem;font-size:0.75rem">X</button>
            </div>
          </div>
        `)}
        ${contacts.length === 0 && html`<div style="color:var(--text-dim)">No upcoming contacts scheduled</div>`}
      </div>
    </div>
  `;
}

// --- App Shell ---
function App() {
  const [tab, setTab] = useState('winlink');
  const [health, setHealth] = useState(null);

  useEffect(() => { api.get('/health').then(setHealth); }, []);

  const tabs = { winlink: WinlinkTab, js8call: JS8CallTab, frequencies: FrequenciesTab, scheduler: SchedulerTab };
  const TabContent = tabs[tab];

  return html`
    <header>
      <h1>HAM RADIO</h1>
      <nav>
        <button class=${tab === 'winlink' ? 'active' : ''} onClick=${() => setTab('winlink')}>Winlink</button>
        <button class=${tab === 'js8call' ? 'active' : ''} onClick=${() => setTab('js8call')}>JS8Call</button>
        <button class=${tab === 'frequencies' ? 'active' : ''} onClick=${() => setTab('frequencies')}>Frequencies</button>
        <button class=${tab === 'scheduler' ? 'active' : ''} onClick=${() => setTab('scheduler')}>Scheduler</button>
      </nav>
      <span class="status-dot ${health?.status === 'ok' ? 'ok' : 'err'}" title=${health?.status || 'loading'}></span>
    </header>
    <main>
      <${TabContent} />
    </main>
  `;
}

render(html`<${App} />`, document.getElementById('app'));
