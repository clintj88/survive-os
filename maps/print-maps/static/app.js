import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const PAPER_SIZES = ['A4', 'A3', 'letter', 'tabloid', 'custom'];
const ORIENTATIONS = ['portrait', 'landscape'];
const DPI_OPTIONS = [150, 300, 600];
const TEMPLATE_TYPES = ['patrol_map', 'foraging_map', 'trade_route_map', 'general'];

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

function StatusBadge({ status }) {
    return html`<span class="badge badge-${status}">${status}</span>`;
}

function Modal({ title, onClose, children }) {
    return html`<div class="modal-overlay" onClick=${(e) => e.target === e.currentTarget && onClose()}>
        <div class="modal">
            <h3>${title}</h3>
            ${children}
        </div>
    </div>`;
}

// --- Print Jobs Tab ---
function JobsTab() {
    const [jobs, setJobs] = useState([]);
    const [filter, setFilter] = useState('');
    const [showCreate, setShowCreate] = useState(false);

    const load = useCallback(async () => {
        const params = new URLSearchParams();
        if (filter) params.set('status', filter);
        setJobs(await api(`/api/jobs?${params}`));
    }, [filter]);

    useEffect(() => { load(); }, [load]);

    return html`
        <div class="controls">
            <select value=${filter} onChange=${e => setFilter(e.target.value)}>
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="rendering">Rendering</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
            </select>
            <button onClick=${() => setShowCreate(true)}>+ New Print Job</button>
        </div>
        ${jobs.length === 0 ? html`<div class="empty">No print jobs</div>` : html`
            <table>
                <thead><tr>
                    <th>Title</th><th>Center</th><th>Paper</th><th>DPI</th>
                    <th>Status</th><th>Created</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${jobs.map(job => html`<tr key=${job.id}>
                        <td>${job.title || '(untitled)'}</td>
                        <td>${job.center_lat.toFixed(4)}, ${job.center_lng.toFixed(4)}</td>
                        <td>${job.paper_size} ${job.orientation}</td>
                        <td>${job.dpi}</td>
                        <td><${StatusBadge} status=${job.status} /></td>
                        <td style="white-space:nowrap">${job.created_at}</td>
                        <td>
                            ${job.status === 'completed' && html`
                                <a href="/api/jobs/${job.id}/download" style="color:var(--accent)">Download</a>
                            `}
                        </td>
                    </tr>`)}
                </tbody>
            </table>
        `}
        ${showCreate && html`<${CreateJobModal} onClose=${() => { setShowCreate(false); load(); }} />`}
    `;
}

function CreateJobModal({ onClose }) {
    const [form, setForm] = useState({
        title: '', center_lat: 0, center_lng: 0, zoom: 13,
        paper_size: 'A4', orientation: 'portrait', dpi: 300,
        include_legend: true, include_scale_bar: true, include_north_arrow: true,
        include_grid: false, include_date: true,
    });
    const [err, setErr] = useState('');

    const submit = async () => {
        try {
            await api('/api/jobs', { method: 'POST', body: {
                ...form,
                center_lat: Number(form.center_lat),
                center_lng: Number(form.center_lng),
                zoom: Number(form.zoom),
                dpi: Number(form.dpi),
            }});
            onClose();
        } catch(e) { setErr(e.message); }
    };

    return html`<${Modal} title="New Print Job" onClose=${onClose}>
        ${err && html`<p style="color:var(--red)">${err}</p>`}
        <div class="form-row"><label>Title</label><input value=${form.title} onInput=${e => setForm({...form, title: e.target.value})} /></div>
        <div class="form-row"><label>Latitude</label><input type="number" step="any" value=${form.center_lat} onInput=${e => setForm({...form, center_lat: e.target.value})} /></div>
        <div class="form-row"><label>Longitude</label><input type="number" step="any" value=${form.center_lng} onInput=${e => setForm({...form, center_lng: e.target.value})} /></div>
        <div class="form-row"><label>Zoom</label><input type="number" min="1" max="20" value=${form.zoom} onInput=${e => setForm({...form, zoom: e.target.value})} /></div>
        <div class="form-row"><label>Paper Size</label><select value=${form.paper_size} onChange=${e => setForm({...form, paper_size: e.target.value})}>
            ${PAPER_SIZES.map(s => html`<option value=${s}>${s}</option>`)}
        </select></div>
        <div class="form-row"><label>Orientation</label><select value=${form.orientation} onChange=${e => setForm({...form, orientation: e.target.value})}>
            ${ORIENTATIONS.map(o => html`<option value=${o}>${o}</option>`)}
        </select></div>
        <div class="form-row"><label>DPI</label><select value=${form.dpi} onChange=${e => setForm({...form, dpi: Number(e.target.value)})}>
            ${DPI_OPTIONS.map(d => html`<option value=${d}>${d}</option>`)}
        </select></div>
        <div class="checkbox-row">
            <label><input type="checkbox" checked=${form.include_legend} onChange=${e => setForm({...form, include_legend: e.target.checked})} /> Legend</label>
            <label><input type="checkbox" checked=${form.include_scale_bar} onChange=${e => setForm({...form, include_scale_bar: e.target.checked})} /> Scale Bar</label>
            <label><input type="checkbox" checked=${form.include_north_arrow} onChange=${e => setForm({...form, include_north_arrow: e.target.checked})} /> North Arrow</label>
            <label><input type="checkbox" checked=${form.include_grid} onChange=${e => setForm({...form, include_grid: e.target.checked})} /> Grid</label>
            <label><input type="checkbox" checked=${form.include_date} onChange=${e => setForm({...form, include_date: e.target.checked})} /> Date</label>
        </div>
        <div class="modal-actions">
            <button class="secondary" onClick=${onClose}>Cancel</button>
            <button onClick=${submit}>Create Job</button>
        </div>
    <//>`
}

