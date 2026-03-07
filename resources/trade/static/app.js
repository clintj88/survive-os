import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

async function api(url, opts) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// --- Ledger Tab ---
function LedgerTab() {
  const [trades, setTrades] = useState([]);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    party_a: '', party_b: '', description: '',
    giveDesc: '', giveQty: '', giveUnit: '', giveHours: '',
    recvDesc: '', recvQty: '', recvUnit: '', recvHours: '',
  });

  const load = () => api('/api/trades').then(setTrades).catch(e => setError(e.message));
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api('/api/trades', {
        method: 'POST',
        body: JSON.stringify({
          party_a: form.party_a, party_b: form.party_b, description: form.description,
          items: [
            { side: 'give', item_description: form.giveDesc, quantity: +form.giveQty, unit: form.giveUnit, value_in_labor_hours: +form.giveHours },
            { side: 'receive', item_description: form.recvDesc, quantity: +form.recvQty, unit: form.recvUnit, value_in_labor_hours: +form.recvHours },
          ],
        }),
      });
      setShowForm(false);
      setForm({ party_a: '', party_b: '', description: '', giveDesc: '', giveQty: '', giveUnit: '', giveHours: '', recvDesc: '', recvQty: '', recvUnit: '', recvHours: '' });
      load();
    } catch (e) { setError(e.message); }
  };

  const updateStatus = async (id, status) => {
    await api(`/api/trades/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
    load();
  };

  return html`
    <div>
      <div class="tab-header">
        <h2>Trade Ledger</h2>
        <button class="btn-primary" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'New Trade'}</button>
      </div>
      ${error && html`<div class="error">${error}</div>`}
      ${showForm && html`
        <form class="form-card" onSubmit=${submit}>
          <div class="form-row">
            <input placeholder="Party A" value=${form.party_a} onInput=${e => setForm({ ...form, party_a: e.target.value })} required />
            <input placeholder="Party B" value=${form.party_b} onInput=${e => setForm({ ...form, party_b: e.target.value })} required />
          </div>
          <input placeholder="Description" value=${form.description} onInput=${e => setForm({ ...form, description: e.target.value })} style="width:100%" />
          <h4>Give Side (Party A provides)</h4>
          <div class="form-row">
            <input placeholder="Item" value=${form.giveDesc} onInput=${e => setForm({ ...form, giveDesc: e.target.value })} required />
            <input type="number" step="any" placeholder="Qty" value=${form.giveQty} onInput=${e => setForm({ ...form, giveQty: e.target.value })} required />
            <input placeholder="Unit" value=${form.giveUnit} onInput=${e => setForm({ ...form, giveUnit: e.target.value })} required />
            <input type="number" step="any" placeholder="Hours" value=${form.giveHours} onInput=${e => setForm({ ...form, giveHours: e.target.value })} required />
          </div>
          <h4>Receive Side (Party A receives)</h4>
          <div class="form-row">
            <input placeholder="Item" value=${form.recvDesc} onInput=${e => setForm({ ...form, recvDesc: e.target.value })} required />
            <input type="number" step="any" placeholder="Qty" value=${form.recvQty} onInput=${e => setForm({ ...form, recvQty: e.target.value })} required />
            <input placeholder="Unit" value=${form.recvUnit} onInput=${e => setForm({ ...form, recvUnit: e.target.value })} required />
            <input type="number" step="any" placeholder="Hours" value=${form.recvHours} onInput=${e => setForm({ ...form, recvHours: e.target.value })} required />
          </div>
          <button type="submit" class="btn-primary">Record Trade</button>
        </form>
      `}
      <div class="list">
        ${trades.map(t => html`
          <div class="card" key=${t.id}>
            <div class="card-header">
              <strong>${t.party_a}</strong> <span class="arrow">⇄</span> <strong>${t.party_b}</strong>
              <span class="badge badge-${t.status}">${t.status}</span>
            </div>
            <div class="card-desc">${t.description}</div>
            <div class="card-items">
              ${(t.items || []).map(i => html`
                <div class="item ${i.side}">
                  <span class="side-label">${i.side}</span>
                  ${i.quantity} ${i.unit} ${i.item_description} (${i.value_in_labor_hours}h)
                </div>
              `)}
            </div>
            <div class="card-actions">
              ${t.status === 'pending' && html`
                <button class="btn-sm btn-success" onClick=${() => updateStatus(t.id, 'completed')}>Complete</button>
                <button class="btn-sm btn-warn" onClick=${() => updateStatus(t.id, 'disputed')}>Dispute</button>
                <button class="btn-sm btn-danger" onClick=${() => updateStatus(t.id, 'cancelled')}>Cancel</button>
              `}
            </div>
          </div>
        `)}
        ${trades.length === 0 && html`<p class="empty">No trades recorded yet.</p>`}
      </div>
    </div>
  `;
}

// --- Rates Tab ---
function RatesTab() {
  const [rates, setRates] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ commodity_a: '', commodity_b: 'labor_hours', rate: '', set_by: '' });
  const [error, setError] = useState('');

  const load = () => api('/api/rates/current').then(setRates).catch(e => setError(e.message));
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api('/api/rates', {
        method: 'POST',
        body: JSON.stringify({ ...form, rate: +form.rate }),
      });
      setShowForm(false);
      setForm({ commodity_a: '', commodity_b: 'labor_hours', rate: '', set_by: '' });
      load();
    } catch (e) { setError(e.message); }
  };

  return html`
    <div>
      <div class="tab-header">
        <h2>Exchange Rates</h2>
        <button class="btn-primary" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'New Rate'}</button>
      </div>
      ${error && html`<div class="error">${error}</div>`}
      ${showForm && html`
        <form class="form-card" onSubmit=${submit}>
          <div class="form-row">
            <input placeholder="Commodity" value=${form.commodity_a} onInput=${e => setForm({ ...form, commodity_a: e.target.value })} required />
            <span class="arrow">=</span>
            <input type="number" step="any" placeholder="Rate" value=${form.rate} onInput=${e => setForm({ ...form, rate: e.target.value })} required />
            <input placeholder="Base unit" value=${form.commodity_b} onInput=${e => setForm({ ...form, commodity_b: e.target.value })} required />
          </div>
          <input placeholder="Set by" value=${form.set_by} onInput=${e => setForm({ ...form, set_by: e.target.value })} style="width:100%" />
          <button type="submit" class="btn-primary">Save Rate</button>
        </form>
      `}
      <table class="data-table">
        <thead><tr><th>Commodity</th><th>Rate</th><th>Base Unit</th><th>Set By</th><th>Effective</th></tr></thead>
        <tbody>
          ${rates.map(r => html`
            <tr key=${r.id}>
              <td>${r.commodity_a}</td>
              <td>${r.rate}</td>
              <td>${r.commodity_b}</td>
              <td>${r.set_by}</td>
              <td>${r.effective_date}</td>
            </tr>
          `)}
        </tbody>
      </table>
      ${rates.length === 0 && html`<p class="empty">No exchange rates defined.</p>`}
    </div>
  `;
}

// --- History Tab ---
function HistoryTab() {
  const [person, setPerson] = useState('');
  const [history, setHistory] = useState(null);
  const [partyA, setPartyA] = useState('');
  const [partyB, setPartyB] = useState('');
  const [balance, setBalance] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { api('/api/history/summary').then(setSummary).catch(() => {}); }, []);

  const searchHistory = async () => {
    if (!person) return;
    setError('');
    try {
      setHistory(await api(`/api/history/person/${encodeURIComponent(person)}`));
    } catch (e) { setError(e.message); }
  };

  const searchBalance = async () => {
    if (!partyA || !partyB) return;
    setError('');
    try {
      setBalance(await api(`/api/history/balance/${encodeURIComponent(partyA)}/${encodeURIComponent(partyB)}`));
    } catch (e) { setError(e.message); }
  };

  return html`
    <div>
      <h2>Trade History</h2>
      ${error && html`<div class="error">${error}</div>`}

      ${summary && html`
        <div class="stats-row">
          <div class="stat"><span class="stat-val">${summary.total_trades}</span><span class="stat-label">Total</span></div>
          <div class="stat"><span class="stat-val">${summary.completed}</span><span class="stat-label">Completed</span></div>
          <div class="stat"><span class="stat-val">${summary.pending}</span><span class="stat-label">Pending</span></div>
          <div class="stat"><span class="stat-val">${summary.disputed}</span><span class="stat-label">Disputed</span></div>
        </div>
      `}

      <div class="form-card">
        <h4>Person History</h4>
        <div class="form-row">
          <input placeholder="Person name" value=${person} onInput=${e => setPerson(e.target.value)} />
          <button class="btn-primary" onClick=${searchHistory}>Search</button>
        </div>
      </div>
      ${history && html`
        <div class="list">
          ${history.map(t => html`
            <div class="card" key=${t.id}>
              <strong>${t.party_a}</strong> ⇄ <strong>${t.party_b}</strong>
              <span class="badge badge-${t.status}">${t.status}</span>
              <div class="card-desc">${t.description} - ${t.date}</div>
            </div>
          `)}
          ${history.length === 0 && html`<p class="empty">No trades found.</p>`}
        </div>
      `}

      <div class="form-card" style="margin-top:16px">
        <h4>Balance Between Parties</h4>
        <div class="form-row">
          <input placeholder="Party A" value=${partyA} onInput=${e => setPartyA(e.target.value)} />
          <input placeholder="Party B" value=${partyB} onInput=${e => setPartyB(e.target.value)} />
          <button class="btn-primary" onClick=${searchBalance}>Check</button>
        </div>
      </div>
      ${balance && html`
        <div class="balance-card">
          <div>${balance.party_a} gave: <strong>${balance.a_gave_hours}h</strong></div>
          <div>${balance.party_b} gave: <strong>${balance.b_gave_hours}h</strong></div>
          <div class="balance-summary">${balance.summary}</div>
        </div>
      `}
    </div>
  `;
}

// --- Market Tab ---
function MarketTab() {
  const [markets, setMarkets] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ date: '', location: '', organizer: '' });
  const [listingForm, setListingForm] = useState({ person: '', item_description: '', quantity: '', unit: '', asking_price_hours: '', type: 'offer' });
  const [error, setError] = useState('');

  const load = () => api('/api/market').then(setMarkets).catch(e => setError(e.message));
  useEffect(() => { load(); }, []);

  const createMarket = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api('/api/market', { method: 'POST', body: JSON.stringify(form) });
      setShowForm(false);
      setForm({ date: '', location: '', organizer: '' });
      load();
    } catch (e) { setError(e.message); }
  };

  const selectMarket = async (id) => {
    setSelected(await api(`/api/market/${id}`));
  };

  const addListing = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api(`/api/market/${selected.id}/listings`, {
        method: 'POST',
        body: JSON.stringify({ ...listingForm, quantity: +listingForm.quantity, asking_price_hours: +listingForm.asking_price_hours }),
      });
      setListingForm({ person: '', item_description: '', quantity: '', unit: '', asking_price_hours: '', type: 'offer' });
      selectMarket(selected.id);
    } catch (e) { setError(e.message); }
  };

  return html`
    <div>
      <div class="tab-header">
        <h2>Market Days</h2>
        <button class="btn-primary" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'New Market Day'}</button>
      </div>
      ${error && html`<div class="error">${error}</div>`}
      ${showForm && html`
        <form class="form-card" onSubmit=${createMarket}>
          <div class="form-row">
            <input type="date" value=${form.date} onInput=${e => setForm({ ...form, date: e.target.value })} required />
            <input placeholder="Location" value=${form.location} onInput=${e => setForm({ ...form, location: e.target.value })} required />
            <input placeholder="Organizer" value=${form.organizer} onInput=${e => setForm({ ...form, organizer: e.target.value })} required />
          </div>
          <button type="submit" class="btn-primary">Create</button>
        </form>
      `}
      <div class="list">
        ${markets.map(m => html`
          <div class="card clickable" key=${m.id} onClick=${() => selectMarket(m.id)}>
            <strong>${m.date}</strong> - ${m.location}
            <span class="badge badge-${m.status}">${m.status}</span>
            <div class="card-desc">Organized by ${m.organizer}</div>
          </div>
        `)}
      </div>
      ${selected && html`
        <div class="detail-panel">
          <h3>Market: ${selected.date} at ${selected.location}</h3>
          <div class="listings-grid">
            <div>
              <h4>Offers</h4>
              ${(selected.listings || []).filter(l => l.type === 'offer').map(l => html`
                <div class="listing offer">${l.person}: ${l.quantity} ${l.unit} ${l.item_description} (${l.asking_price_hours}h)</div>
              `)}
            </div>
            <div>
              <h4>Wants</h4>
              ${(selected.listings || []).filter(l => l.type === 'want').map(l => html`
                <div class="listing want">${l.person}: ${l.quantity} ${l.unit} ${l.item_description}</div>
              `)}
            </div>
          </div>
          <form class="form-card" onSubmit=${addListing}>
            <h4>Add Listing</h4>
            <div class="form-row">
              <input placeholder="Person" value=${listingForm.person} onInput=${e => setListingForm({ ...listingForm, person: e.target.value })} required />
              <input placeholder="Item" value=${listingForm.item_description} onInput=${e => setListingForm({ ...listingForm, item_description: e.target.value })} required />
              <input type="number" step="any" placeholder="Qty" value=${listingForm.quantity} onInput=${e => setListingForm({ ...listingForm, quantity: e.target.value })} required />
              <input placeholder="Unit" value=${listingForm.unit} onInput=${e => setListingForm({ ...listingForm, unit: e.target.value })} required />
              <input type="number" step="any" placeholder="Price (h)" value=${listingForm.asking_price_hours} onInput=${e => setListingForm({ ...listingForm, asking_price_hours: e.target.value })} />
              <select value=${listingForm.type} onChange=${e => setListingForm({ ...listingForm, type: e.target.value })}>
                <option value="offer">Offer</option>
                <option value="want">Want</option>
              </select>
            </div>
            <button type="submit" class="btn-primary">Add</button>
          </form>
        </div>
      `}
    </div>
  `;
}

// --- Skills Tab ---
function SkillsTab() {
  const [skills, setSkills] = useState([]);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({ person_name: '', skill_category: 'farming', skill_name: '', proficiency: 'beginner', hourly_rate: '1', available: true });
  const [error, setError] = useState('');

  const load = () => api('/api/skills').then(setSkills).catch(e => setError(e.message));
  useEffect(() => {
    load();
    api('/api/skills/categories').then(setCategories).catch(() => {});
  }, []);

  const doSearch = async () => {
    if (!search) { load(); return; }
    try {
      setSkills(await api(`/api/skills/search?q=${encodeURIComponent(search)}`));
    } catch (e) { setError(e.message); }
  };

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api('/api/skills', {
        method: 'POST',
        body: JSON.stringify({ ...form, hourly_rate: +form.hourly_rate }),
      });
      setShowForm(false);
      setForm({ person_name: '', skill_category: 'farming', skill_name: '', proficiency: 'beginner', hourly_rate: '1', available: true });
      load();
    } catch (e) { setError(e.message); }
  };

  return html`
    <div>
      <div class="tab-header">
        <h2>Skills Registry</h2>
        <button class="btn-primary" onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'Register Skill'}</button>
      </div>
      ${error && html`<div class="error">${error}</div>`}
      <div class="form-row" style="margin-bottom:16px">
        <input placeholder="Search skills or people..." value=${search} onInput=${e => setSearch(e.target.value)} onKeyDown=${e => e.key === 'Enter' && doSearch()} />
        <button class="btn-primary" onClick=${doSearch}>Search</button>
      </div>
      ${showForm && html`
        <form class="form-card" onSubmit=${submit}>
          <div class="form-row">
            <input placeholder="Person name" value=${form.person_name} onInput=${e => setForm({ ...form, person_name: e.target.value })} required />
            <select value=${form.skill_category} onChange=${e => setForm({ ...form, skill_category: e.target.value })}>
              ${categories.map(c => html`<option value=${c}>${c}</option>`)}
            </select>
            <input placeholder="Skill name" value=${form.skill_name} onInput=${e => setForm({ ...form, skill_name: e.target.value })} required />
          </div>
          <div class="form-row">
            <select value=${form.proficiency} onChange=${e => setForm({ ...form, proficiency: e.target.value })}>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="expert">Expert</option>
            </select>
            <input type="number" step="any" placeholder="Hourly rate" value=${form.hourly_rate} onInput=${e => setForm({ ...form, hourly_rate: e.target.value })} />
            <label><input type="checkbox" checked=${form.available} onChange=${e => setForm({ ...form, available: e.target.checked })} /> Available</label>
          </div>
          <button type="submit" class="btn-primary">Register</button>
        </form>
      `}
      <div class="list">
        ${skills.map(s => html`
          <div class="card" key=${s.id}>
            <div class="card-header">
              <strong>${s.person_name}</strong>
              <span class="badge badge-${s.skill_category}">${s.skill_category}</span>
              ${s.available ? html`<span class="badge badge-available">Available</span>` : html`<span class="badge badge-unavailable">Unavailable</span>`}
            </div>
            <div>${s.skill_name} - <em>${s.proficiency}</em> - ${s.hourly_rate}h/hr</div>
          </div>
        `)}
        ${skills.length === 0 && html`<p class="empty">No skills registered.</p>`}
      </div>
    </div>
  `;
}

// --- App Shell ---
function App() {
  const [tab, setTab] = useState('ledger');
  const tabs = [
    { id: 'ledger', label: 'Ledger' },
    { id: 'rates', label: 'Rates' },
    { id: 'history', label: 'History' },
    { id: 'market', label: 'Market' },
    { id: 'skills', label: 'Skills' },
  ];

  return html`
    <div class="shell">
      <header>
        <h1>Trade & Barter</h1>
        <nav>
          ${tabs.map(t => html`
            <button key=${t.id} class="tab-btn ${tab === t.id ? 'active' : ''}" onClick=${() => setTab(t.id)}>
              ${t.label}
            </button>
          `)}
        </nav>
      </header>
      <main>
        ${tab === 'ledger' && html`<${LedgerTab} />`}
        ${tab === 'rates' && html`<${RatesTab} />`}
        ${tab === 'history' && html`<${HistoryTab} />`}
        ${tab === 'market' && html`<${MarketTab} />`}
        ${tab === 'skills' && html`<${SkillsTab} />`}
      </main>
    </div>
  `;
}

render(html`<${App} />`, document.getElementById('app'));
