import { h, render, Component } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

async function api(path, opts = {}) {
    const res = await fetch(`/api${path}`, {
        headers: { 'Content-Type': 'application/json', ...opts.headers },
        ...opts,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (res.status === 204) return null;
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// ---- Inventory Tab ----
function InventoryTab() {
    const [lots, setLots] = useState([]);
    const [search, setSearch] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [showLedger, setShowLedger] = useState(null);
    const [ledgerEntries, setLedgerEntries] = useState([]);
    const [alerts, setAlerts] = useState([]);

    const load = useCallback(async () => {
        const params = search ? `?search=${encodeURIComponent(search)}` : '';
        const [lotsData, alertsData] = await Promise.all([
            api(`/inventory/lots${params}`),
            api('/inventory/alerts/low-stock'),
        ]);
        setLots(lotsData);
        setAlerts(alertsData);
    }, [search]);

    useEffect(() => { load(); }, [load]);

    async function handleCreate(e) {
        e.preventDefault();
        const fd = new FormData(e.target);
        const body = Object.fromEntries(fd);
        body.quantity = parseFloat(body.quantity) || 0;
        body.low_stock_threshold = parseFloat(body.low_stock_threshold) || 50;
        body.storage_temp = body.storage_temp ? parseFloat(body.storage_temp) : null;
        body.storage_humidity = body.storage_humidity ? parseFloat(body.storage_humidity) : null;
        await api('/inventory/lots', { method: 'POST', body });
        setShowForm(false);
        load();
    }

    async function openLedger(lotId) {
        const entries = await api(`/inventory/lots/${lotId}/ledger`);
        setLedgerEntries(entries);
        setShowLedger(lotId);
    }

    async function handleLedger(e) {
        e.preventDefault();
        const fd = new FormData(e.target);
        await api(`/inventory/lots/${showLedger}/ledger`, {
            method: 'POST',
            body: { type: fd.get('type'), amount: parseFloat(fd.get('amount')), reason: fd.get('reason') },
        });
        openLedger(showLedger);
        load();
    }

    return html`
        <div>
            ${alerts.length > 0 && html`
                <div class="card" style="border-color: var(--warning)">
                    <h2>Low Stock Alerts</h2>
                    <ul class="alert-list">
                        ${alerts.map(a => html`<li class="alert-item">${a.name} (${a.species}): ${a.quantity} ${a.unit} remaining</li>`)}
                    </ul>
                </div>
            `}
            <div class="search-bar">
                <input type="text" placeholder="Search seeds..." value=${search} onInput=${e => setSearch(e.target.value)} />
                <button class="btn btn-primary" onClick=${() => setShowForm(true)}>+ Add Lot</button>
            </div>
            <div class="card">
                <table>
                    <thead><tr>
                        <th>Name</th><th>Species</th><th>Variety</th><th>Qty</th><th>Source</th><th>Location</th><th>Actions</th>
                    </tr></thead>
                    <tbody>
                        ${lots.length === 0 && html`<tr><td colspan="7" class="empty-state">No seed lots found</td></tr>`}
                        ${lots.map(l => html`
                            <tr>
                                <td>${l.name}</td>
                                <td>${l.species}</td>
                                <td>${l.variety || '-'}</td>
                                <td>${l.quantity} ${l.unit}</td>
                                <td>${l.source || '-'}</td>
                                <td>${l.storage_location || '-'}</td>
                                <td><button class="btn btn-sm btn-primary" onClick=${() => openLedger(l.id)}>Ledger</button></td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>

            ${showForm && html`
                <div class="modal-overlay" onClick=${e => e.target === e.currentTarget && setShowForm(false)}>
                    <div class="modal">
                        <h2>Add Seed Lot</h2>
                        <form onSubmit=${handleCreate}>
                            <div class="form-row">
                                <div class="form-group"><label>Name</label><input name="name" required /></div>
                                <div class="form-group"><label>Species</label><input name="species" required /></div>
                            </div>
                            <div class="form-row">
                                <div class="form-group"><label>Variety</label><input name="variety" /></div>
                                <div class="form-group"><label>Source</label><input name="source" /></div>
                            </div>
                            <div class="form-row">
                                <div class="form-group"><label>Quantity</label><input name="quantity" type="number" step="any" value="0" /></div>
                                <div class="form-group"><label>Unit</label><select name="unit"><option>grams</option><option>count</option><option>kg</option></select></div>
                            </div>
                            <div class="form-row">
                                <div class="form-group"><label>Storage Location</label><input name="storage_location" /></div>
                                <div class="form-group"><label>Date Collected</label><input name="date_collected" type="date" /></div>
                            </div>
                            <div class="form-row">
                                <div class="form-group"><label>Storage Temp (C)</label><input name="storage_temp" type="number" step="any" /></div>
                                <div class="form-group"><label>Storage Humidity (%)</label><input name="storage_humidity" type="number" step="any" /></div>
                            </div>
                            <div class="form-group"><label>Low Stock Threshold</label><input name="low_stock_threshold" type="number" step="any" value="50" /></div>
                            <div class="form-group"><label>Notes</label><textarea name="notes" rows="2"></textarea></div>
                            <div class="modal-actions">
                                <button type="button" class="btn" onClick=${() => setShowForm(false)}>Cancel</button>
                                <button type="submit" class="btn btn-primary">Create</button>
                            </div>
                        </form>
                    </div>
                </div>
            `}

            ${showLedger && html`
                <div class="modal-overlay" onClick=${e => e.target === e.currentTarget && setShowLedger(null)}>
                    <div class="modal">
                        <h2>Ledger</h2>
                        <form onSubmit=${handleLedger} style="margin-bottom: 1rem">
                            <div class="form-row">
                                <div class="form-group"><label>Type</label><select name="type"><option value="deposit">Deposit</option><option value="withdrawal">Withdrawal</option></select></div>
                                <div class="form-group"><label>Amount</label><input name="amount" type="number" step="any" required /></div>
                            </div>
                            <div class="form-group"><label>Reason</label><input name="reason" /></div>
                            <button type="submit" class="btn btn-primary btn-sm">Add Entry</button>
                        </form>
                        <table>
                            <thead><tr><th>Date</th><th>Type</th><th>Amount</th><th>Reason</th></tr></thead>
                            <tbody>
                                ${ledgerEntries.map(e => html`
                                    <tr><td>${e.created_at}</td><td><span class="badge ${e.type === 'deposit' ? 'badge-green' : 'badge-red'}">${e.type}</span></td><td>${e.amount}</td><td>${e.reason}</td></tr>
                                `)}
                            </tbody>
                        </table>
                        <div class="modal-actions"><button class="btn" onClick=${() => setShowLedger(null)}>Close</button></div>
                    </div>
                </div>
            `}
        </div>
    `;
}

// ---- Germination Tab ----
function GerminationTab() {
    const [tests, setTests] = useState([]);
    const [lots, setLots] = useState([]);
    const [reminders, setReminders] = useState([]);
    const [showForm, setShowForm] = useState(false);

    const load = useCallback(async () => {
        const [t, l, r] = await Promise.all([
            api('/germination/tests'),
            api('/inventory/lots'),
            api('/germination/reminders'),
        ]);
        setTests(t);
        setLots(l);
        setReminders(r);
    }, []);

    useEffect(() => { load(); }, [load]);

    async function handleCreate(e) {
        e.preventDefault();
        const fd = new FormData(e.target);
        await api('/germination/tests', {
            method: 'POST',
            body: {
                lot_id: parseInt(fd.get('lot_id')),
                date_tested: fd.get('date_tested'),
                sample_size: parseInt(fd.get('sample_size')),
                germination_count: parseInt(fd.get('germination_count')),
                notes: fd.get('notes'),
            },
        });
        setShowForm(false);
        load();
    }

    return html`
        <div>
            ${reminders.length > 0 && html`
                <div class="card" style="border-color: var(--warning)">
                    <h2>Test Reminders</h2>
                    <ul class="alert-list">
                        ${reminders.map(r => html`<li class="alert-item">${r.name} (${r.species}): ${r.days_since_test} days since last test</li>`)}
                    </ul>
                </div>
            `}
            <div style="display:flex;justify-content:flex-end;margin-bottom:1rem">
                <button class="btn btn-primary" onClick=${() => setShowForm(true)}>+ Record Test</button>
            </div>
            <div class="card">
                <table>
                    <thead><tr><th>Date</th><th>Lot</th><th>Species</th><th>Sample</th><th>Germinated</th><th>Rate</th></tr></thead>
                    <tbody>
                        ${tests.length === 0 && html`<tr><td colspan="6" class="empty-state">No tests recorded</td></tr>`}
                        ${tests.map(t => html`
                            <tr>
                                <td>${t.date_tested}</td>
                                <td>${t.lot_name}</td>
                                <td>${t.species}</td>
                                <td>${t.sample_size}</td>
                                <td>${t.germination_count}</td>
                                <td><span class="badge ${t.germination_rate >= 70 ? 'badge-green' : t.germination_rate >= 40 ? 'badge-yellow' : 'badge-red'}">${t.germination_rate}%</span></td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>

            ${showForm && html`
                <div class="modal-overlay" onClick=${e => e.target === e.currentTarget && setShowForm(false)}>
                    <div class="modal">
                        <h2>Record Germination Test</h2>
                        <form onSubmit=${handleCreate}>
                            <div class="form-group">
                                <label>Seed Lot</label>
                                <select name="lot_id" required>
                                    <option value="">Select lot...</option>
                                    ${lots.map(l => html`<option value=${l.id}>${l.name} (${l.species})</option>`)}
                                </select>
                            </div>
                            <div class="form-group"><label>Date Tested</label><input name="date_tested" type="date" /></div>
                            <div class="form-row">
                                <div class="form-group"><label>Sample Size</label><input name="sample_size" type="number" required /></div>
                                <div class="form-group"><label>Germinated</label><input name="germination_count" type="number" required /></div>
                            </div>
                            <div class="form-group"><label>Notes</label><textarea name="notes" rows="2"></textarea></div>
                            <div class="modal-actions">
                                <button type="button" class="btn" onClick=${() => setShowForm(false)}>Cancel</button>
                                <button type="submit" class="btn btn-primary">Save</button>
                            </div>
                        </form>
                    </div>
                </div>
            `}
        </div>
    `;
}

// ---- Viability Tab ----
function ViabilityTab() {
    const [dashboard, setDashboard] = useState([]);

    useEffect(() => {
        api('/viability/dashboard').then(setDashboard);
    }, []);

    function barColor(status) {
        return status === 'green' ? 'var(--green)' : status === 'yellow' ? 'var(--yellow)' : 'var(--red)';
    }

    return html`
        <div>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">${dashboard.filter(d => d.status === 'green').length}</div>
                    <div class="stat-label">Viable (Green)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${dashboard.filter(d => d.status === 'yellow').length}</div>
                    <div class="stat-label">Aging (Yellow)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${dashboard.filter(d => d.status === 'red').length}</div>
                    <div class="stat-label">Low Viability (Red)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${dashboard.filter(d => d.status === 'unknown').length}</div>
                    <div class="stat-label">Unknown</div>
                </div>
            </div>
            <div class="card">
                <table>
                    <thead><tr><th>Name</th><th>Species</th><th>Age</th><th>Viability</th><th>Status</th><th>Years Left</th></tr></thead>
                    <tbody>
                        ${dashboard.length === 0 && html`<tr><td colspan="6" class="empty-state">No data</td></tr>`}
                        ${dashboard.map(d => html`
                            <tr>
                                <td>${d.name}</td>
                                <td>${d.species}</td>
                                <td>${d.age_years != null ? d.age_years + 'y' : '-'}</td>
                                <td>
                                    ${d.predicted_viability_pct != null ? html`
                                        <div>${d.predicted_viability_pct}%</div>
                                        <div class="viability-bar">
                                            <div class="viability-fill" style="width:${d.predicted_viability_pct}%;background:${barColor(d.status)}"></div>
                                        </div>
                                    ` : '-'}
                                </td>
                                <td><span class="badge badge-${d.status}">${d.status}</span></td>
                                <td>${d.years_remaining != null ? d.years_remaining + 'y' : '-'}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// ---- Diversity Tab ----
function DiversityTab() {
    const [scores, setScores] = useState([]);
    const [alerts, setAlerts] = useState([]);

    useEffect(() => {
        Promise.all([api('/diversity/scores'), api('/diversity/alerts')]).then(([s, a]) => {
            setScores(s);
            setAlerts(a);
        });
    }, []);

    return html`
        <div>
            ${alerts.length > 0 && html`
                <div class="card" style="border-color: var(--danger)">
                    <h2>Diversity Alerts</h2>
                    <ul class="alert-list">
                        ${alerts.map(a => html`<li class="alert-item ${a.status === 'critical' ? 'critical' : ''}">${a.species}: ${a.distinct_sources} source(s) (min ${a.min_sources} recommended)</li>`)}
                    </ul>
                </div>
            `}
            <div class="card">
                <table>
                    <thead><tr><th>Species</th><th>Total Lots</th><th>Sources</th><th>Score</th><th>Status</th><th>Source List</th></tr></thead>
                    <tbody>
                        ${scores.length === 0 && html`<tr><td colspan="6" class="empty-state">No data</td></tr>`}
                        ${scores.map(s => html`
                            <tr>
                                <td>${s.species}</td>
                                <td>${s.total_lots}</td>
                                <td>${s.distinct_sources}</td>
                                <td>${s.diversity_score}%</td>
                                <td><span class="badge badge-${s.status === 'healthy' ? 'green' : s.status === 'warning' ? 'yellow' : 'red'}">${s.status}</span></td>
                                <td style="font-size:0.8rem">${s.sources}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// ---- Exchange Tab ----
function ExchangeTab() {
    const [listings, setListings] = useState([]);
    const [showForm, setShowForm] = useState(false);

    const load = useCallback(async () => {
        setListings(await api('/exchange/listings'));
    }, []);

    useEffect(() => { load(); }, [load]);

    async function handleCreate(e) {
        e.preventDefault();
        const fd = new FormData(e.target);
        await api('/exchange/listings', {
            method: 'POST',
            body: {
                type: fd.get('type'),
                species: fd.get('species'),
                variety: fd.get('variety'),
                quantity_available: parseFloat(fd.get('quantity_available')) || 0,
                unit: fd.get('unit'),
                description: fd.get('description'),
                contact: fd.get('contact'),
                community: fd.get('community') || 'local',
            },
        });
        setShowForm(false);
        load();
    }

    return html`
        <div>
            <div style="display:flex;justify-content:flex-end;margin-bottom:1rem">
                <button class="btn btn-primary" onClick=${() => setShowForm(true)}>+ New Listing</button>
            </div>
            <div class="card">
                <table>
                    <thead><tr><th>Type</th><th>Species</th><th>Variety</th><th>Qty</th><th>Community</th><th>Contact</th><th>Description</th></tr></thead>
                    <tbody>
                        ${listings.length === 0 && html`<tr><td colspan="7" class="empty-state">No listings</td></tr>`}
                        ${listings.map(l => html`
                            <tr>
                                <td><span class="badge ${l.type === 'offer' ? 'badge-green' : 'badge-info'}">${l.type}</span></td>
                                <td>${l.species}</td>
                                <td>${l.variety || '-'}</td>
                                <td>${l.quantity_available} ${l.unit}</td>
                                <td>${l.community}</td>
                                <td>${l.contact || '-'}</td>
                                <td>${l.description || '-'}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>

            ${showForm && html`
                <div class="modal-overlay" onClick=${e => e.target === e.currentTarget && setShowForm(false)}>
                    <div class="modal">
                        <h2>New Exchange Listing</h2>
                        <form onSubmit=${handleCreate}>
                            <div class="form-row">
                                <div class="form-group"><label>Type</label><select name="type"><option value="offer">Offer</option><option value="request">Request</option></select></div>
                                <div class="form-group"><label>Species</label><input name="species" required /></div>
                            </div>
                            <div class="form-row">
                                <div class="form-group"><label>Variety</label><input name="variety" /></div>
                                <div class="form-group"><label>Community</label><input name="community" value="local" /></div>
                            </div>
                            <div class="form-row">
                                <div class="form-group"><label>Quantity</label><input name="quantity_available" type="number" step="any" /></div>
                                <div class="form-group"><label>Unit</label><select name="unit"><option>grams</option><option>count</option><option>kg</option></select></div>
                            </div>
                            <div class="form-group"><label>Contact</label><input name="contact" /></div>
                            <div class="form-group"><label>Description</label><textarea name="description" rows="2"></textarea></div>
                            <div class="modal-actions">
                                <button type="button" class="btn" onClick=${() => setShowForm(false)}>Cancel</button>
                                <button type="submit" class="btn btn-primary">Create</button>
                            </div>
                        </form>
                    </div>
                </div>
            `}
        </div>
    `;
}

// ---- Main App ----
function App() {
    const [tab, setTab] = useState('inventory');
    const tabs = [
        ['inventory', 'Inventory'],
        ['germination', 'Germination'],
        ['viability', 'Viability'],
        ['diversity', 'Diversity'],
        ['exchange', 'Exchange'],
    ];

    return html`
        <h1>Seed Bank</h1>
        <div class="tabs">
            ${tabs.map(([id, label]) => html`
                <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
            `)}
        </div>
        ${tab === 'inventory' && html`<${InventoryTab} />`}
        ${tab === 'germination' && html`<${GerminationTab} />`}
        ${tab === 'viability' && html`<${ViabilityTab} />`}
        ${tab === 'diversity' && html`<${DiversityTab} />`}
        ${tab === 'exchange' && html`<${ExchangeTab} />`}
    `;
}

render(html`<${App} />`, document.getElementById('app'));
