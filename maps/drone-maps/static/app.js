import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const SURVEY_STATUSES = ['planned', 'in_progress', 'completed'];
const JOB_STATUSES = ['pending', 'processing', 'completed', 'failed'];

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

function Badge({ value }) {
    return html`<span class="badge badge-${value}">${value.replace('_', ' ')}</span>`;
}

function Modal({ title, onClose, children }) {
    return html`<div class="modal-overlay" onClick=${(e) => e.target === e.currentTarget && onClose()}>
        <div class="modal">
            <h3>${title}</h3>
            ${children}
        </div>
    </div>`;
}

// --- Surveys Tab ---
function SurveysTab() {
    const [surveys, setSurveys] = useState([]);
    const [filter, setFilter] = useState({ status: '', area_name: '' });
    const [showAdd, setShowAdd] = useState(false);

    const load = useCallback(async () => {
        const params = new URLSearchParams();
        if (filter.status) params.set('status', filter.status);
        if (filter.area_name) params.set('area_name', filter.area_name);
        setSurveys(await api(`/api/surveys?${params}`));
    }, [filter]);

    useEffect(() => { load(); }, [load]);

    return html`
        <div class="controls">
            <input placeholder="Search area..." value=${filter.area_name}
                onInput=${e => setFilter({...filter, area_name: e.target.value})} />
            <select value=${filter.status} onChange=${e => setFilter({...filter, status: e.target.value})}>
                <option value="">All Statuses</option>
                ${SURVEY_STATUSES.map(s => html`<option value=${s}>${s.replace('_',' ')}</option>`)}
            </select>
            <button onClick=${() => setShowAdd(true)}>+ New Survey</button>
        </div>
        ${surveys.length === 0 ? html`<div class="empty">No surveys found</div>` : html`
            <table>
                <thead><tr>
                    <th>Name</th><th>Area</th><th>Date</th><th>Drone</th>
                    <th>Operator</th><th>Status</th>
                </tr></thead>
                <tbody>
                    ${surveys.map(s => html`<tr key=${s.id}>
                        <td>${s.name}</td>
                        <td>${s.area_name}</td>
                        <td>${s.date}</td>
                        <td>${s.drone_model || '-'}</td>
                        <td>${s.operator || '-'}</td>
                        <td><${Badge} value=${s.status} /></td>
                    </tr>`)}
                </tbody>
            </table>
        `}
        ${showAdd && html`<${AddSurveyModal} onClose=${() => { setShowAdd(false); load(); }} />`}
    `;
}

function AddSurveyModal({ onClose }) {
    const [form, setForm] = useState({ name:'', area_name:'', date:'', drone_model:'', operator:'', notes:'' });
    const [err, setErr] = useState('');

    const submit = async () => {
        try {
            await api('/api/surveys', { method: 'POST', body: form });
            onClose();
        } catch(e) { setErr(e.message); }
    };

    return html`<${Modal} title="New Survey" onClose=${onClose}>
        ${err && html`<p style="color:var(--red)">${err}</p>`}
        <div class="form-row"><label>Name</label><input value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} /></div>
        <div class="form-row"><label>Area</label><input value=${form.area_name} onInput=${e => setForm({...form, area_name: e.target.value})} /></div>
        <div class="form-row"><label>Date</label><input type="date" value=${form.date} onInput=${e => setForm({...form, date: e.target.value})} /></div>
        <div class="form-row"><label>Drone</label><input value=${form.drone_model} onInput=${e => setForm({...form, drone_model: e.target.value})} /></div>
        <div class="form-row"><label>Operator</label><input value=${form.operator} onInput=${e => setForm({...form, operator: e.target.value})} /></div>
        <div class="form-row"><label>Notes</label><input value=${form.notes} onInput=${e => setForm({...form, notes: e.target.value})} /></div>
        <div class="modal-actions">
            <button class="secondary" onClick=${onClose}>Cancel</button>
            <button onClick=${submit}>Create</button>
        </div>
    <//>`
}

// --- Jobs Tab ---
function JobsTab() {
    const [jobs, setJobs] = useState([]);
    const [filter, setFilter] = useState('');

    const load = useCallback(async () => {
        const params = new URLSearchParams();
        if (filter) params.set('status', filter);
        setJobs(await api(`/api/processing?${params}`));
    }, [filter]);

    useEffect(() => { load(); }, [load]);

    const runJob = async (id) => {
        try {
            await api(`/api/processing/${id}/run`, { method: 'POST' });
            load();
        } catch(e) { alert(e.message); }
    };

    return html`
        <div class="controls">
            <select value=${filter} onChange=${e => setFilter(e.target.value)}>
                <option value="">All Statuses</option>
                ${JOB_STATUSES.map(s => html`<option value=${s}>${s}</option>`)}
            </select>
        </div>
        ${jobs.length === 0 ? html`<div class="empty">No processing jobs</div>` : html`
            <table>
                <thead><tr>
                    <th>ID</th><th>Survey</th><th>Status</th><th>Resolution</th>
                    <th>Size</th><th>Created</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${jobs.map(j => html`<tr key=${j.id}>
                        <td>${j.id}</td>
                        <td>${j.survey_id}</td>
                        <td><${Badge} value=${j.status} /></td>
                        <td>${j.resolution ? j.resolution + ' m/px' : '-'}</td>
                        <td>${j.file_size ? (j.file_size / 1048576).toFixed(1) + ' MB' : '-'}</td>
                        <td>${j.created_at}</td>
                        <td>${j.status === 'pending' ? html`<button class="secondary" onClick=${() => runJob(j.id)}>Run</button>` : ''}</td>
                    </tr>`)}
                </tbody>
            </table>
        `}
    `;
}

// --- Changes Tab ---
function ChangesTab() {
    const [changes, setChanges] = useState([]);

    useEffect(async () => {
        setChanges(await api('/api/changes'));
    }, []);

    return html`
        ${changes.length === 0 ? html`<div class="empty">No change detections</div>` : html`
            <table>
                <thead><tr>
                    <th>Survey A</th><th>Survey B</th><th>Type</th>
                    <th>Severity</th><th>Description</th><th>Detected</th>
                </tr></thead>
                <tbody>
                    ${changes.map(c => html`<tr key=${c.id}>
                        <td>${c.survey_a_id}</td>
                        <td>${c.survey_b_id}</td>
                        <td><${Badge} value=${c.change_type} /></td>
                        <td><${Badge} value=${c.severity} /></td>
                        <td>${c.description || '-'}</td>
                        <td>${c.created_at}</td>
                    </tr>`)}
                </tbody>
            </table>
        `}
    `;
}

// --- App ---
function App() {
    const [tab, setTab] = useState('surveys');
    const tabs = [
        ['surveys', 'Surveys'],
        ['jobs', 'Processing'],
        ['changes', 'Changes'],
    ];

    return html`
        <header>
            <h1>SURVIVE // DRONE MAPS</h1>
        </header>
        <div class="tabs">
            ${tabs.map(([id, label]) => html`
                <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
            `)}
        </div>
        <div class="panel">
            ${tab === 'surveys' && html`<${SurveysTab} />`}
            ${tab === 'jobs' && html`<${JobsTab} />`}
            ${tab === 'changes' && html`<${ChangesTab} />`}
        </div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
