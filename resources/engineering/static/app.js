import { h, render } from 'https://esm.sh/preact';
import { useState, useEffect } from 'https://esm.sh/preact/hooks';
import htm from 'https://esm.sh/htm';

const html = htm.bind(h);

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

async function postJSON(url, data) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// --- Condition Badge ---
function ConditionBadge({ condition }) {
    const cls = `badge badge-${condition}`;
    return html`<span class=${cls}>${condition}</span>`;
}

function DifficultyBadge({ difficulty }) {
    const cls = `badge badge-diff-${difficulty}`;
    return html`<span class=${cls}>${difficulty}</span>`;
}

// --- Maintenance Tab ---
function MaintenanceTab() {
    const [items, setItems] = useState([]);
    const [overdue, setOverdue] = useState([]);
    const [schedules, setSchedules] = useState([]);
    const [selectedItem, setSelectedItem] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState({ name: '', category: 'equipment', location: '', condition: 'good', notes: '' });

    const load = async () => {
        setItems(await fetchJSON('/api/maintenance/items'));
        setOverdue(await fetchJSON('/api/maintenance/overdue'));
    };
    useEffect(() => { load(); }, []);

    const loadSchedules = async (itemId) => {
        setSelectedItem(itemId);
        setSchedules(await fetchJSON(`/api/maintenance/schedules?item_id=${itemId}`));
    };

    const addItem = async (e) => {
        e.preventDefault();
        await postJSON('/api/maintenance/items', form);
        setForm({ name: '', category: 'equipment', location: '', condition: 'good', notes: '' });
        setShowForm(false);
        load();
    };

    const completeMaint = async (schedId) => {
        const by = prompt('Performed by:') || '';
        await postJSON(`/api/maintenance/schedules/${schedId}/complete`, { performed_by: by, notes: '' });
        if (selectedItem) loadSchedules(selectedItem);
        load();
    };

    return html`
        <div class="tab-content">
            ${overdue.length > 0 && html`
                <div class="alert alert-warning">
                    <strong>Overdue Tasks (${overdue.length}):</strong>
                    ${overdue.map(s => html`
                        <div class="overdue-item" key=${s.id}>
                            <span>${s.item_name} - ${s.task_description} (due ${s.next_due})</span>
                            <button class="btn btn-sm" onClick=${() => completeMaint(s.id)}>Complete</button>
                        </div>
                    `)}
                </div>
            `}
            <div class="section-header">
                <h3>Infrastructure Items</h3>
                <button class="btn" onClick=${() => setShowForm(!showForm)}>+ Add Item</button>
            </div>
            ${showForm && html`
                <form class="form-card" onSubmit=${addItem}>
                    <input placeholder="Name" required value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} />
                    <select value=${form.category} onChange=${e => setForm({...form, category: e.target.value})}>
                        <option value="water">Water</option>
                        <option value="power">Power</option>
                        <option value="building">Building</option>
                        <option value="vehicle">Vehicle</option>
                        <option value="equipment">Equipment</option>
                    </select>
                    <input placeholder="Location" value=${form.location} onInput=${e => setForm({...form, location: e.target.value})} />
                    <select value=${form.condition} onChange=${e => setForm({...form, condition: e.target.value})}>
                        <option value="good">Good</option>
                        <option value="fair">Fair</option>
                        <option value="poor">Poor</option>
                        <option value="critical">Critical</option>
                    </select>
                    <input placeholder="Notes" value=${form.notes} onInput=${e => setForm({...form, notes: e.target.value})} />
                    <button class="btn" type="submit">Save</button>
                </form>
            `}
            <div class="card-grid">
                ${items.map(item => html`
                    <div class="card" key=${item.id} onClick=${() => loadSchedules(item.id)}>
                        <div class="card-header">
                            <span class="card-title">${item.name}</span>
                            <${ConditionBadge} condition=${item.condition} />
                        </div>
                        <div class="card-meta">${item.category} | ${item.location || 'No location'}</div>
                        ${item.notes && html`<div class="card-notes">${item.notes}</div>`}
                    </div>
                `)}
            </div>
            ${selectedItem && html`
                <div class="schedules-panel">
                    <h4>Maintenance Schedules</h4>
                    ${schedules.length === 0 && html`<p class="text-muted">No schedules for this item.</p>`}
                    ${schedules.map(s => html`
                        <div class="schedule-row" key=${s.id}>
                            <div>
                                <strong>${s.task_description}</strong>
                                <div class="text-muted">Every ${s.frequency_days} days | Next due: ${s.next_due}</div>
                            </div>
                            <button class="btn btn-sm" onClick=${() => completeMaint(s.id)}>Complete</button>
                        </div>
                    `)}
                </div>
            `}
        </div>
    `;
}