// --- Templates Tab ---
function TemplatesTab() {
    const [templates, setTemplates] = useState([]);
    const [filter, setFilter] = useState('');
    const [showCreate, setShowCreate] = useState(false);

    const load = useCallback(async () => {
        const params = new URLSearchParams();
        if (filter) params.set('template_type', filter);
        setTemplates(await api(`/api/templates?${params}`));
    }, [filter]);

    useEffect(() => { load(); }, [load]);

    return html`
        <div class="controls">
            <select value=${filter} onChange=${e => setFilter(e.target.value)}>
                <option value="">All Types</option>
                ${TEMPLATE_TYPES.map(t => html`<option value=${t}>${t.replace(/_/g, ' ')}</option>`)}
            </select>
            <button onClick=${() => setShowCreate(true)}>+ New Template</button>
        </div>
        ${templates.length === 0 ? html`<div class="empty">No templates</div>` : html`
            <table>
                <thead><tr>
                    <th>Name</th><th>Type</th><th>Paper</th><th>DPI</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${templates.map(t => html`<tr key=${t.id}>
                        <td>${t.name}</td>
                        <td>${t.template_type.replace(/_/g, ' ')}</td>
                        <td>${t.paper_size} ${t.orientation}</td>
                        <td>${t.dpi}</td>
                        <td>
                            <button class="secondary" onClick=${async () => {
                                await api('/api/templates/' + t.id, { method: 'DELETE' });
                                load();
                            }}>Delete</button>
                        </td>
                    </tr>`)}
                </tbody>
            </table>
        `}
        ${showCreate && html`<${CreateTemplateModal} onClose=${() => { setShowCreate(false); load(); }} />`}
    `;
}

function CreateTemplateModal({ onClose }) {
    const [form, setForm] = useState({
        name: '', description: '', template_type: 'general',
        paper_size: 'A4', orientation: 'portrait', dpi: 300,
        include_legend: true, include_scale_bar: true, include_north_arrow: true,
        include_grid: false, include_date: true,
    });
    const [err, setErr] = useState('');

    const submit = async () => {
        try {
            await api('/api/templates', { method: 'POST', body: { ...form, dpi: Number(form.dpi) } });
            onClose();
        } catch(e) { setErr(e.message); }
    };

    return html`<${Modal} title="New Template" onClose=${onClose}>
        ${err && html`<p style="color:var(--red)">${err}</p>`}
        <div class="form-row"><label>Name</label><input value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} /></div>
        <div class="form-row"><label>Description</label><input value=${form.description} onInput=${e => setForm({...form, description: e.target.value})} /></div>
        <div class="form-row"><label>Type</label><select value=${form.template_type} onChange=${e => setForm({...form, template_type: e.target.value})}>
            ${TEMPLATE_TYPES.map(t => html`<option value=${t}>${t.replace(/_/g, ' ')}</option>`)}
        </select></div>
        <div class="form-row"><label>Paper Size</label><select value=${form.paper_size} onChange=${e => setForm({...form, paper_size: e.target.value})}>
            ${PAPER_SIZES.map(s => html`<option value=${s}>${s}</option>`)}
        </select></div>
        <div class="form-row"><label>Orientation</label><select value=${form.orientation} onChange=${e => setForm({...form, orientation: e.target.value})}>
            ${ORIENTATIONS.map(o => html`<option value=${o}>${o}</option>`)}
        </select></div>
        <div class="form-row"><label>DPI</label><select value=${form.dpi} onChange=${e => setForm({...form, dpi: Number(e.target.value)})}>
            ${DPI_OPTIONS.map(d => html`<option value=${d}>${d}</option>`)}
        </select></div>
        <div class="checkbox-row">
            <label><input type="checkbox" checked=${form.include_legend} onChange=${e => setForm({...form, include_legend: e.target.checked})} /> Legend</label>
            <label><input type="checkbox" checked=${form.include_scale_bar} onChange=${e => setForm({...form, include_scale_bar: e.target.checked})} /> Scale Bar</label>
            <label><input type="checkbox" checked=${form.include_north_arrow} onChange=${e => setForm({...form, include_north_arrow: e.target.checked})} /> North Arrow</label>
            <label><input type="checkbox" checked=${form.include_grid} onChange=${e => setForm({...form, include_grid: e.target.checked})} /> Grid</label>
            <label><input type="checkbox" checked=${form.include_date} onChange=${e => setForm({...form, include_date: e.target.checked})} /> Date</label>
        </div>
        <div class="modal-actions">
            <button class="secondary" onClick=${onClose}>Cancel</button>
            <button onClick=${submit}>Save Template</button>
        </div>
    <//>`
}

// --- App ---
function App() {
    const [tab, setTab] = useState('jobs');
    const tabs = [
        ['jobs', 'Print Jobs'],
        ['templates', 'Templates'],
    ];

    return html`
        <header>
            <h1>SURVIVE // PRINT MAPS</h1>
        </header>
        <div class="tabs">
            ${tabs.map(([id, label]) => html`
                <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
            `)}
        </div>
        <div class="panel">
            ${tab === 'jobs' && html`<${JobsTab} />`}
            ${tab === 'templates' && html`<${TemplatesTab} />`}
        </div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
