import { h, render, Component } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const LAYER_TYPES = ['resource_locations','hazard_zones','agricultural_plots','patrol_routes','trade_routes','mesh_nodes'];
const CATEGORIES = ['water_source','fuel_cache','supply_depot','contamination','structural_collapse','flooding','crop_assignment','patrol_route','checkpoint','trade_route','travel_corridor','meshtastic_node'];

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
function Badge({ type }) {
    return html`<span class="badge badge-${type}">${type.replace(/_/g, ' ')}</span>`;
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

// --- Layers Tab ---
function LayersTab() {
    const [layers, setLayers] = useState([]);
    const [showAdd, setShowAdd] = useState(false);

    const load = useCallback(async () => {
        setLayers(await api('/api/layers'));
    }, []);

    useEffect(() => { load(); }, [load]);

    const toggleVisibility = async (layer) => {
        await api(`/api/layers/${layer.id}`, { method: 'PUT', body: { visible: !layer.visible } });
        load();
    };

    const deleteLayer = async (id) => {
        await api(`/api/layers/${id}`, { method: 'DELETE' });
        load();
    };

    return html`
        <div class="controls">
            <button onClick=${() => setShowAdd(true)}>+ Add Layer</button>
        </div>
        ${layers.length === 0 ? html`<div class="empty">No layers defined</div>` : html`
            <table>
                <thead><tr>
                    <th>Color</th><th>Name</th><th>Type</th><th>Annotations</th><th>Visible</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${layers.map(l => html`<tr key=${l.id}>
                        <td><span class="color-dot" style="background:${l.color}"></span></td>
                        <td>${l.name}</td>
                        <td><${Badge} type=${l.type} /></td>
                        <td>${l.annotation_count || 0}</td>
                        <td style="color:${l.visible ? 'var(--green)' : 'var(--text-dim)'}">${l.visible ? 'ON' : 'OFF'}</td>
                        <td>
                            <button class="secondary" onClick=${() => toggleVisibility(l)}>${l.visible ? 'Hide' : 'Show'}</button>
                            <button class="secondary" style="color:var(--red)" onClick=${() => deleteLayer(l.id)}>Del</button>
                        </td>
                    </tr>`)}
                </tbody>
            </table>
        `}
        ${showAdd && html`<${AddLayerModal} onClose=${() => { setShowAdd(false); load(); }} />`}
    `;
}

function AddLayerModal({ onClose }) {
    const [form, setForm] = useState({ name: '', type: 'resource_locations', color: '#4facfe', description: '' });
    const [err, setErr] = useState('');

    const submit = async () => {
        try {
            await api('/api/layers', { method: 'POST', body: form });
            onClose();
        } catch(e) { setErr(e.message); }
    };

    return html`<${Modal} title="Add Layer" onClose=${onClose}>
        ${err && html`<p style="color:var(--red)">${err}</p>`}
        <div class="form-row"><label>Name</label><input value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} /></div>
        <div class="form-row"><label>Type</label><select value=${form.type} onChange=${e => setForm({...form, type: e.target.value})}>
            ${LAYER_TYPES.map(t => html`<option value=${t}>${t.replace(/_/g,' ')}</option>`)}
        </select></div>
        <div class="form-row"><label>Color</label><input type="color" value=${form.color} onInput=${e => setForm({...form, color: e.target.value})} /></div>
        <div class="form-row"><label>Description</label><input value=${form.description} onInput=${e => setForm({...form, description: e.target.value})} /></div>
        <div class="modal-actions">
            <button class="secondary" onClick=${onClose}>Cancel</button>
            <button onClick=${submit}>Save</button>
        </div>
    <//>`
}

// --- Annotations Tab ---
function AnnotationsTab() {
    const [annotations, setAnnotations] = useState([]);
    const [layers, setLayers] = useState([]);
    const [filterLayer, setFilterLayer] = useState('');
    const [showAdd, setShowAdd] = useState(false);

    const load = useCallback(async () => {
        const params = filterLayer ? `?layer_id=${filterLayer}` : '';
        const [anns, lyrs] = await Promise.all([
            api(`/api/annotations${params}`),
            api('/api/layers'),
        ]);
        setAnnotations(anns);
        setLayers(lyrs);
    }, [filterLayer]);

    useEffect(() => { load(); }, [load]);

    const deleteAnn = async (id) => {
        await api(`/api/annotations/${id}`, { method: 'DELETE' });
        load();
    };

    return html`
        <div class="controls">
            <select value=${filterLayer} onChange=${e => setFilterLayer(e.target.value)}>
                <option value="">All Layers</option>
                ${layers.map(l => html`<option value=${l.id}>${l.name}</option>`)}
            </select>
            <button onClick=${() => setShowAdd(true)}>+ Add Annotation</button>
        </div>
        ${annotations.length === 0 ? html`<div class="empty">No annotations</div>` : html`
            <table>
                <thead><tr>
                    <th>Title</th><th>Category</th><th>Type</th><th>Lat</th><th>Lng</th><th>Creator</th><th>Actions</th>
                </tr></thead>
                <tbody>
                    ${annotations.map(a => html`<tr key=${a.id}>
                        <td>${a.title || '-'}</td>
                        <td>${a.category.replace(/_/g,' ')}</td>
                        <td>${a.geometry?.type || '-'}</td>
                        <td>${a.latitude != null ? a.latitude.toFixed(4) : '-'}</td>
                        <td>${a.longitude != null ? a.longitude.toFixed(4) : '-'}</td>
                        <td>${a.creator || '-'}</td>
                        <td>
                            <button class="secondary" style="color:var(--red)" onClick=${() => deleteAnn(a.id)}>Del</button>
                        </td>
                    </tr>`)}
                </tbody>
            </table>
        `}
        ${showAdd && html`<${AddAnnotationModal} layers=${layers} onClose=${() => { setShowAdd(false); load(); }} />`}
    `;
}

function AddAnnotationModal({ layers, onClose }) {
    const [form, setForm] = useState({
        layer_id: layers[0]?.id || '', category: 'water_source', title: '', description: '',
        creator: '', latitude: '', longitude: '', radius_meters: '',
    });
    const [err, setErr] = useState('');

    const submit = async () => {
        try {
            const lat = form.latitude ? Number(form.latitude) : null;
            const lng = form.longitude ? Number(form.longitude) : null;
            const geometry = lat != null && lng != null
                ? { type: 'Point', coordinates: [lng, lat] }
                : { type: 'Point', coordinates: [0, 0] };
            await api('/api/annotations', { method: 'POST', body: {
                ...form,
                layer_id: Number(form.layer_id),
                geometry,
                latitude: lat,
                longitude: lng,
                radius_meters: form.radius_meters ? Number(form.radius_meters) : null,
            }});
            onClose();
        } catch(e) { setErr(e.message); }
    };

    return html`<${Modal} title="Add Annotation" onClose=${onClose}>
        ${err && html`<p style="color:var(--red)">${err}</p>`}
        <div class="form-row"><label>Layer</label><select value=${form.layer_id} onChange=${e => setForm({...form, layer_id: e.target.value})}>
            ${layers.map(l => html`<option value=${l.id}>${l.name}</option>`)}
        </select></div>
        <div class="form-row"><label>Category</label><select value=${form.category} onChange=${e => setForm({...form, category: e.target.value})}>
            ${CATEGORIES.map(c => html`<option value=${c}>${c.replace(/_/g,' ')}</option>`)}
        </select></div>
        <div class="form-row"><label>Title</label><input value=${form.title} onInput=${e => setForm({...form, title: e.target.value})} /></div>
        <div class="form-row"><label>Description</label><input value=${form.description} onInput=${e => setForm({...form, description: e.target.value})} /></div>
        <div class="form-row"><label>Creator</label><input value=${form.creator} onInput=${e => setForm({...form, creator: e.target.value})} /></div>
        <div class="form-row"><label>Latitude</label><input type="number" step="any" value=${form.latitude} onInput=${e => setForm({...form, latitude: e.target.value})} /></div>
        <div class="form-row"><label>Longitude</label><input type="number" step="any" value=${form.longitude} onInput=${e => setForm({...form, longitude: e.target.value})} /></div>
        <div class="form-row"><label>Radius (m)</label><input type="number" value=${form.radius_meters} onInput=${e => setForm({...form, radius_meters: e.target.value})} /></div>
        <div class="modal-actions">
            <button class="secondary" onClick=${onClose}>Cancel</button>
            <button onClick=${submit}>Save</button>
        </div>
    <//>`
}

// --- App ---
function App() {
    const [tab, setTab] = useState('layers');
    const tabs = [
        ['layers', 'Layers'],
        ['annotations', 'Annotations'],
    ];

    return html`
        <header>
            <h1>SURVIVE // MAP ANNOTATIONS</h1>
        </header>
        <div class="tabs">
            ${tabs.map(([id, label]) => html`
                <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
            `)}
        </div>
        <div class="panel">
            ${tab === 'layers' && html`<${LayersTab} />`}
            ${tab === 'annotations' && html`<${AnnotationsTab} />`}
        </div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
