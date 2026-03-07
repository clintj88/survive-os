import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);
const api = (path, opts) => fetch(`/api${path}`, {
  ...opts,
  headers: { 'Content-Type': 'application/json', ...opts?.headers },
}).then(r => r.ok ? (r.status === 204 ? null : r.json()) : Promise.reject(r));

// --- Tab Manager ---
function App() {
  const [tab, setTab] = useState('surveillance');

  useEffect(() => {
    document.querySelectorAll('.tab').forEach(el => {
      el.classList.toggle('active', el.dataset.tab === tab);
      el.onclick = () => setTab(el.dataset.tab);
    });
  }, [tab]);

  const panels = {
    surveillance: SurveillancePanel,
    alerts: AlertsPanel,
    contacts: ContactsPanel,
    quarantine: QuarantinePanel,
    history: HistoryPanel,
  };
  const Panel = panels[tab];
  return html`<${Panel} />`;
}

// --- Surveillance ---
function SurveillancePanel() {
  const [reports, setReports] = useState([]);
  const [counts, setCounts] = useState([]);
  const load = () => {
    api('/surveillance/reports').then(setReports);
    api('/surveillance/counts').then(setCounts);
  };
  useEffect(load, []);

  const syndromes = ['respiratory','gastrointestinal','fever/febrile','rash/dermatological','neurological','hemorrhagic','other'];
  const ageGroups = ['0-4','5-14','15-24','25-44','45-64','65+'];

  const submit = e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    api('/surveillance/reports', {
      method: 'POST',
      body: JSON.stringify(Object.fromEntries(fd)),
    }).then(() => { e.target.reset(); load(); });
  };

  const maxCount = Math.max(1, ...counts.map(c => c.count));

  return html`
    <div class="grid">
      <div class="card">
        <h3>Report Symptom</h3>
        <form onSubmit=${submit}>
          <label>Date <input name="date" type="date" required /></label>
          <label>Syndrome <select name="syndrome" required>
            ${syndromes.map(s => html`<option value=${s}>${s}</option>`)}
          </select></label>
          <label>Patient ID (optional) <input name="patient_id" /></label>
          <label>Age Group <select name="age_group" required>
            ${ageGroups.map(a => html`<option value=${a}>${a}</option>`)}
          </select></label>
          <label>Sex <select name="sex" required>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="unknown">Unknown</option>
          </select></label>
          <label>Area <input name="area" value="default" /></label>
          <label>Notes <textarea name="notes" rows="2"></textarea></label>
          <button class="btn" type="submit">Submit Report</button>
        </form>
      </div>
      <div class="card">
        <h3>Daily Counts</h3>
        <div class="bar-chart">
          ${counts.slice(-30).map(c => html`
            <div class="bar" style="height:${(c.count/maxCount)*100}%"
                 title="${c.period} - ${c.syndrome}: ${c.count}"></div>
          `)}
        </div>
        ${counts.length === 0 && html`<p class="empty">No data yet</p>`}
      </div>
    </div>
    <div class="card mt-1">
      <h3>Recent Reports (${reports.length})</h3>
      <table>
        <thead><tr><th>Date</th><th>Syndrome</th><th>Age</th><th>Sex</th><th>Area</th></tr></thead>
        <tbody>
          ${reports.slice(0, 50).map(r => html`
            <tr><td>${r.date}</td><td>${r.syndrome}</td><td>${r.age_group}</td><td>${r.sex}</td><td>${r.area}</td></tr>
          `)}
        </tbody>
      </table>
    </div>
  `;
}

// --- Alerts ---
function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const load = () => api('/alerts').then(setAlerts);
  useEffect(load, []);

  const runCheck = () => api('/alerts/check', { method: 'POST' }).then(load);
  const ack = id => api(`/alerts/${id}/acknowledge`, { method: 'POST' }).then(load);

  return html`
    <div style="display:flex;gap:0.5rem;margin-bottom:1rem">
      <button class="btn" onClick=${runCheck}>Run Threshold Check</button>
    </div>
    <div class="grid">
      ${alerts.map(a => html`
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <h3>${a.syndrome}</h3>
            <span class="badge badge-${a.level}">${a.level}</span>
          </div>
          <p style="font-size:0.875rem;margin:0.5rem 0">
            Count: <strong>${a.count}</strong> | Baseline: ${a.baseline} | ${a.multiplier}x
          </p>
          <p style="font-size:0.8rem;color:#94a3b8">${a.recommendation}</p>
          <p style="font-size:0.75rem;color:#64748b">Area: ${a.area} | ${a.created_at}</p>
          ${!a.acknowledged && html`
            <button class="btn mt-1" onClick=${() => ack(a.id)}>Acknowledge</button>
          `}
        </div>
      `)}
      ${alerts.length === 0 && html`<p class="empty">No alerts</p>`}
    </div>
  `;
}