// --- Parts Tab ---
function PartsTab() {
    const [parts, setParts] = useState([]);
    const [searchEquip, setSearchEquip] = useState('');
    const [searchResults, setSearchResults] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState({ part_number: '', name: '', category: '', description: '', fits_equipment: '', salvage_sources: '', quantity_on_hand: 0, location: '' });

    useEffect(() => { fetchJSON('/api/parts').then(setParts); }, []);

    const search = async () => {
        if (!searchEquip.trim()) return;
        setSearchResults(await fetchJSON(`/api/parts/search?equipment=${encodeURIComponent(searchEquip)}`));
    };

    const addPart = async (e) => {
        e.preventDefault();
        await postJSON('/api/parts', {
            ...form,
            fits_equipment: form.fits_equipment.split(',').map(s => s.trim()).filter(Boolean),
            salvage_sources: form.salvage_sources.split(',').map(s => s.trim()).filter(Boolean),
            quantity_on_hand: parseInt(form.quantity_on_hand) || 0,
        });
        setShowForm(false);
        setParts(await fetchJSON('/api/parts'));
    };

    const displayParts = searchResults !== null ? searchResults : parts;

    return html`
        <div class="tab-content">
            <div class="search-bar">
                <input placeholder="Search by equipment name..." value=${searchEquip} onInput=${e => setSearchEquip(e.target.value)} onKeyDown=${e => e.key === 'Enter' && search()} />
                <button class="btn" onClick=${search}>Search</button>
                ${searchResults !== null && html`<button class="btn btn-secondary" onClick=${() => { setSearchResults(null); setSearchEquip(''); }}>Clear</button>`}
                <button class="btn" onClick=${() => setShowForm(!showForm)}>+ Add Part</button>
            </div>
            ${showForm && html`
                <form class="form-card" onSubmit=${addPart}>
                    <input placeholder="Part Number" required value=${form.part_number} onInput=${e => setForm({...form, part_number: e.target.value})} />
                    <input placeholder="Name" required value=${form.name} onInput=${e => setForm({...form, name: e.target.value})} />
                    <input placeholder="Category" value=${form.category} onInput=${e => setForm({...form, category: e.target.value})} />
                    <input placeholder="Description" value=${form.description} onInput=${e => setForm({...form, description: e.target.value})} />
                    <input placeholder="Fits Equipment (comma-separated)" value=${form.fits_equipment} onInput=${e => setForm({...form, fits_equipment: e.target.value})} />
                    <input placeholder="Salvage Sources (comma-separated)" value=${form.salvage_sources} onInput=${e => setForm({...form, salvage_sources: e.target.value})} />
                    <input type="number" placeholder="Quantity" value=${form.quantity_on_hand} onInput=${e => setForm({...form, quantity_on_hand: e.target.value})} />
                    <input placeholder="Location" value=${form.location} onInput=${e => setForm({...form, location: e.target.value})} />
                    <button class="btn" type="submit">Save</button>
                </form>
            `}
            <div class="card-grid">
                ${displayParts.map(p => html`
                    <div class="card" key=${p.id}>
                        <div class="card-header">
                            <span class="card-title">${p.name}</span>
                            <span class="badge">${p.part_number}</span>
                        </div>
                        <div class="card-meta">Qty: ${p.quantity_on_hand} | ${p.location || 'No location'}</div>
                        ${p.description && html`<div class="card-notes">${p.description}</div>`}
                        ${p.fits_equipment && p.fits_equipment.length > 0 && html`
                            <div class="tag-list">Fits: ${p.fits_equipment.map(e => html`<span class="tag" key=${e}>${e}</span>`)}</div>
                        `}
                    </div>
                `)}
            </div>
        </div>
    `;
}

