import { html, render, useState, useEffect } from 'https://esm.sh/htm/preact/standalone';

const api = (path, opts) => fetch(path, { headers: { 'Content-Type': 'application/json' }, ...opts }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(e)));

// --- Census Tab ---
function CensusTab() {
  const [persons, setPersons] = useState([]);
  const [stats, setStats] = useState(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', dob: '', sex: '', occupation: '', housing_assignment: '' });

  const load = () => {
    api(`/api/census/persons?search=${search}`).then(setPersons);
    api('/api/census/stats').then(setStats);
  };
  useEffect(load, [search]);

  const submit = () => {
    api('/api/census/persons', { method: 'POST', body: JSON.stringify(form) })
      .then(() => { setShowForm(false); setForm({ name: '', dob: '', sex: '', occupation: '', housing_assignment: '' }); load(); });
  };

  return html`
    <div>
      ${stats && html`
        <div class="grid" style="margin-bottom:1rem">
          <div class="stat-box"><div class="value">${stats.total_active}</div><div class="label">Active Population</div></div>
          <div class="stat-box"><div class="value">${stats.skills_summary?.length || 0}</div><div class="label">Skill Categories</div></div>
          <div class="stat-box"><div class="value">${stats.by_status?.find(s=>s.status==='deceased')?.count || 0}</div><div class="label">Deceased</div></div>
        </div>
      `}
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
          <h3>Population Registry</h3>
          <button class="btn" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'Add Person'}</button>
        </div>
        <input placeholder="Search by name..." value=${search} onInput=${e => setSearch(e.target.value)} />
        ${showForm && html`
          <div class="card" style="margin-bottom:0.5rem">
            <div class="form-row">
              <input placeholder="Name" value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} />
              <input type="date" placeholder="DOB" value=${form.dob} onInput=${e => setForm({...form, dob: e.target.value})} />
            </div>
            <div class="form-row">
              <select value=${form.sex} onChange=${e => setForm({...form, sex: e.target.value})}>
                <option value="">Sex</option><option value="M">Male</option><option value="F">Female</option><option value="X">Other</option>
              </select>
              <input placeholder="Occupation" value=${form.occupation} onInput=${e => setForm({...form, occupation: e.target.value})} />
            </div>
            <input placeholder="Housing Assignment" value=${form.housing_assignment} onInput=${e => setForm({...form, housing_assignment: e.target.value})} />
            <button class="btn" onClick=${submit}>Save</button>
          </div>
        `}
        <table>
          <thead><tr><th>Name</th><th>DOB</th><th>Status</th><th>Occupation</th><th>Arrived</th></tr></thead>
          <tbody>${persons.map(p => html`
            <tr key=${p.id}>
              <td>${p.name}</td><td>${p.dob || '-'}</td>
              <td><span class="badge badge-${p.status}">${p.status}</span></td>
              <td>${p.occupation || '-'}</td><td>${p.arrival_date}</td>
            </tr>
          `)}</tbody>
        </table>
      </div>
    </div>`;
}

// --- Voting Tab ---
function VotingTab() {
  const [ballots, setBallots] = useState([]);
  const [results, setResults] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', ballot_type: 'yes_no', options: 'yes,no', voting_period_end: '', created_by: '' });

  const load = () => api('/api/voting/ballots').then(setBallots);
  useEffect(load, []);

  const submit = () => {
    const opts = form.options.split(',').map(s => s.trim());
    api('/api/voting/ballots', { method: 'POST', body: JSON.stringify({ ...form, options: opts }) })
      .then(() => { setShowForm(false); load(); });
  };

  const viewResults = (id) => api(`/api/voting/ballots/${id}/results`).then(setResults);

  return html`
    <div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
          <h3>Ballots</h3>
          <button class="btn" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'New Ballot'}</button>
        </div>
        ${showForm && html`
          <div class="card">
            <input placeholder="Title" value=${form.title} onInput=${e => setForm({...form, title: e.target.value})} />
            <textarea placeholder="Description" value=${form.description} onInput=${e => setForm({...form, description: e.target.value})} />
            <div class="form-row">
              <select value=${form.ballot_type} onChange=${e => setForm({...form, ballot_type: e.target.value})}>
                <option value="yes_no">Yes/No</option><option value="multiple_choice">Multiple Choice</option><option value="ranked_choice">Ranked Choice</option>
              </select>
              <input placeholder="Options (comma separated)" value=${form.options} onInput=${e => setForm({...form, options: e.target.value})} />
            </div>
            <div class="form-row">
              <input type="datetime-local" placeholder="End Date" value=${form.voting_period_end} onInput=${e => setForm({...form, voting_period_end: e.target.value})} />
              <input placeholder="Created By" value=${form.created_by} onInput=${e => setForm({...form, created_by: e.target.value})} />
            </div>
            <button class="btn" onClick=${submit}>Create Ballot</button>
          </div>
        `}
        ${ballots.map(b => html`
          <div class="card" key=${b.id}>
            <h4>${b.title}</h4>
            <p style="color:var(--muted)">${b.description}</p>
            <p>Type: ${b.ballot_type} | Ends: ${b.voting_period_end}</p>
            <button class="btn btn-secondary" onClick=${() => viewResults(b.id)}>View Results</button>
          </div>
        `)}
      </div>
      ${results && html`
        <div class="card">
          <h3>Results: ${results.title}</h3>
          <p>Total votes: ${results.total_votes}</p>
          <table>
            <thead><tr><th>Option</th><th>Votes</th></tr></thead>
            <tbody>${Object.entries(results.tally || {}).map(([k, v]) => html`<tr><td>${k}</td><td>${v}</td></tr>`)}</tbody>
          </table>
        </div>
      `}
    </div>`;
}

