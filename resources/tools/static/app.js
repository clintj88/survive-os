import { html, render, useState, useEffect, useCallback } from 'https://unpkg.com/htm/preact/standalone.module.js';

const API = '';

async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 204) return null;
  return res.json();
}

// --- Components ---

function Badge({ type, text }) {
  return html`<span class="badge badge-${type}">${text || type}</span>`;
}

function Modal({ title, onClose, children }) {
  return html`
    <div class="modal-overlay" onClick=${e => e.target === e.currentTarget && onClose()}>
      <div class="modal">
        <h2>${title}</h2>
        ${children}
      </div>
    </div>`;
}

// --- Tools Tab ---

function ToolsTab() {
  const [tools, setTools] = useState([]);
  const [filter, setFilter] = useState({ category: '', condition: '', status: '', search: '' });
  const [showForm, setShowForm] = useState(false);

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (filter.category) params.set('category', filter.category);
    if (filter.condition) params.set('condition', filter.condition);
    if (filter.status) params.set('status', filter.status);
    if (filter.search) params.set('search', filter.search);
    const q = params.toString();
    setTools(await api('/api/tools' + (q ? '?' + q : '')));
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const categories = ['hand_tools','power_tools','garden','mechanical','kitchen','medical','measuring','safety'];
  const conditions = ['excellent','good','fair','poor','broken'];

  return html`
    <div class="filters">
      <select value=${filter.category} onChange=${e => setFilter({...filter, category: e.target.value})}>
        <option value="">All Categories</option>
        ${categories.map(c => html`<option value=${c}>${c.replace('_', ' ')}</option>`)}
      </select>
      <select value=${filter.condition} onChange=${e => setFilter({...filter, condition: e.target.value})}>
        <option value="">All Conditions</option>
        ${conditions.map(c => html`<option value=${c}>${c}</option>`)}
      </select>
      <select value=${filter.status} onChange=${e => setFilter({...filter, status: e.target.value})}>
        <option value="">All Statuses</option>
        <option value="available">Available</option>
        <option value="checked_out">Checked Out</option>
        <option value="maintenance">Maintenance</option>
        <option value="retired">Retired</option>
      </select>
      <input placeholder="Search..." value=${filter.search}
        onInput=${e => setFilter({...filter, search: e.target.value})} />
      <button class="btn-primary" onClick=${() => setShowForm(true)}>+ Add Tool</button>
    </div>
    <div class="grid">
      ${tools.length === 0 && html`<div class="empty">No tools found</div>`}
      ${tools.map(t => html`
        <div class="card">
          <h3>${t.name}</h3>
          <p>${t.description || 'No description'}</p>
          <p>${t.category.replace('_', ' ')} · ${t.location || 'Unknown location'}</p>
          <div style="margin-top:0.5rem;display:flex;gap:0.3rem">
            <${Badge} type=${t.status} />
            <${Badge} type=${t.condition} />
          </div>
        </div>
      `)}
    </div>
    ${showForm && html`<${ToolForm} onClose=${() => { setShowForm(false); load(); }} />`}`;
}