// --- Calculator Tab ---
function CalculatorTab() {
    const [subTab, setSubTab] = useState('lumber');
    const [result, setResult] = useState(null);

    const [lumber, setLumber] = useState({ length_ft: '', width_in: '', thickness_in: '', wall_length_ft: '', spacing_in: '16' });
    const [concrete, setConcrete] = useState({ length_ft: '', width_ft: '', depth_in: '', diameter_in: '', height_ft: '', shape: 'slab' });
    const [roofing, setRoofing] = useState({ length_ft: '', width_ft: '', pitch: '4' });
    const [fencing, setFencing] = useState({ perimeter_ft: '', post_spacing_ft: '8', wire_strands: '3' });
    const [paint, setPaint] = useState({ wallLength: '', wallHeight: '', coats: '2', doors: '0', windows: '0' });

    const calc = async (type, data) => {
        setResult(await postJSON(`/api/calculator/${type}`, data));
    };

    const calcLumber = () => calc('lumber', {
        length_ft: parseFloat(lumber.length_ft) || 0,
        width_in: parseFloat(lumber.width_in) || 0,
        thickness_in: parseFloat(lumber.thickness_in) || 0,
        wall_length_ft: parseFloat(lumber.wall_length_ft) || 0,
        spacing_in: parseFloat(lumber.spacing_in) || 16,
    });

    const calcConcrete = () => calc('concrete', {
        length_ft: parseFloat(concrete.length_ft) || 0,
        width_ft: parseFloat(concrete.width_ft) || 0,
        depth_in: parseFloat(concrete.depth_in) || 0,
        diameter_in: parseFloat(concrete.diameter_in) || 0,
        height_ft: parseFloat(concrete.height_ft) || 0,
        shape: concrete.shape,
    });

    const calcRoofing = () => calc('roofing', {
        length_ft: parseFloat(roofing.length_ft) || 0,
        width_ft: parseFloat(roofing.width_ft) || 0,
        pitch: parseFloat(roofing.pitch) || 4,
    });

    const calcFencing = () => calc('fencing', {
        perimeter_ft: parseFloat(fencing.perimeter_ft) || 0,
        post_spacing_ft: parseFloat(fencing.post_spacing_ft) || 8,
        wire_strands: parseInt(fencing.wire_strands) || 3,
    });

    const calcPaint = () => calc('paint', {
        walls: [{ length: parseFloat(paint.wallLength) || 0, height: parseFloat(paint.wallHeight) || 0 }],
        coats: parseInt(paint.coats) || 2,
        doors: parseInt(paint.doors) || 0,
        windows: parseInt(paint.windows) || 0,
    });

    return html`
        <div class="tab-content">
            <div class="sub-tabs">
                ${['lumber', 'concrete', 'roofing', 'fencing', 'paint'].map(t => html`
                    <button key=${t} class=${'sub-tab' + (subTab === t ? ' active' : '')} onClick=${() => { setSubTab(t); setResult(null); }}>${t.charAt(0).toUpperCase() + t.slice(1)}</button>
                `)}
            </div>

            ${subTab === 'lumber' && html`
                <div class="calc-form">
                    <h4>Board Feet</h4>
                    <div class="form-row">
                        <input placeholder="Length (ft)" value=${lumber.length_ft} onInput=${e => setLumber({...lumber, length_ft: e.target.value})} />
                        <input placeholder="Width (in)" value=${lumber.width_in} onInput=${e => setLumber({...lumber, width_in: e.target.value})} />
                        <input placeholder="Thickness (in)" value=${lumber.thickness_in} onInput=${e => setLumber({...lumber, thickness_in: e.target.value})} />
                    </div>
                    <h4>Stud Count</h4>
                    <div class="form-row">
                        <input placeholder="Wall Length (ft)" value=${lumber.wall_length_ft} onInput=${e => setLumber({...lumber, wall_length_ft: e.target.value})} />
                        <input placeholder="Spacing (in)" value=${lumber.spacing_in} onInput=${e => setLumber({...lumber, spacing_in: e.target.value})} />
                    </div>
                    <button class="btn" onClick=${calcLumber}>Calculate</button>
                </div>
            `}

            ${subTab === 'concrete' && html`
                <div class="calc-form">
                    <select value=${concrete.shape} onChange=${e => setConcrete({...concrete, shape: e.target.value})}>
                        <option value="slab">Slab</option>
                        <option value="footing">Footing</option>
                        <option value="column">Column</option>
                    </select>
                    ${concrete.shape !== 'column' ? html`
                        <div class="form-row">
                            <input placeholder="Length (ft)" value=${concrete.length_ft} onInput=${e => setConcrete({...concrete, length_ft: e.target.value})} />
                            <input placeholder="Width (ft)" value=${concrete.width_ft} onInput=${e => setConcrete({...concrete, width_ft: e.target.value})} />
                            <input placeholder="Depth (in)" value=${concrete.depth_in} onInput=${e => setConcrete({...concrete, depth_in: e.target.value})} />
                        </div>
                    ` : html`
                        <div class="form-row">
                            <input placeholder="Diameter (in)" value=${concrete.diameter_in} onInput=${e => setConcrete({...concrete, diameter_in: e.target.value})} />
                            <input placeholder="Height (ft)" value=${concrete.height_ft} onInput=${e => setConcrete({...concrete, height_ft: e.target.value})} />
                        </div>
                    `}
                    <button class="btn" onClick=${calcConcrete}>Calculate</button>
                </div>
            `}

            ${subTab === 'roofing' && html`
                <div class="calc-form">
                    <div class="form-row">
                        <input placeholder="Length (ft)" value=${roofing.length_ft} onInput=${e => setRoofing({...roofing, length_ft: e.target.value})} />
                        <input placeholder="Width (ft)" value=${roofing.width_ft} onInput=${e => setRoofing({...roofing, width_ft: e.target.value})} />
                        <input placeholder="Pitch (rise/12)" value=${roofing.pitch} onInput=${e => setRoofing({...roofing, pitch: e.target.value})} />
                    </div>
                    <button class="btn" onClick=${calcRoofing}>Calculate</button>
                </div>
            `}

            ${subTab === 'fencing' && html`
                <div class="calc-form">
                    <div class="form-row">
                        <input placeholder="Perimeter (ft)" value=${fencing.perimeter_ft} onInput=${e => setFencing({...fencing, perimeter_ft: e.target.value})} />
                        <input placeholder="Post Spacing (ft)" value=${fencing.post_spacing_ft} onInput=${e => setFencing({...fencing, post_spacing_ft: e.target.value})} />
                        <input placeholder="Wire Strands" value=${fencing.wire_strands} onInput=${e => setFencing({...fencing, wire_strands: e.target.value})} />
                    </div>
                    <button class="btn" onClick=${calcFencing}>Calculate</button>
                </div>
            `}

            ${subTab === 'paint' && html`
                <div class="calc-form">
                    <div class="form-row">
                        <input placeholder="Wall Length (ft)" value=${paint.wallLength} onInput=${e => setPaint({...paint, wallLength: e.target.value})} />
                        <input placeholder="Wall Height (ft)" value=${paint.wallHeight} onInput=${e => setPaint({...paint, wallHeight: e.target.value})} />
                        <input placeholder="Coats" value=${paint.coats} onInput=${e => setPaint({...paint, coats: e.target.value})} />
                    </div>
                    <div class="form-row">
                        <input placeholder="Doors" value=${paint.doors} onInput=${e => setPaint({...paint, doors: e.target.value})} />
                        <input placeholder="Windows" value=${paint.windows} onInput=${e => setPaint({...paint, windows: e.target.value})} />
                    </div>
                    <button class="btn" onClick=${calcPaint}>Calculate</button>
                </div>
            `}

            ${result && html`
                <div class="result-card">
                    <h4>Results</h4>
                    <table class="result-table">
                        <tbody>
                            ${Object.entries(result).map(([k, v]) => html`
                                <tr key=${k}>
                                    <td class="result-label">${k.replace(/_/g, ' ')}</td>
                                    <td class="result-value">${typeof v === 'number' ? v.toLocaleString() : v}</td>
                                </tr>
                            `)}
                        </tbody>
                    </table>
                </div>
            `}
        </div>
    `;
}

