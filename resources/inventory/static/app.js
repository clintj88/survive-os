import { h, render, Component } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const CATEGORIES = ['food','water','medical','tools','fuel','ammunition','building_materials','trade_goods'];
const CONDITIONS = ['new','good','fair','poor'];
const LOCATION_TYPES = ['warehouse','cache','vehicle','building'];

async function api(path, opts = {}) {
    const resp = await fetch(path, {
        headers: { 'Content-Type': 'application/json', ...opts.headers },
        ...opts,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    if (resp.headers.get('content-type')?.includes('json')) return resp.json();
    return resp;
}

// --- Badge component ---
function Badge({ category }) {
    return html`<span class="badge badge-${category}">${category.replace('_', ' ')}</span>`;
}

// --- Quantity bar ---
function QtyBar({ quantity, maxQty }) {
    const pct = maxQty > 0 ? Math.min(100, (quantity / maxQty) * 100) : 0;
    const color = pct > 50 ? 'var(--green)' : pct > 20 ? 'var(--yellow)' : 'var(--red)';
    return html`<span class="qty-bar"><span class="qty-fill" style="width:${pct}%;background:${color}"></span></span>`;
}

// --- Modal ---
function Modal({ title, onClose, children }) {
    return html`<div class="modal-overlay" onClick=${(e) => e.target === e.currentTarget && onClose()}>
        <div class="modal">
            <h3>${title}</h3>
            ${children}
        </div>
    </div>`;
}

// --- Inventory Tab ---
function InventoryTab() {
    const [items, setItems] = useState([]);
    const [filter, setFilter] = useState({ category: '', name: '' });
    const [showAdd, setShowAdd] = useState(false);
    const [qrItem, setQrItem] = useState(null);

    const load = useCallback(async () => {
        const params = new URLSearchParams();
        if (filter.category) params.set('category', filter.category);
        if (filter.name) params.set('name', filter.name);
        setItems(await api(`/api/items?${params}`));
    }, [filter]);

    useEffect(() => { load(); }, [load]);

    const maxQty = Math.max(...items.map(i => i.quantity), 1);

    return html`
        <div class="controls">
            <input placeholder="Search items..." value=${filter.name}
                onInput=${e => setFilter({...filter, name: e.target.value})} />
            <select value=${filter.category} onChange=${e => setFilter({...filter, category: e.target.value})}>
                <option value="">All Categories</option>
                ${CATEGORIES.map(c => html`<option value=${c}>${c.replace('_',' ')}</option>`)}
            </select>
            <button onClick=${() => setShowAdd(true)}>+ Add Item</button>
        </div>
        ${items.length === 0 ? html`<div class="empty">No items found</div>` : html`
            <table>
                <thead><tr>
                    <th>Name</th><th>Category</th><th>Qty</th><th>Unit</th>
                    <th>Condition</th><th>Location</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${items.map(item => html`<tr key=${item.id}>
                        <td>${item.name}</td>
                        <td><${Badge} category=${item.category} /></td>
                        <td>${item.quantity} <${QtyBar} quantity=${item.quantity} maxQty=${maxQty} /></td>
                        <td>${item.unit}</td>
                        <td>${item.condition}</td>
                        <td>${item.location_name || '-'}</td>
                        <td>
                            <button class="secondary" onClick=${() => setQrItem(item)}>QR</button>
                        </td>
                    </tr>`)}
                </tbody>
            </table>
        `}
        ${showAdd && html`<${AddItemModal} onClose=${() => { setShowAdd(false); load(); }} />`}
        ${qrItem && html`<${Modal} title="QR Code - ${qrItem.name}" onClose=${() => setQrItem(null)}>
            <div class="qr-container">
                <img src="/api/scanning/qr/${qrItem.id}" alt="QR Code" width="200" />
                <p style="margin-top:0.5rem;color:var(--text-dim)">${qrItem.qr_code}</p>
            </div>
        <//>`}
    `;
}

function AddItemModal({ onClose }) {
    const [form, setForm] = useState({ name:'', category:'food', subcategory:'', quantity:0, unit:'count', condition:'good', notes:'' });
    const [err, setErr] = useState('');

    const submit = async () => {
        try {
            await api('/api/items', { method: 'POST', body: { ...form, quantity: Number(form.quantity) } });
            onClose();
        } catch(e) { setErr(e.message); }
    };

    return html`<${Modal} title="Add Item" onClose=${onClose}>
        ${err && html`<p style="color:var(--red)">${err}</p>`}
        <div class="form-row"><label>Name</label><input value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} /></div>
        <div class="form-row"><label>Category</label><select value=${form.category} onChange=${e => setForm({...form, category: e.target.value})}>
            ${CATEGORIES.map(c => html`<option value=${c}>${c.replace('_',' ')}</option>`)}
        </select></div>
        <div class="form-row"><label>Quantity</label><input type="number" value=${form.quantity} onInput=${e => setForm({...form, quantity: e.target.value})} /></div>
        <div class="form-row"><label>Unit</label><input value=${form.unit} onInput=${e => setForm({...form, unit: e.target.value})} /></div>
        <div class="form-row"><label>Condition</label><select value=${form.condition} onChange=${e => setForm({...form, condition: e.target.value})}>
            ${CONDITIONS.map(c => html`<option value=${c}>${c}</option>`)}
        </select></div>
        <div class="form-row"><label>Notes</label><input value=${form.notes} onInput=${e => setForm({...form, notes: e.target.value})} /></div>
        <div class="modal-actions">
            <button class="secondary" onClick=${onClose}>Cancel</button>
            <button onClick=${submit}>Save</button>
        </div>
    <//>`
}

// --- Consumption Tab ---
function ConsumptionTab() {
    const [itemId, setItemId] = useState('');
    const [rate, setRate] = useState(null);
    const [history, setHistory] = useState([]);

    const lookup = async () => {
        if (!itemId) return;
        try {
            const [r, h] = await Promise.all([
                api(`/api/consumption/rate/${itemId}`),
                api(`/api/consumption/history/${itemId}`),
            ]);
            setRate(r);
            setHistory(h);
        } catch(e) { setRate(null); setHistory([]); }
    };

    return html`
        <div class="controls">
            <input placeholder="Item ID" type="number" value=${itemId} onInput=${e => setItemId(e.target.value)} />
            <button onClick=${lookup}>Lookup</button>
        </div>
        ${rate && html`
            <div class="stat-cards">
                <div class="stat-card"><div class="label">Current Stock</div><div class="value">${rate.current_quantity} ${rate.unit}</div></div>
                <div class="stat-card"><div class="label">Daily Rate</div><div class="value">${rate.daily_rate} / day</div></div>
                <div class="stat-card"><div class="label">Weekly Rate</div><div class="value">${rate.weekly_rate} / week</div></div>
                <div class="stat-card"><div class="label">Days of Supply</div><div class="value" style="color:${rate.days_of_supply !== null && rate.days_of_supply < 14 ? 'var(--red)' : 'var(--green)'}">${rate.days_of_supply !== null ? rate.days_of_supply : 'N/A'}</div></div>
            </div>
        `}
        ${history.length > 0 && html`
            <table>
                <thead><tr><th>Date</th><th>Qty</th><th>By</th><th>Purpose</th></tr></thead>
                <tbody>${history.map(e => html`<tr>
                    <td>${e.date}</td><td>${e.quantity_consumed}</td>
                    <td>${e.consumed_by || '-'}</td><td>${e.purpose || '-'}</td>
                </tr>`)}</tbody>
            </table>
        `}
    `;
}

// --- Locations Tab ---
function LocationsTab() {
    const [locations, setLocations] = useState([]);

    useEffect(async () => {
        setLocations(await api('/api/locations'));
    }, []);

    return html`
        ${locations.length === 0 ? html`<div class="empty">No locations</div>` : html`
            <div class="stat-cards">
                ${locations.map(loc => html`
                    <div class="stat-card" key=${loc.id}>
                        <div class="label">${loc.type}</div>
                        <div class="value" style="font-size:1rem">${loc.name}</div>
                        <div style="margin-top:0.5rem;font-size:0.8rem;color:var(--text-dim)">
                            ${loc.item_count} items / ${loc.total_quantity} total
                        </div>
                    </div>
                `)}
            </div>
        `}
    `;
}

// --- Alerts Tab ---
function AlertsTab() {
    const [alerts, setAlerts] = useState([]);

    useEffect(async () => {
        setAlerts(await api('/api/alerts'));
    }, []);

    return html`
        ${alerts.length === 0 ? html`<div class="empty">No active alerts</div>` : html`
            <table>
                <thead><tr><th>Item</th><th>Category</th><th>Quantity</th><th>Min Level</th><th>Status</th></tr></thead>
                <tbody>
                    ${alerts.map(a => html`<tr key=${a.item_id}>
                        <td>${a.item_name}</td>
                        <td><${Badge} category=${a.category} /></td>
                        <td>${a.quantity} ${a.unit}</td>
                        <td>${a.min_level}</td>
                        <td class="alert-${a.alert_level}">${a.alert_level.toUpperCase()}</td>
                    </tr>`)}
                </tbody>
            </table>
        `}
    `;
}

// --- Audit Tab ---
function AuditTab() {
    const [entries, setEntries] = useState([]);
    const [filterBy, setFilterBy] = useState('');

    const load = useCallback(async () => {
        const params = new URLSearchParams();
        if (filterBy) params.set('performed_by', filterBy);
        setEntries(await api(`/api/audit?${params}`));
    }, [filterBy]);

    useEffect(() => { load(); }, [load]);

    return html`
        <div class="controls">
            <input placeholder="Filter by user..." value=${filterBy}
                onInput=${e => setFilterBy(e.target.value)} />
        </div>
        ${entries.length === 0 ? html`<div class="empty">No audit entries</div>` : html`
            <table>
                <thead><tr><th>Time</th><th>Item</th><th>Action</th><th>Change</th><th>By</th><th>Notes</th></tr></thead>
                <tbody>
                    ${entries.map(e => html`<tr key=${e.id}>
                        <td style="white-space:nowrap">${e.timestamp}</td>
                        <td>${e.item_name || '-'}</td>
                        <td>${e.action}</td>
                        <td>${e.quantity_change != null ? (e.quantity_change > 0 ? '+' : '') + e.quantity_change : '-'}</td>
                        <td>${e.performed_by || '-'}</td>
                        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis">${e.notes}</td>
                    </tr>`)}
                </tbody>
            </table>
        `}
    `;
}

// --- App ---
function App() {
    const [tab, setTab] = useState('inventory');
    const tabs = [
        ['inventory', 'Inventory'],
        ['consumption', 'Consumption'],
        ['locations', 'Locations'],
        ['alerts', 'Alerts'],
        ['audit', 'Audit'],
    ];

    return html`
        <header>
            <h1>SURVIVE // INVENTORY</h1>
        </header>
        <div class="tabs">
            ${tabs.map(([id, label]) => html`
                <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
            `)}
        </div>
        <div class="panel">
            ${tab === 'inventory' && html`<${InventoryTab} />`}
            ${tab === 'consumption' && html`<${ConsumptionTab} />`}
            ${tab === 'locations' && html`<${LocationsTab} />`}
            ${tab === 'alerts' && html`<${AlertsTab} />`}
            ${tab === 'audit' && html`<${AuditTab} />`}
        </div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