function ToolForm({ onClose }) {
  const [form, setForm] = useState({
    name: '', category: 'hand_tools', description: '', condition: 'good', location: '',
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async () => {
    await api('/api/tools', { method: 'POST', body: form });
    onClose();
  };

  return html`<${Modal} title="Add Tool" onClose=${onClose}>
    <div class="form-group"><label>Name</label>
      <input value=${form.name} onInput=${e => set('name', e.target.value)} /></div>
    <div class="form-group"><label>Category</label>
      <select value=${form.category} onChange=${e => set('category', e.target.value)}>
        ${['hand_tools','power_tools','garden','mechanical','kitchen','medical','measuring','safety']
          .map(c => html`<option value=${c}>${c.replace('_',' ')}</option>`)}
      </select></div>
    <div class="form-group"><label>Description</label>
      <textarea value=${form.description} onInput=${e => set('description', e.target.value)} /></div>
    <div class="form-group"><label>Condition</label>
      <select value=${form.condition} onChange=${e => set('condition', e.target.value)}>
        ${['excellent','good','fair','poor'].map(c => html`<option value=${c}>${c}</option>`)}
      </select></div>
    <div class="form-group"><label>Location</label>
      <input value=${form.location} onInput=${e => set('location', e.target.value)} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Save</button>
    </div>
  <//>`;
}

// --- Checkout Tab ---

function CheckoutTab() {
  const [active, setActive] = useState([]);
  const [overdue, setOverdue] = useState([]);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setActive(await api('/api/checkouts?active=true'));
    setOverdue(await api('/api/checkouts/overdue'));
  };

  useEffect(() => { load(); }, []);

  const checkin = async (id) => {
    const cond = prompt('Return condition (excellent/good/fair/poor/broken):', 'good');
    if (!cond) return;
    await api(`/api/checkouts/${id}/checkin`, { method: 'POST', body: { condition_at_return: cond } });
    load();
  };

  return html`
    <div style="margin-bottom:1rem">
      <button class="btn-primary" onClick=${() => setShowForm(true)}>+ Check Out Tool</button>
    </div>
    ${overdue.length > 0 && html`
      <h3 style="color:var(--danger);margin-bottom:0.5rem">Overdue Returns</h3>
      <table>
        <thead><tr><th>Tool</th><th>Borrower</th><th>Due</th><th></th></tr></thead>
        <tbody>${overdue.map(c => html`<tr>
          <td>${c.tool_name}</td><td>${c.borrowed_by}</td>
          <td><${Badge} type="overdue" text=${c.expected_return_date} /></td>
          <td><button class="btn-success btn-sm" onClick=${() => checkin(c.id)}>Return</button></td>
        </tr>`)}</tbody>
      </table>`}
    <h3 style="margin:1rem 0 0.5rem">Currently Borrowed</h3>
    ${active.length === 0 ? html`<div class="empty">No active checkouts</div>` : html`
      <table>
        <thead><tr><th>Tool</th><th>Borrower</th><th>Checked Out</th><th>Due</th><th></th></tr></thead>
        <tbody>${active.map(c => html`<tr>
          <td>${c.tool_name}</td><td>${c.borrowed_by}</td>
          <td>${c.checkout_date?.slice(0,10)}</td><td>${c.expected_return_date}</td>
          <td><button class="btn-success btn-sm" onClick=${() => checkin(c.id)}>Return</button></td>
        </tr>`)}</tbody>
      </table>`}
    ${showForm && html`<${CheckoutForm} onClose=${() => { setShowForm(false); load(); }} />`}`;
}

function CheckoutForm({ onClose }) {
  const [tools, setTools] = useState([]);
  const [form, setForm] = useState({ tool_id: '', borrowed_by: '', expected_return_date: '', notes: '' });

  useEffect(async () => {
    setTools(await api('/api/tools?status=available'));
  }, []);

  const submit = async () => {
    await api('/api/checkouts', { method: 'POST', body: { ...form, tool_id: parseInt(form.tool_id) } });
    onClose();
  };

  return html`<${Modal} title="Check Out Tool" onClose=${onClose}>
    <div class="form-group"><label>Tool</label>
      <select value=${form.tool_id} onChange=${e => setForm({...form, tool_id: e.target.value})}>
        <option value="">Select tool...</option>
        ${tools.map(t => html`<option value=${t.id}>${t.name}</option>`)}
      </select></div>
    <div class="form-group"><label>Borrowed By</label>
      <input value=${form.borrowed_by} onInput=${e => setForm({...form, borrowed_by: e.target.value})} /></div>
    <div class="form-group"><label>Expected Return Date</label>
      <input type="date" value=${form.expected_return_date}
        onInput=${e => setForm({...form, expected_return_date: e.target.value})} /></div>
    <div class="form-group"><label>Notes</label>
      <textarea value=${form.notes} onInput=${e => setForm({...form, notes: e.target.value})} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Check Out</button>
    </div>
  <//>`;
}

// --- Maintenance Tab ---

function MaintenanceTab() {
  const [tasks, setTasks] = useState([]);
  const [overdue, setOverdue] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const load = async () => {
    setTasks(await api('/api/maintenance/tasks'));
    setOverdue(await api('/api/maintenance/overdue'));
    setAlerts(await api('/api/maintenance/condition-alerts'));
  };

  useEffect(() => { load(); }, []);

  const complete = async (id) => {
    const by = prompt('Performed by:');
    if (by === null) return;
    await api(`/api/maintenance/tasks/${id}/complete`, { method: 'POST', body: { performed_by: by } });
    load();
  };

  return html`
    ${alerts.length > 0 && html`
      <h3 style="color:var(--warn);margin-bottom:0.5rem">Condition Downgrade Suggestions</h3>
      <div class="grid" style="margin-bottom:1rem">
        ${alerts.map(a => html`<div class="card">
          <h3>${a.name}</h3>
          <p>Current: <${Badge} type=${a.condition} /> · ${a.overdue_tasks} overdue task(s)</p>
          <p>Oldest overdue: ${a.oldest_overdue}</p>
        </div>`)}
      </div>`}
    ${overdue.length > 0 && html`
      <h3 style="color:var(--danger);margin-bottom:0.5rem">Overdue Maintenance</h3>
      <table style="margin-bottom:1rem">
        <thead><tr><th>Tool</th><th>Task</th><th>Due</th><th></th></tr></thead>
        <tbody>${overdue.map(t => html`<tr>
          <td>${t.tool_name}</td><td>${t.task}</td>
          <td><${Badge} type="overdue" text=${t.next_due} /></td>
          <td><button class="btn-success btn-sm" onClick=${() => complete(t.id)}>Done</button></td>
        </tr>`)}</tbody>
      </table>`}
    <h3 style="margin-bottom:0.5rem">All Scheduled Tasks</h3>
    ${tasks.length === 0 ? html`<div class="empty">No maintenance tasks</div>` : html`
      <table>
        <thead><tr><th>Tool</th><th>Task</th><th>Freq</th><th>Last</th><th>Next Due</th><th></th></tr></thead>
        <tbody>${tasks.map(t => html`<tr>
          <td>${t.tool_name}</td><td>${t.task}</td><td>${t.frequency_days}d</td>
          <td>${t.last_performed?.slice(0,10) || '-'}</td><td>${t.next_due}</td>
          <td><button class="btn-success btn-sm" onClick=${() => complete(t.id)}>Done</button></td>
        </tr>`)}</tbody>
      </table>`}`;
}

// --- Usage Tab ---

function UsageTab() {
  const [mostUsed, setMostUsed] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(async () => {
    setMostUsed(await api('/api/usage/most-used'));
    setAlerts(await api('/api/usage/replacement-alerts'));
  }, []);

  const wearColor = pct => pct >= 80 ? 'progress-high' : pct >= 50 ? 'progress-mid' : 'progress-low';

  return html`
    ${alerts.length > 0 && html`
      <h3 style="color:var(--danger);margin-bottom:0.5rem">Replacement Planning</h3>
      <div class="grid" style="margin-bottom:1rem">
        ${alerts.map(a => html`<div class="card">
          <h3>${a.tool_name}</h3>
          <p>${a.category.replace('_',' ')} · <${Badge} type=${a.condition} /></p>
          <div class="progress-bar" style="margin:0.5rem 0">
            <div class="progress-fill ${wearColor(a.wear_percentage)}" style="width:${a.wear_percentage}%"></div>
          </div>
          <p>${a.wear_percentage}% worn · ${a.remaining_life_days} days remaining</p>
          ${a.estimated_replacement_date && html`<p>Replace by: ${a.estimated_replacement_date}</p>`}
        </div>`)}
      </div>`}
    <h3 style="margin-bottom:0.5rem">Most Used Tools</h3>
    ${mostUsed.length === 0 ? html`<div class="empty">No usage data yet</div>` : html`
      <table>
        <thead><tr><th>Tool</th><th>Category</th><th>Checkouts</th><th>Days Used</th><th>Condition</th></tr></thead>
        <tbody>${mostUsed.map(t => html`<tr>
          <td>${t.name}</td><td>${t.category.replace('_',' ')}</td>
          <td>${t.checkout_count}</td><td>${t.total_days_used || 0}</td>
          <td><${Badge} type=${t.condition} /></td>
        </tr>`)}</tbody>
      </table>`}`;
}

// --- Reservations Tab ---

function ReservationsTab() {
  const [reservations, setReservations] = useState([]);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setReservations(await api('/api/reservations?status=active'));
  };

  useEffect(() => { load(); }, []);

  const cancel = async (id) => {
    await api(`/api/reservations/${id}/cancel`, { method: 'POST' });
    load();
  };

  return html`
    <div style="margin-bottom:1rem">
      <button class="btn-primary" onClick=${() => setShowForm(true)}>+ Reserve Tool</button>
    </div>
    ${reservations.length === 0 ? html`<div class="empty">No active reservations</div>` : html`
      <table>
        <thead><tr><th>Tool</th><th>Reserved By</th><th>Date Needed</th><th>Duration</th><th>Purpose</th><th></th></tr></thead>
        <tbody>${reservations.map(r => html`<tr>
          <td>${r.tool_name}</td><td>${r.reserved_by}</td>
          <td>${r.date_needed}</td><td>${r.duration_days}d</td>
          <td>${r.purpose || '-'}</td>
          <td><button class="btn-sm btn-secondary" onClick=${() => cancel(r.id)}>Cancel</button></td>
        </tr>`)}</tbody>
      </table>`}
    ${showForm && html`<${ReservationForm} onClose=${() => { setShowForm(false); load(); }} />`}`;
}