// --- Chemistry Tab ---
function ChemistryTab() {
    const [recipes, setRecipes] = useState([]);
    const [search, setSearch] = useState('');
    const [expanded, setExpanded] = useState(null);

    const load = async (q) => {
        if (q && q.trim()) {
            setRecipes(await fetchJSON(`/api/chemistry/search?q=${encodeURIComponent(q)}`));
        } else {
            setRecipes(await fetchJSON('/api/chemistry'));
        }
    };
    useEffect(() => { load(); }, []);

    const doSearch = () => load(search);

    return html`
        <div class="tab-content">
            <div class="search-bar">
                <input placeholder="Search recipes or ingredients..." value=${search} onInput=${e => setSearch(e.target.value)} onKeyDown=${e => e.key === 'Enter' && doSearch()} />
                <button class="btn" onClick=${doSearch}>Search</button>
                ${search && html`<button class="btn btn-secondary" onClick=${() => { setSearch(''); load(); }}>Clear</button>`}
            </div>
            <div class="card-grid">
                ${recipes.map(r => html`
                    <div class="card card-expandable" key=${r.id} onClick=${() => setExpanded(expanded === r.id ? null : r.id)}>
                        <div class="card-header">
                            <span class="card-title">${r.name}</span>
                            <${DifficultyBadge} difficulty=${r.difficulty} />
                        </div>
                        <div class="card-meta">${r.category}</div>
                        ${expanded === r.id && html`
                            <div class="card-expanded">
                                <h5>Ingredients</h5>
                                <ul>
                                    ${r.ingredients.map((ing, i) => html`<li key=${i}>${ing.name} - ${ing.quantity}</li>`)}
                                </ul>
                                <h5>Procedure</h5>
                                <ol>
                                    ${r.procedure.map((step, i) => html`<li key=${i}>${step}</li>`)}
                                </ol>
                                ${r.safety_notes && html`<div class="safety-notes"><strong>Safety:</strong> ${r.safety_notes}</div>`}
                                ${r.yield && html`<div class="text-muted">Yield: ${r.yield}</div>`}
                            </div>
                        `}
                    </div>
                `)}
            </div>
        </div>
    `;
}

