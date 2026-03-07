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

function SocGauge({ percent }) {
  const color = percent > 50 ? 'var(--success)' : percent > 20 ? 'var(--warn)' : 'var(--danger)';
  return html`
    <span class="soc-gauge">
      <span class="soc-fill" style="width:${percent}%;background:${color}"></span>
    </span>
    <span>${percent}%</span>`;
}

// --- Solar Tab ---

function SolarTab() {
  const [panels, setPanels] = useState([]);
  const [efficiency, setEfficiency] = useState([]);
  const [production, setProduction] = useState([]);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setPanels(await api('/api/solar/panels'));
    setEfficiency(await api('/api/solar/efficiency'));
    setProduction(await api('/api/solar/production/daily?days=7'));
  };

  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t); }, []);

  return html`
    <div style="margin-bottom:1rem">
      <button class="btn-primary" onClick=${() => setShowForm(true)}>+ Add Panel</button>
    </div>
    <div class="grid">
      ${panels.length === 0 && html`<div class="empty">No solar panels registered</div>`}
      ${panels.map(p => {
        const eff = efficiency.find(e => e.panel_id === p.id);
        return html`
          <div class="card">
            <h3>${p.name}</h3>
            <p>Rated: ${p.rated_watts}W · ${p.orientation} @ ${p.tilt_angle} deg</p>
            <p>Location: ${p.location || 'N/A'}</p>
            ${eff && html`
              <p>Avg output: ${eff.avg_output_watts}W (${eff.efficiency_percent}% eff)</p>
              <div class="progress-bar" style="margin:0.5rem 0">
                <div class="progress-fill ${eff.efficiency_percent > 50 ? 'progress-high' : eff.efficiency_percent > 25 ? 'progress-mid' : 'progress-low'}"
                     style="width:${Math.min(100, eff.efficiency_percent)}%"></div>
              </div>`}
          </div>`;
      })}
    </div>
    ${production.length > 0 && html`
      <h3 style="margin:1.5rem 0 0.5rem">Daily Production (last 7 days)</h3>
      <table>
        <thead><tr><th>Panel</th><th>Date</th><th>Total Wh</th><th>Readings</th></tr></thead>
        <tbody>${production.map(p => html`<tr>
          <td>${p.panel_id}</td><td>${p.date}</td><td>${Math.round(p.total_wh)}</td><td>${p.readings}</td>
        </tr>`)}</tbody>
      </table>`}
    ${showForm && html`<${PanelForm} onClose=${() => { setShowForm(false); load(); }} />`}`;
}

function PanelForm({ onClose }) {
  const [form, setForm] = useState({
    name: '', rated_watts: '', location: '', orientation: 'south', tilt_angle: '30',
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async () => {
    await api('/api/solar/panels', { method: 'POST', body: {
      ...form, rated_watts: parseFloat(form.rated_watts), tilt_angle: parseFloat(form.tilt_angle),
    }});
    onClose();
  };

  return html`<${Modal} title="Add Solar Panel" onClose=${onClose}>
    <div class="form-group"><label>Name</label>
      <input value=${form.name} onInput=${e => set('name', e.target.value)} /></div>
    <div class="form-group"><label>Rated Watts</label>
      <input type="number" value=${form.rated_watts} onInput=${e => set('rated_watts', e.target.value)} /></div>
    <div class="form-group"><label>Location</label>
      <input value=${form.location} onInput=${e => set('location', e.target.value)} /></div>
    <div class="form-group"><label>Orientation</label>
      <select value=${form.orientation} onChange=${e => set('orientation', e.target.value)}>
        ${['north','south','east','west'].map(d => html`<option value=${d}>${d}</option>`)}
      </select></div>
    <div class="form-group"><label>Tilt Angle</label>
      <input type="number" value=${form.tilt_angle} onInput=${e => set('tilt_angle', e.target.value)} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Save</button>
    </div>
  <//>`;
}

// --- Batteries Tab ---

function BatteriesTab() {
  const [banks, setBanks] = useState([]);
  const [lowAlerts, setLowAlerts] = useState([]);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    const b = await api('/api/batteries/banks');
    setBanks(b);
    setLowAlerts(await api('/api/batteries/low-battery'));
    // Fetch latest state for each bank
    for (const bank of b) {
      bank._latest = await api(`/api/batteries/state/${bank.id}/latest`);
      bank._cycles = await api(`/api/batteries/cycles/${bank.id}`);
    }
    setBanks([...b]);
  };

  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t); }, []);

  return html`
    <div style="margin-bottom:1rem">
      <button class="btn-primary" onClick=${() => setShowForm(true)}>+ Add Battery Bank</button>
    </div>
    ${lowAlerts.length > 0 && html`
      <h3 style="color:var(--danger);margin-bottom:0.5rem">Low Battery Alerts</h3>
      <div class="grid" style="margin-bottom:1rem">
        ${lowAlerts.map(a => html`<div class="card" style="border-color:var(--danger)">
          <h3>${a.name}</h3>
          <p><${SocGauge} percent=${a.soc_percent} /></p>
          <p>${a.voltage}V · ${a.temperature ? a.temperature + ' C' : ''}</p>
        </div>`)}
      </div>`}
    <div class="grid">
      ${banks.length === 0 && html`<div class="empty">No battery banks registered</div>`}
      ${banks.map(b => {
        const soc = b._latest?.latest_state?.soc_percent;
        const health = b._cycles?.health_percent;
        return html`
          <div class="card">
            <h3>${b.name}</h3>
            <p>${b.type} · ${b.voltage}V · ${b.capacity_ah}Ah (${Math.round(b.capacity_ah * b.voltage)}Wh)</p>
            <p>${b.num_cells} cells</p>
            ${soc != null && html`<p style="margin-top:0.5rem"><${SocGauge} percent=${soc} /></p>`}
            ${health != null && html`<p>Health: ${health}% (${b._cycles.estimated_cycles} cycles)</p>`}
          </div>`;
      })}
    </div>
    ${showForm && html`<${BankForm} onClose=${() => { setShowForm(false); load(); }} />`}`;
}