// --- Contact Tracing ---
function ContactsPanel() {
  const [contacts, setContacts] = useState([]);
  const load = () => api('/contacts').then(setContacts);
  useEffect(load, []);

  const submit = e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = Object.fromEntries(fd);
    data.case_id = parseInt(data.case_id);
    api('/contacts', { method: 'POST', body: JSON.stringify(data) })
      .then(() => { e.target.reset(); load(); });
  };

  return html`
    <div class="grid">
      <div class="card">
        <h3>Add Contact</h3>
        <form onSubmit=${submit}>
          <label>Case ID <input name="case_id" type="number" required /></label>
          <label>Contact Person <input name="contact_person" required /></label>
          <label>Relationship <input name="relationship" /></label>
          <label>Date of Contact <input name="date_of_contact" type="date" required /></label>
          <label>Exposure <select name="exposure_type">
            <option value="casual">Casual</option>
            <option value="close">Close</option>
          </select></label>
          <button class="btn" type="submit">Add Contact</button>
        </form>
      </div>
    </div>
    <div class="card mt-1">
      <h3>Contact Records (${contacts.length})</h3>
      <table>
        <thead><tr><th>Case</th><th>Contact</th><th>Exposure</th><th>Risk</th><th>Status</th><th>Date</th></tr></thead>
        <tbody>
          ${contacts.map(c => html`
            <tr>
              <td>#${c.case_id}</td><td>${c.contact_person}</td>
              <td>${c.exposure_type}</td><td>${c.risk_score}</td>
              <td>${c.follow_up_status}</td><td>${c.date_of_contact}</td>
            </tr>
          `)}
        </tbody>
      </table>
    </div>
  `;
}

// --- Quarantine ---
function QuarantinePanel() {
  const [quarantines, setQuarantines] = useState([]);
  const [census, setCensus] = useState({});
  const load = () => {
    api('/quarantine').then(setQuarantines);
    api('/quarantine/census').then(setCensus);
  };
  useEffect(load, []);

  const submit = e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    api('/quarantine', { method: 'POST', body: JSON.stringify(Object.fromEntries(fd)) })
      .then(() => { e.target.reset(); load(); });
  };

  return html`
    <div class="grid">
      <div class="card stat"><div class="value">${census.active || 0}</div><div class="label">Active</div></div>
      <div class="card stat"><div class="value">${census.completed || 0}</div><div class="label">Completed</div></div>
      <div class="card stat"><div class="value">${census.released || 0}</div><div class="label">Released</div></div>
      <div class="card stat"><div class="value">${census.supplies_needed || 0}</div><div class="label">Supplies Needed</div></div>
    </div>
    <div class="grid mt-1">
      <div class="card">
        <h3>New Quarantine</h3>
        <form onSubmit=${submit}>
          <label>Person <input name="person" required /></label>
          <label>Start Date <input name="start_date" type="date" required /></label>
          <label>Expected End <input name="expected_end" type="date" required /></label>
          <label>Location <input name="location" /></label>
          <label>Reason <input name="reason" /></label>
          <button class="btn" type="submit">Create</button>
        </form>
      </div>
    </div>
    <div class="card mt-1">
      <h3>Quarantine Records</h3>
      <table>
        <thead><tr><th>Person</th><th>Start</th><th>End</th><th>Location</th><th>Status</th></tr></thead>
        <tbody>
          ${quarantines.map(q => html`
            <tr>
              <td>${q.person}</td><td>${q.start_date}</td><td>${q.expected_end}</td>
              <td>${q.location}</td>
              <td><span class="badge badge-${q.status}">${q.status}</span></td>
            </tr>
          `)}
        </tbody>
      </table>
    </div>
  `;
}

// --- History ---
function HistoryPanel() {
  const [events, setEvents] = useState([]);
  const load = () => api('/timeline/events').then(setEvents);
  useEffect(load, []);

  const submit = e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = Object.fromEntries(fd);
    data.total_cases = parseInt(data.total_cases) || 0;
    data.total_deaths = parseInt(data.total_deaths) || 0;
    api('/timeline/events', { method: 'POST', body: JSON.stringify(data) })
      .then(() => { e.target.reset(); load(); });
  };

  return html`
    <div class="grid">
      <div class="card">
        <h3>Record Event</h3>
        <form onSubmit=${submit}>
          <label>Name <input name="name" required /></label>
          <label>Pathogen <input name="pathogen" value="unknown" /></label>
          <label>Start Date <input name="start_date" type="date" required /></label>
          <label>End Date <input name="end_date" type="date" /></label>
          <label>Total Cases <input name="total_cases" type="number" value="0" /></label>
          <label>Total Deaths <input name="total_deaths" type="number" value="0" /></label>
          <label>Response Actions <textarea name="response_actions" rows="2"></textarea></label>
          <label>Lessons Learned <textarea name="lessons_learned" rows="2"></textarea></label>
          <button class="btn" type="submit">Record Event</button>
        </form>
      </div>
    </div>
    <div class="card mt-1">
      <h3>Epidemic Timeline</h3>
      ${events.map(ev => html`
        <div class="card" style="border-left:3px solid #f97316">
          <h3>${ev.name} ${ev.pathogen !== 'unknown' ? html`<span style="color:#94a3b8">(${ev.pathogen})</span>` : ''}</h3>
          <p style="font-size:0.875rem">${ev.start_date} ${ev.end_date ? `- ${ev.end_date}` : '(ongoing)'}</p>
          <p style="font-size:0.875rem">Cases: ${ev.total_cases} | Deaths: ${ev.total_deaths}</p>
          ${ev.response_actions && html`<p style="font-size:0.8rem;color:#94a3b8;margin-top:0.25rem">${ev.response_actions}</p>`}
          ${ev.lessons_learned && html`<p style="font-size:0.8rem;color:#fbbf24;margin-top:0.25rem">${ev.lessons_learned}</p>`}
        </div>
      `)}
      ${events.length === 0 && html`<p class="empty">No historical events recorded</p>`}
    </div>
  `;
}

render(html`<${App} />`, document.getElementById('app'));