// --- Guides Tab ---
function GuidesTab() {
    const [guides, setGuides] = useState([]);
    const [search, setSearch] = useState('');
    const [selectedGuide, setSelectedGuide] = useState(null);

    const load = async (q) => {
        if (q && q.trim()) {
            setGuides(await fetchJSON(`/api/guides/search?q=${encodeURIComponent(q)}`));
        } else {
            setGuides(await fetchJSON('/api/guides'));
        }
    };
    useEffect(() => { load(); }, []);

    const viewGuide = async (id) => {
        setSelectedGuide(await fetchJSON(`/api/guides/${id}`));
    };

    return html`
        <div class="tab-content">
            ${selectedGuide ? html`
                <div>
                    <button class="btn btn-secondary" onClick=${() => setSelectedGuide(null)}>Back to Guides</button>
                    <div class="guide-view">
                        <h2>${selectedGuide.title}</h2>
                        <div class="card-meta">${selectedGuide.category} | ${selectedGuide.difficulty} | by ${selectedGuide.author}</div>
                        ${selectedGuide.parts_needed && selectedGuide.parts_needed.length > 0 && html`
                            <div class="tag-list">Parts: ${selectedGuide.parts_needed.map(p => html`<span class="tag" key=${p}>${p}</span>`)}</div>
                        `}
                        <div class="guide-content">${selectedGuide.content}</div>
                    </div>
                </div>
            ` : html`
                <div>
                    <div class="search-bar">
                        <input placeholder="Search guides..." value=${search} onInput=${e => setSearch(e.target.value)} onKeyDown=${e => e.key === 'Enter' && load(search)} />
                        <button class="btn" onClick=${() => load(search)}>Search</button>
                        ${search && html`<button class="btn btn-secondary" onClick=${() => { setSearch(''); load(); }}>Clear</button>`}
                    </div>
                    <div class="card-grid">
                        ${guides.map(g => html`
                            <div class="card" key=${g.id} onClick=${() => viewGuide(g.id)}>
                                <div class="card-header">
                                    <span class="card-title">${g.title}</span>
                                    <${DifficultyBadge} difficulty=${g.difficulty} />
                                </div>
                                <div class="card-meta">${g.category} | by ${g.author}</div>
                            </div>
                        `)}
                    </div>
                </div>
            `}
        </div>
    `;
}