function BankForm({ onClose }) {
  const [form, setForm] = useState({
    name: '', type: 'lead-acid', capacity_ah: '', voltage: '', num_cells: '1',
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async () => {
    await api('/api/batteries/banks', { method: 'POST', body: {
      ...form, capacity_ah: parseFloat(form.capacity_ah),
      voltage: parseFloat(form.voltage), num_cells: parseInt(form.num_cells),
    }});
    onClose();
  };

  return html`<${Modal} title="Add Battery Bank" onClose=${onClose}>
    <div class="form-group"><label>Name</label>
      <input value=${form.name} onInput=${e => set('name', e.target.value)} /></div>
    <div class="form-group"><label>Type</label>
      <select value=${form.type} onChange=${e => set('type', e.target.value)}>
        ${['lead-acid','lithium','nickel'].map(t => html`<option value=${t}>${t}</option>`)}
      </select></div>
    <div class="form-group"><label>Capacity (Ah)</label>
      <input type="number" value=${form.capacity_ah} onInput=${e => set('capacity_ah', e.target.value)} /></div>
    <div class="form-group"><label>Voltage</label>
      <input type="number" value=${form.voltage} onInput=${e => set('voltage', e.target.value)} /></div>
    <div class="form-group"><label>Number of Cells</label>
      <input type="number" min="1" value=${form.num_cells} onInput=${e => set('num_cells', e.target.value)} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Save</button>
    </div>
  <//>`;
}

// --- Fuel Tab ---

function FuelTab() {
  const [summary, setSummary] = useState([]);
  const [supply, setSupply] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showUseForm, setShowUseForm] = useState(false);

  const load = async () => {
    setSummary(await api('/api/fuel/summary'));
    setSupply(await api('/api/fuel/days-of-supply'));
  };

  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t); }, []);

  const fuelColors = {
    gasoline: '#e74c3c', diesel: '#f39c12', propane: '#3498db',
    firewood: '#8b4513', kerosene: '#9b59b6', ethanol: '#2ecc71',
  };

  const maxQty = Math.max(...summary.map(s => s.total_stored || 1), 1);

  return html`
    <div style="margin-bottom:1rem;display:flex;gap:0.5rem">
      <button class="btn-primary" onClick=${() => setShowAddForm(true)}>+ Add Fuel</button>
      <button class="btn-secondary" onClick=${() => setShowUseForm(true)}>Log Usage</button>
    </div>
    <div class="grid">
      ${summary.map(s => {
        const ds = supply.find(d => d.fuel_type === s.fuel_type);
        const pct = maxQty > 0 ? (s.net_available / maxQty) * 100 : 0;
        return html`
          <div class="card">
            <h3 style="text-transform:capitalize">${s.fuel_type}</h3>
            <div class="fuel-bar">
              <div class="fuel-fill" style="width:${pct}%;background:${fuelColors[s.fuel_type] || 'var(--accent)'}"></div>
            </div>
            <p>${s.net_available} ${s.unit} available</p>
            <p>Stored: ${s.total_stored} · Used: ${s.total_consumed}</p>
            ${ds && ds.days_of_supply >= 0 && html`
              <p style="color:${ds.days_of_supply <= 7 ? 'var(--danger)' : 'var(--success)'}">
                ${ds.days_of_supply} days supply (${ds.avg_daily_consumption} ${s.unit}/day)
              </p>`}
          </div>`;
      })}
    </div>
    ${showAddForm && html`<${FuelAddForm} onClose=${() => { setShowAddForm(false); load(); }} />`}
    ${showUseForm && html`<${FuelUseForm} onClose=${() => { setShowUseForm(false); load(); }} />`}`;
}