// --- Resources Tab ---
function ResourcesTab() {
  const [inventory, setInventory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ category: 'food', name: '', quantity: 0, unit: 'units', low_threshold: 10 });

  const load = () => {
    api('/api/resources/inventory').then(setInventory);
    api('/api/resources/alerts').then(setAlerts);
  };
  useEffect(load, []);

  const submit = () => {
    api('/api/resources/inventory', { method: 'POST', body: JSON.stringify(form) })
      .then(() => { setShowForm(false); load(); });
  };

  return html`
    <div>
      ${alerts.length > 0 && html`
        <div class="card" style="border-color:var(--warning)">
          <h3 style="color:var(--warning)">Low Resource Alerts</h3>
          ${alerts.map(a => html`<p key=${a.id}>${a.name} (${a.category}): ${a.quantity} ${a.unit} remaining</p>`)}
        </div>
      `}
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
          <h3>Inventory</h3>
          <button class="btn" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'Add Resource'}</button>
        </div>
        ${showForm && html`
          <div class="card">
            <div class="form-row">
              <select value=${form.category} onChange=${e => setForm({...form, category: e.target.value})}>
                <option value="food">Food</option><option value="water">Water</option><option value="fuel">Fuel</option>
                <option value="medicine">Medicine</option><option value="building_materials">Building Materials</option><option value="tools">Tools</option>
              </select>
              <input placeholder="Name" value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} />
            </div>
            <div class="form-row">
              <input type="number" placeholder="Quantity" value=${form.quantity} onInput=${e => setForm({...form, quantity: +e.target.value})} />
              <input placeholder="Unit" value=${form.unit} onInput=${e => setForm({...form, unit: e.target.value})} />
              <input type="number" placeholder="Low Threshold" value=${form.low_threshold} onInput=${e => setForm({...form, low_threshold: +e.target.value})} />
            </div>
            <button class="btn" onClick=${submit}>Save</button>
          </div>
        `}
        <table>
          <thead><tr><th>Category</th><th>Name</th><th>Quantity</th><th>Unit</th><th>Status</th></tr></thead>
          <tbody>${inventory.map(r => html`
            <tr key=${r.id}>
              <td>${r.category}</td><td>${r.name}</td><td>${r.quantity}</td><td>${r.unit}</td>
              <td><span class="badge ${r.quantity <= r.low_threshold ? 'badge-open' : 'badge-active'}">${r.quantity <= r.low_threshold ? 'LOW' : 'OK'}</span></td>
            </tr>
          `)}</tbody>
        </table>
      </div>
    </div>`;
}

// --- Journal Tab ---
function JournalTab() {
  const [entries, setEntries] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', content: '', author: '', category: 'daily_log' });

  const load = () => api('/api/journal/entries').then(setEntries);
  useEffect(load, []);

  const submit = () => {
    api('/api/journal/entries', { method: 'POST', body: JSON.stringify(form) })
      .then(() => { setShowForm(false); setForm({ title: '', content: '', author: '', category: 'daily_log' }); load(); });
  };

  return html`
    <div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
          <h3>Community Journal</h3>
          <button class="btn" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'New Entry'}</button>
        </div>
        ${showForm && html`
          <div class="card">
            <input placeholder="Title" value=${form.title} onInput=${e => setForm({...form, title: e.target.value})} />
            <textarea placeholder="Content" value=${form.content} onInput=${e => setForm({...form, content: e.target.value})} />
            <div class="form-row">
              <input placeholder="Author" value=${form.author} onInput=${e => setForm({...form, author: e.target.value})} />
              <select value=${form.category} onChange=${e => setForm({...form, category: e.target.value})}>
                <option value="daily_log">Daily Log</option><option value="event">Event</option>
                <option value="milestone">Milestone</option><option value="memorial">Memorial</option>
              </select>
            </div>
            <button class="btn" onClick=${submit}>Save Entry</button>
          </div>
        `}
        ${entries.map(e => html`
          <div class="timeline-entry" key=${e.id}>
            <div class="date">${e.entry_date} - ${e.category}</div>
            <h4>${e.title}</h4>
            <p>${e.content}</p>
            <small style="color:var(--muted)">by ${e.author}</small>
          </div>
        `)}
      </div>
    </div>`;
}