// --- Drawings Tab ---
function DrawingsTab() {
    const [drawings, setDrawings] = useState([]);
    const [search, setSearch] = useState('');

    const load = async (q) => {
        if (q && q.trim()) {
            setDrawings(await fetchJSON(`/api/drawings/search?q=${encodeURIComponent(q)}`));
        } else {
            setDrawings(await fetchJSON('/api/drawings'));
        }
    };
    useEffect(() => { load(); }, []);

    return html`
        <div class="tab-content">
            <div class="search-bar">
                <input placeholder="Search drawings..." value=${search} onInput=${e => setSearch(e.target.value)} onKeyDown=${e => e.key === 'Enter' && load(search)} />
                <button class="btn" onClick=${() => load(search)}>Search</button>
                ${search && html`<button class="btn btn-secondary" onClick=${() => { setSearch(''); load(); }}>Clear</button>`}
            </div>
            ${drawings.length === 0 && html`<p class="text-muted">No technical drawings yet.</p>`}
            <div class="card-grid">
                ${drawings.map(d => html`
                    <div class="card" key=${d.id}>
                        <div class="card-header">
                            <span class="card-title">${d.title}</span>
                        </div>
                        <div class="card-meta">${d.category} | ${d.related_equipment || 'General'}</div>
                        ${d.description && html`<div class="card-notes">${d.description}</div>`}
                        <div class="text-muted">File: ${d.file_path}</div>
                    </div>
                `)}
            </div>
        </div>
    `;
}

// --- Main App ---
function App() {
    const [tab, setTab] = useState('maintenance');

    const tabs = [
        { id: 'maintenance', label: 'Maintenance' },
        { id: 'parts', label: 'Parts' },
        { id: 'calculator', label: 'Calculator' },
        { id: 'chemistry', label: 'Chemistry' },
        { id: 'guides', label: 'Guides' },
        { id: 'drawings', label: 'Drawings' },
    ];

    return html`
        <div class="app-container">
            <header class="app-header">
                <h1>Engineering & Maintenance</h1>
                <nav class="tab-bar">
                    ${tabs.map(t => html`
                        <button key=${t.id} class=${'tab-btn' + (tab === t.id ? ' active' : '')} onClick=${() => setTab(t.id)}>${t.label}</button>
                    `)}
                </nav>
            </header>
            <main class="app-main">
                ${tab === 'maintenance' && html`<${MaintenanceTab} />`}
                ${tab === 'parts' && html`<${PartsTab} />`}
                ${tab === 'calculator' && html`<${CalculatorTab} />`}
                ${tab === 'chemistry' && html`<${ChemistryTab} />`}
                ${tab === 'guides' && html`<${GuidesTab} />`}
                ${tab === 'drawings' && html`<${DrawingsTab} />`}
            </main>
        </div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