function FuelAddForm({ onClose }) {
  const [form, setForm] = useState({
    fuel_type: 'gasoline', quantity: '', unit: 'liters', storage_location: '',
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async () => {
    await api('/api/fuel/storage', { method: 'POST', body: {
      ...form, quantity: parseFloat(form.quantity),
    }});
    onClose();
  };

  return html`<${Modal} title="Add Fuel" onClose=${onClose}>
    <div class="form-group"><label>Fuel Type</label>
      <select value=${form.fuel_type} onChange=${e => set('fuel_type', e.target.value)}>
        ${['gasoline','diesel','propane','firewood','kerosene','ethanol'].map(t =>
          html`<option value=${t}>${t}</option>`)}
      </select></div>
    <div class="form-group"><label>Quantity</label>
      <input type="number" step="0.1" value=${form.quantity} onInput=${e => set('quantity', e.target.value)} /></div>
    <div class="form-group"><label>Unit</label>
      <select value=${form.unit} onChange=${e => set('unit', e.target.value)}>
        ${['liters','gallons','kg','cords'].map(u => html`<option value=${u}>${u}</option>`)}
      </select></div>
    <div class="form-group"><label>Storage Location</label>
      <input value=${form.storage_location} onInput=${e => set('storage_location', e.target.value)} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Save</button>
    </div>
  <//>`;
}

function FuelUseForm({ onClose }) {
  const [form, setForm] = useState({
    fuel_type: 'gasoline', quantity_used: '', unit: 'liters', purpose: '', used_by: '',
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async () => {
    await api('/api/fuel/consumption', { method: 'POST', body: {
      ...form, quantity_used: parseFloat(form.quantity_used),
    }});
    onClose();
  };

  return html`<${Modal} title="Log Fuel Usage" onClose=${onClose}>
    <div class="form-group"><label>Fuel Type</label>
      <select value=${form.fuel_type} onChange=${e => set('fuel_type', e.target.value)}>
        ${['gasoline','diesel','propane','firewood','kerosene','ethanol'].map(t =>
          html`<option value=${t}>${t}</option>`)}
      </select></div>
    <div class="form-group"><label>Quantity Used</label>
      <input type="number" step="0.1" value=${form.quantity_used} onInput=${e => set('quantity_used', e.target.value)} /></div>
    <div class="form-group"><label>Unit</label>
      <select value=${form.unit} onChange=${e => set('unit', e.target.value)}>
        ${['liters','gallons','kg','cords'].map(u => html`<option value=${u}>${u}</option>`)}
      </select></div>
    <div class="form-group"><label>Purpose</label>
      <input value=${form.purpose} onInput=${e => set('purpose', e.target.value)} /></div>
    <div class="form-group"><label>Used By</label>
      <input value=${form.used_by} onInput=${e => set('used_by', e.target.value)} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Save</button>
    </div>
  <//>`;
}

// --- Generators Tab ---

function GeneratorsTab() {
  const [gens, setGens] = useState([]);
  const [maintenanceDue, setMaintenanceDue] = useState([]);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    const g = await api('/api/generators');
    setGens(g);
    setMaintenanceDue(await api('/api/generators/maintenance-due'));
    for (const gen of g) {
      gen._efficiency = await api(`/api/generators/efficiency/${gen.id}`);
    }
    setGens([...g]);
  };

  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t); }, []);

  return html`
    <div style="margin-bottom:1rem">
      <button class="btn-primary" onClick=${() => setShowForm(true)}>+ Add Generator</button>
    </div>
    ${maintenanceDue.length > 0 && html`
      <h3 style="color:var(--warn);margin-bottom:0.5rem">Maintenance Due</h3>
      <table style="margin-bottom:1rem">
        <thead><tr><th>Generator</th><th>Task</th><th>Interval</th><th>Hours Overdue</th></tr></thead>
        <tbody>${maintenanceDue.map(m => html`<tr>
          <td>${m.generator_name}</td><td>${m.task}</td>
          <td>Every ${m.interval_hours}h</td>
          <td style="color:var(--danger)">${m.hours_overdue}h</td>
        </tr>`)}</tbody>
      </table>`}
    <div class="grid">
      ${gens.length === 0 && html`<div class="empty">No generators registered</div>`}
      ${gens.map(g => html`
        <div class="card">
          <h3>${g.name}</h3>
          <p>${g.rated_kw} kW · ${g.fuel_type}</p>
          <p>Location: ${g.location || 'N/A'}</p>
          <p>Total runtime: ${Math.round(g.total_runtime_hours)}h</p>
          ${g._efficiency && html`
            <p>Efficiency: ${g._efficiency.kwh_per_liter} kWh/L</p>`}
        </div>`)}
    </div>
    ${showForm && html`<${GeneratorForm} onClose=${() => { setShowForm(false); load(); }} />`}`;
}