function ReservationForm({ onClose }) {
  const [tools, setTools] = useState([]);
  const [form, setForm] = useState({ tool_id: '', reserved_by: '', date_needed: '', duration_days: 1, purpose: '' });

  useEffect(async () => { setTools(await api('/api/tools')); }, []);

  const submit = async () => {
    const res = await api('/api/reservations', {
      method: 'POST',
      body: { ...form, tool_id: parseInt(form.tool_id), duration_days: parseInt(form.duration_days) },
    });
    if (res.id) onClose();
    else alert('Conflict: tool already reserved for that date range');
  };

  return html`<${Modal} title="Reserve Tool" onClose=${onClose}>
    <div class="form-group"><label>Tool</label>
      <select value=${form.tool_id} onChange=${e => setForm({...form, tool_id: e.target.value})}>
        <option value="">Select tool...</option>
        ${tools.map(t => html`<option value=${t.id}>${t.name}</option>`)}
      </select></div>
    <div class="form-group"><label>Reserved By</label>
      <input value=${form.reserved_by} onInput=${e => setForm({...form, reserved_by: e.target.value})} /></div>
    <div class="form-group"><label>Date Needed</label>
      <input type="date" value=${form.date_needed}
        onInput=${e => setForm({...form, date_needed: e.target.value})} /></div>
    <div class="form-group"><label>Duration (days)</label>
      <input type="number" min="1" value=${form.duration_days}
        onInput=${e => setForm({...form, duration_days: e.target.value})} /></div>
    <div class="form-group"><label>Purpose</label>
      <textarea value=${form.purpose} onInput=${e => setForm({...form, purpose: e.target.value})} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Reserve</button>
    </div>
  <//>`;
}

// --- App ---

function App() {
  const [tab, setTab] = useState('tools');
  const tabs = [
    ['tools', 'Tools'],
    ['checkout', 'Checkout'],
    ['maintenance', 'Maintenance'],
    ['usage', 'Usage'],
    ['reservations', 'Reservations'],
  ];

  return html`
    <header>
      <h1>Tool Library</h1>
      <span style="color:var(--muted);font-size:0.85rem">SURVIVE OS</span>
    </header>
    <div class="tabs">
      ${tabs.map(([id, label]) => html`
        <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
      `)}
    </div>
    <div class="content">
      ${tab === 'tools' && html`<${ToolsTab} />`}
      ${tab === 'checkout' && html`<${CheckoutTab} />`}
      ${tab === 'maintenance' && html`<${MaintenanceTab} />`}
      ${tab === 'usage' && html`<${UsageTab} />`}
      ${tab === 'reservations' && html`<${ReservationsTab} />`}
    </div>`;
}

render(html`<${App} />`, document.getElementById('app'));
