import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

async function api(path, opts = {}) {
    const res = await fetch(`/api${path}`, {
        headers: { 'Content-Type': 'application/json', ...opts.headers },
        ...opts,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
}

function App() {
    const [view, setView] = useState('dashboard');

    return html`
        <header>
            <h1>SURVIVE OS // Emergency Alerts</h1>
            <nav>
                <a href="#" onClick=${() => setView('dashboard')}>Dashboard</a>
                <a href="#" onClick=${() => setView('create')}>Create Alert</a>
                <a href="#" onClick=${() => setView('history')}>History</a>
            </nav>
        </header>
        <div class="container">
            ${view === 'dashboard' && html`<${Dashboard} />`}
            ${view === 'create' && html`<${CreateAlert} onCreated=${() => setView('dashboard')} />`}
            ${view === 'history' && html`<${AlertHistory} />`}
        </div>
    `;
}

function Dashboard() {
    const [alerts, setAlerts] = useState([]);
    const load = () => api('/alerts?active=true').then(setAlerts);
    useEffect(() => { load(); }, []);

    const counts = { emergency: 0, critical: 0, warning: 0, info: 0 };
    alerts.forEach(a => { if (counts[a.severity] !== undefined) counts[a.severity]++; });

    const ack = async (id, userId) => {
        try { await api(`/alerts/${id}/ack`, { method: 'POST', body: { user_id: userId } }); }
        catch(e) { /* already acked */ }
        load();
    };

    const resolve = async (id, user) => {
        await api(`/alerts/${id}/resolve`, { method: 'POST', body: { resolved_by: user } });
        load();
    };

    return html`
        <h2>Active Alerts</h2>
        <div class="stats">
            <div class="stat-card"><div class="value" style="color:var(--emergency)">${counts.emergency}</div><div class="label">Emergency</div></div>
            <div class="stat-card"><div class="value" style="color:var(--danger)">${counts.critical}</div><div class="label">Critical</div></div>
            <div class="stat-card"><div class="value" style="color:var(--warning)">${counts.warning}</div><div class="label">Warning</div></div>
            <div class="stat-card"><div class="value" style="color:var(--info)">${counts.info}</div><div class="label">Info</div></div>
        </div>
        <${AlertList} alerts=${alerts} onAck=${ack} onResolve=${resolve} showActions=${true} />
        ${alerts.length === 0 && html`<p style="color:var(--text-muted);padding:1rem">No active alerts.</p>`}
    `;
}

function AlertList({ alerts, onAck, onResolve, showActions }) {
    return html`
        <ul class="alert-list">
            ${alerts.map(a => html`
                <li class="alert-item severity-${a.severity} ${a.active ? '' : 'resolved'}">
                    <div class="alert-header">
                        <span class="alert-title">${a.title}</span>
                        <span class="severity-badge ${a.severity}">${a.severity}</span>
                    </div>
                    <div class="alert-meta">by ${a.author} | ${new Date(a.created_at).toLocaleString()} | ${a.ack_count || 0} ack(s)</div>
                    <div class="alert-body">${a.message}</div>
                    ${showActions && a.active && html`
                        <div class="alert-actions">
                            <button class="btn btn-sm" onClick=${() => { const u = prompt('Your user ID:'); if (u) onAck(a.id, u); }}>Acknowledge</button>
                            <button class="btn btn-sm btn-success" onClick=${() => { const u = prompt('Resolved by:'); if (u) onResolve(a.id, u); }}>Resolve</button>
                        </div>
                    `}
                    ${!a.active && html`<div class="alert-meta">Resolved by ${a.resolved_by} at ${new Date(a.resolved_at).toLocaleString()}</div>`}
                </li>
            `)}
        </ul>
    `;
}

function CreateAlert({ onCreated }) {
    const [title, setTitle] = useState('');
    const [message, setMessage] = useState('');
    const [severity, setSeverity] = useState('warning');
    const [author, setAuthor] = useState('');
    const [error, setError] = useState('');

    const submit = async () => {
        if (!title || !message || !author) { setError('All fields required'); return; }
        try {
            await api('/alerts', { method: 'POST', body: { title, message, severity, author } });
            onCreated();
        } catch (e) { setError(e.message); }
    };

    return html`
        <h2>Create Alert</h2>
        ${error && html`<p style="color:var(--danger);margin-bottom:0.5rem">${error}</p>`}
        <div style="background:var(--surface);border:1px solid var(--border);padding:1rem;border-radius:4px">
            <div class="form-group"><label>Author</label><input value=${author} onInput=${e => setAuthor(e.target.value)} placeholder="Your user ID" /></div>
            <div class="form-group"><label>Severity</label>
                <select value=${severity} onChange=${e => setSeverity(e.target.value)}>
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="critical">Critical</option>
                    <option value="emergency">Emergency</option>
                </select>
            </div>
            <div class="form-group"><label>Title</label><input value=${title} onInput=${e => setTitle(e.target.value)} placeholder="Alert title" /></div>
            <div class="form-group"><label>Message</label><textarea value=${message} onInput=${e => setMessage(e.target.value)} placeholder="Alert details..." /></div>
            <button class="btn btn-danger" onClick=${submit}>Broadcast Alert</button>
        </div>
    `;
}

function AlertHistory() {
    const [alerts, setAlerts] = useState([]);
    useEffect(() => { api('/alerts').then(setAlerts); }, []);

    return html`
        <h2>Alert History</h2>
        <${AlertList} alerts=${alerts} showActions=${false} />
        ${alerts.length === 0 && html`<p style="color:var(--text-muted);padding:1rem">No alerts yet.</p>`}
    `;
}

render(html`<${App} />`, document.getElementById('app'));
