import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const FORMATS = ['pbf', 'png', 'jpg', 'webp'];

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

function Badge({ format }) {
    return html`<span class="badge badge-${format}">${format}</span>`;
}

function Modal({ title, onClose, children }) {
    return html`<div class="modal-overlay" onClick=${(e) => e.target === e.currentTarget && onClose()}>
        <div class="modal">
            <h3>${title}</h3>
            ${children}
        </div>
    </div>`;
}

// --- Tilesets Tab ---
function TilesetsTab() {
    const [tilesets, setTilesets] = useState([]);
    const [showAdd, setShowAdd] = useState(false);
    const [selected, setSelected] = useState(null);

    const load = useCallback(async () => {
        setTilesets(await api('/api/tilesets'));
    }, []);

    useEffect(() => { load(); }, [load]);

    const remove = async (id) => {
        await api(`/api/tilesets/${id}`, { method: 'DELETE' });
        load();
    };

    return html`
        <div class="controls">
            <button onClick=${() => setShowAdd(true)}>+ Register Tileset</button>
        </div>
        ${tilesets.length === 0 ? html`<div class="empty">No tilesets registered. Add an MBTiles file to get started.</div>` : html`
            <table>
                <thead><tr>
                    <th>Name</th><th>Format</th><th>Zoom</th><th>Description</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${tilesets.map(ts => html`<tr key=${ts.id}>
                        <td>${ts.name}</td>
                        <td><${Badge} format=${ts.format} /></td>
                        <td>${ts.min_zoom} - ${ts.max_zoom}</td>
                        <td>${ts.description || '-'}</td>
                        <td>
                            <button class="secondary" onClick=${() => setSelected(ts)}>Preview</button>
                            <button class="secondary" style="margin-left:0.25rem;color:var(--red)" onClick=${() => remove(ts.id)}>Delete</button>
                        </td>
                    </tr>`)}
                </tbody>
            </table>
        `}
        ${showAdd && html`<${AddTilesetModal} onClose=${() => { setShowAdd(false); load(); }} />`}
        ${selected && html`<${Modal} title="Preview - ${selected.name}" onClose=${() => setSelected(null)}>
            <div class="stat-cards">
                <div class="stat-card"><div class="label">Format</div><div class="value" style="font-size:1rem">${selected.format}</div></div>
                <div class="stat-card"><div class="label">Zoom Range</div><div class="value" style="font-size:1rem">${selected.min_zoom} - ${selected.max_zoom}</div></div>
                <div class="stat-card"><div class="label">Center</div><div class="value" style="font-size:0.8rem">${selected.center_lat}, ${selected.center_lng}</div></div>
            </div>
            <div class="map-preview">
                <span>Map preview requires MapLibre GL JS</span>
            </div>
            <div style="margin-top:0.5rem;font-size:0.8rem;color:var(--text-dim)">
                TileJSON: <a href="/api/tilesets/${selected.id}/tilejson" style="color:var(--accent)">/api/tilesets/${selected.id}/tilejson</a>
            </div>
        <//>`}
    `;
}

function AddTilesetModal({ onClose }) {
    const [form, setForm] = useState({ name: '', filepath: '', format: 'pbf', description: '', min_zoom: 0, max_zoom: 14, bounds: '-180,-85.0511,180,85.0511', center_lat: 0, center_lng: 0, center_zoom: 2 });
    const [err, setErr] = useState('');

    const submit = async () => {
        try {
            await api('/api/tilesets', { method: 'POST', body: { ...form, min_zoom: Number(form.min_zoom), max_zoom: Number(form.max_zoom), center_lat: Number(form.center_lat), center_lng: Number(form.center_lng), center_zoom: Number(form.center_zoom) } });
            onClose();
        } catch(e) { setErr(e.message); }
    };

    return html`<${Modal} title="Register Tileset" onClose=${onClose}>
        ${err && html`<p style="color:var(--red)">${err}</p>`}
        <div class="form-row"><label>Name</label><input value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} /></div>
        <div class="form-row"><label>File Path</label><input value=${form.filepath} onInput=${e => setForm({...form, filepath: e.target.value})} placeholder="/var/lib/survive/tile-server/mbtiles/region.mbtiles" /></div>
        <div class="form-row"><label>Format</label><select value=${form.format} onChange=${e => setForm({...form, format: e.target.value})}>
            ${FORMATS.map(f => html`<option value=${f}>${f}</option>`)}
        </select></div>
        <div class="form-row"><label>Description</label><input value=${form.description} onInput=${e => setForm({...form, description: e.target.value})} /></div>
        <div class="form-row"><label>Min Zoom</label><input type="number" value=${form.min_zoom} onInput=${e => setForm({...form, min_zoom: e.target.value})} /></div>
        <div class="form-row"><label>Max Zoom</label><input type="number" value=${form.max_zoom} onInput=${e => setForm({...form, max_zoom: e.target.value})} /></div>
        <div class="modal-actions">
            <button class="secondary" onClick=${onClose}>Cancel</button>
            <button onClick=${submit}>Register</button>
        </div>
    <//>`
}

// --- Styles Tab ---
function StylesTab() {
    const [styles, setStyles] = useState([]);

    useEffect(async () => {
        setStyles(await api('/api/styles'));
    }, []);

    return html`
        ${styles.length === 0 ? html`<div class="empty">No styles available. Register a tileset first.</div>` : html`
            <table>
                <thead><tr><th>Name</th><th>Style URL</th></tr></thead>
                <tbody>
                    ${styles.map(s => html`<tr key=${s.id}>
                        <td>${s.name}</td>
                        <td><a href=${s.url} style="color:var(--accent)">${s.url}</a></td>
                    </tr>`)}
                </tbody>
            </table>
        `}
    `;
}

// --- App ---
function App() {
    const [tab, setTab] = useState('tilesets');
    const tabs = [
        ['tilesets', 'Tilesets'],
        ['styles', 'Styles'],
    ];

    return html`
        <header>
            <h1>SURVIVE // MAP TILES</h1>
        </header>
        <div class="tabs">
            ${tabs.map(([id, label]) => html`
                <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
            `)}
        </div>
        <div class="panel">
            ${tab === 'tilesets' && html`<${TilesetsTab} />`}
            ${tab === 'styles' && html`<${StylesTab} />`}
        </div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