function GeneratorForm({ onClose }) {
  const [form, setForm] = useState({
    name: '', fuel_type: 'gasoline', rated_kw: '', location: '',
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async () => {
    await api('/api/generators', { method: 'POST', body: {
      ...form, rated_kw: parseFloat(form.rated_kw),
    }});
    onClose();
  };

  return html`<${Modal} title="Add Generator" onClose=${onClose}>
    <div class="form-group"><label>Name</label>
      <input value=${form.name} onInput=${e => set('name', e.target.value)} /></div>
    <div class="form-group"><label>Fuel Type</label>
      <select value=${form.fuel_type} onChange=${e => set('fuel_type', e.target.value)}>
        ${['gasoline','diesel','propane','ethanol'].map(t => html`<option value=${t}>${t}</option>`)}
      </select></div>
    <div class="form-group"><label>Rated kW</label>
      <input type="number" step="0.1" value=${form.rated_kw} onInput=${e => set('rated_kw', e.target.value)} /></div>
    <div class="form-group"><label>Location</label>
      <input value=${form.location} onInput=${e => set('location', e.target.value)} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Save</button>
    </div>
  <//>`;
}

// --- Budget Tab ---

function BudgetTab() {
  const [analysis, setAnalysis] = useState(null);
  const [shedding, setShedding] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setAnalysis(await api('/api/budget/analysis'));
    setShedding(await api('/api/budget/load-shedding'));
  };

  useEffect(() => { load(); const t = setInterval(load, 60000); return () => clearInterval(t); }, []);

  return html`
    <div style="margin-bottom:1rem">
      <button class="btn-primary" onClick=${() => setShowForm(true)}>+ Add Load</button>
    </div>
    ${analysis && html`
      <div class="grid" style="margin-bottom:1.5rem">
        <div class="card stat-card">
          <div class="value">${Math.round(analysis.demand.total_wh_per_day)}</div>
          <div class="label">Daily Demand (Wh)</div>
        </div>
        <div class="card stat-card">
          <div class="value">${Math.round(analysis.supply.total_available_wh)}</div>
          <div class="label">Available Supply (Wh)</div>
        </div>
        <div class="card stat-card">
          <div class="value" style="color:${analysis.surplus_wh >= 0 ? 'var(--success)' : 'var(--danger)'}">
            ${analysis.surplus_wh >= 0 ? '+' : ''}${Math.round(analysis.surplus_wh)}
          </div>
          <div class="label"><${Badge} type=${analysis.status} /></div>
        </div>
      </div>
      <h3 style="margin-bottom:0.5rem">Supply Breakdown</h3>
      <div class="grid" style="margin-bottom:1.5rem">
        <div class="card"><p>Solar: ${Math.round(analysis.supply.solar_wh_per_day)} Wh/day</p></div>
        <div class="card"><p>Battery: ${Math.round(analysis.supply.battery_capacity_wh)} Wh capacity</p></div>
        <div class="card"><p>Generator: ${Math.round(analysis.supply.generator_wh_per_day_max)} Wh/day max</p></div>
      </div>
      <h3 style="margin-bottom:0.5rem">Demand by Priority</h3>
      <div class="grid" style="margin-bottom:1.5rem">
        ${Object.entries(analysis.demand.by_priority).map(([p, wh]) => html`
          <div class="card"><p><${Badge} type=${p} /> ${Math.round(wh)} Wh/day</p></div>
        `)}
      </div>`}
    ${analysis && analysis.demand.breakdown.length > 0 && html`
      <h3 style="margin-bottom:0.5rem">Load List</h3>
      <table style="margin-bottom:1.5rem">
        <thead><tr><th>Device</th><th>Watts</th><th>Hours/Day</th><th>Wh/Day</th><th>Priority</th></tr></thead>
        <tbody>${analysis.demand.breakdown.map(l => html`<tr>
          <td>${l.name}</td><td>${l.watts}</td><td>${l.hours_per_day}</td>
          <td>${Math.round(l.wh_per_day)}</td><td><${Badge} type=${l.priority} /></td>
        </tr>`)}</tbody>
      </table>`}
    ${shedding && shedding.needed && html`
      <h3 style="color:var(--danger);margin-bottom:0.5rem">Load Shedding Recommendations</h3>
      <p style="margin-bottom:0.5rem;color:var(--muted)">Deficit: ${shedding.deficit_wh} Wh</p>
      <table>
        <thead><tr><th>Cut</th><th>Priority</th><th>Wh Saved</th></tr></thead>
        <tbody>${shedding.cuts.map(c => html`<tr>
          <td>${c.name}</td><td><${Badge} type=${c.priority} /></td><td>${Math.round(c.wh_saved)}</td>
        </tr>`)}</tbody>
      </table>
      ${!shedding.resolved && html`
        <p style="color:var(--danger);margin-top:0.5rem">
          Cannot fully resolve deficit. ${shedding.remaining_deficit_wh} Wh still needed.
        </p>`}`}
    ${showForm && html`<${LoadForm} onClose=${() => { setShowForm(false); load(); }} />`}`;
}

function LoadForm({ onClose }) {
  const [form, setForm] = useState({
    name: '', watts_draw: '', priority: 'optional', hours_per_day: '',
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async () => {
    await api('/api/budget/loads', { method: 'POST', body: {
      ...form, watts_draw: parseFloat(form.watts_draw), hours_per_day: parseFloat(form.hours_per_day),
    }});
    onClose();
  };

  return html`<${Modal} title="Add Power Load" onClose=${onClose}>
    <div class="form-group"><label>Device/System Name</label>
      <input value=${form.name} onInput=${e => set('name', e.target.value)} /></div>
    <div class="form-group"><label>Watts Draw</label>
      <input type="number" step="0.1" value=${form.watts_draw} onInput=${e => set('watts_draw', e.target.value)} /></div>
    <div class="form-group"><label>Priority</label>
      <select value=${form.priority} onChange=${e => set('priority', e.target.value)}>
        ${['critical','important','optional'].map(p => html`<option value=${p}>${p}</option>`)}
      </select></div>
    <div class="form-group"><label>Hours per Day</label>
      <input type="number" step="0.1" value=${form.hours_per_day} onInput=${e => set('hours_per_day', e.target.value)} /></div>
    <div class="actions">
      <button class="btn-secondary" onClick=${onClose}>Cancel</button>
      <button class="btn-primary" onClick=${submit}>Save</button>
    </div>
  <//>`;
}

// --- App ---

function App() {
  const [tab, setTab] = useState('solar');
  const tabs = [
    ['solar', 'Solar'],
    ['batteries', 'Batteries'],
    ['fuel', 'Fuel'],
    ['generators', 'Generators'],
    ['budget', 'Power Budget'],
  ];

  return html`
    <header>
      <h1>Energy & Fuel Tracking</h1>
      <span style="color:var(--muted);font-size:0.85rem">SURVIVE OS</span>
    </header>
    <div class="tabs">
      ${tabs.map(([id, label]) => html`
        <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
      `)}
    </div>
    <div class="content">
      ${tab === 'solar' && html`<${SolarTab} />`}
      ${tab === 'batteries' && html`<${BatteriesTab} />`}
      ${tab === 'fuel' && html`<${FuelTab} />`}
      ${tab === 'generators' && html`<${GeneratorsTab} />`}
      ${tab === 'budget' && html`<${BudgetTab} />`}
    </div>`;
}

render(html`<${App} />`, document.getElementById('app'));