// --- Calendar Tab ---
function CalendarTab() {
  const [events, setEvents] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', event_date: '', event_time: '', location: '', event_type: 'meeting', description: '', recurring: false });
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));

  const load = () => api(`/api/calendar/events?month=${month}`).then(setEvents);
  useEffect(load, [month]);

  const submit = () => {
    api('/api/calendar/events', { method: 'POST', body: JSON.stringify(form) })
      .then(() => { setShowForm(false); load(); });
  };

  const daysInMonth = new Date(+month.slice(0,4), +month.slice(5,7), 0).getDate();
  const firstDay = new Date(+month.slice(0,4), +month.slice(5,7)-1, 1).getDay();
  const days = Array.from({length: daysInMonth}, (_, i) => i + 1);
  const blanks = Array.from({length: firstDay}, () => null);

  return html`
    <div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
          <h3>Calendar: ${month}</h3>
          <div style="display:flex;gap:0.5rem">
            <input type="month" value=${month} onChange=${e => setMonth(e.target.value)} />
            <button class="btn" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'Add Event'}</button>
          </div>
        </div>
        ${showForm && html`
          <div class="card">
            <input placeholder="Title" value=${form.title} onInput=${e => setForm({...form, title: e.target.value})} />
            <div class="form-row">
              <input type="date" value=${form.event_date} onInput=${e => setForm({...form, event_date: e.target.value})} />
              <input type="time" value=${form.event_time} onInput=${e => setForm({...form, event_time: e.target.value})} />
            </div>
            <div class="form-row">
              <input placeholder="Location" value=${form.location} onInput=${e => setForm({...form, location: e.target.value})} />
              <select value=${form.event_type} onChange=${e => setForm({...form, event_type: e.target.value})}>
                <option value="meeting">Meeting</option><option value="celebration">Celebration</option>
                <option value="memorial">Memorial</option><option value="seasonal">Seasonal</option><option value="work">Work</option>
              </select>
            </div>
            <textarea placeholder="Description" value=${form.description} onInput=${e => setForm({...form, description: e.target.value})} />
            <button class="btn" onClick=${submit}>Save Event</button>
          </div>
        `}
        <div class="calendar-grid">
          ${['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => html`<div class="day-header">${d}</div>`)}
          ${blanks.map(() => html`<div class="day-cell"></div>`)}
          ${days.map(d => {
            const dateStr = month + '-' + String(d).padStart(2, '0');
            const dayEvents = events.filter(e => e.event_date === dateStr);
            return html`<div class="day-cell">
              <div class="day-num">${d}</div>
              ${dayEvents.map(e => html`<div class="event-dot" key=${e.id}>${e.title}</div>`)}
            </div>`;
          })}
        </div>
      </div>
      <div class="card">
        <h3>Events This Month</h3>
        <table>
          <thead><tr><th>Date</th><th>Time</th><th>Title</th><th>Type</th><th>Location</th></tr></thead>
          <tbody>${events.map(e => html`
            <tr key=${e.id}><td>${e.event_date}</td><td>${e.event_time || '-'}</td><td>${e.title}</td><td>${e.event_type}</td><td>${e.location || '-'}</td></tr>
          `)}</tbody>
        </table>
      </div>
    </div>`;
}

// --- App ---
function App() {
  const [tab, setTab] = useState('census');
  const tabs = [
    ['census', 'Census'], ['voting', 'Voting'], ['resources', 'Resources'],
    ['journal', 'Journal'], ['calendar', 'Calendar'],
    ['treaties', 'Treaties'], ['disputes', 'Disputes'],
    ['duties', 'Duties'], ['registry', 'Registry'],
  ];

  const content = {
    census: html`<${CensusTab} />`,
    voting: html`<${VotingTab} />`,
    resources: html`<${ResourcesTab} />`,
    journal: html`<${JournalTab} />`,
    calendar: html`<${CalendarTab} />`,
    treaties: html`<p class="card">Treaties management - use API at /api/treaties</p>`,
    disputes: html`<p class="card">Dispute resolution - use API at /api/disputes</p>`,
    duties: html`<p class="card">Duty scheduling - use API at /api/duties</p>`,
    registry: html`<p class="card">Civil registry - use API at /api/registry</p>`,
  };

  return html`
    <header>
      <h1>SURVIVE OS Governance</h1>
      <nav>
        ${tabs.map(([id, label]) => html`
          <button key=${id} class=${tab === id ? 'active' : ''} onClick=${() => setTab(id)}>${label}</button>
        `)}
      </nav>
    </header>
    <main>${content[tab]}</main>
  `;
}

render(html`<${App} />`, document.getElementById('app'));
