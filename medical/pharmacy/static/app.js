import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const API = '';

async function api(path, opts = {}) {
    const res = await fetch(`${API}${path}`, {
        headers: { 'Content-Type': 'application/json', ...opts.headers },
        ...opts,
    });
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
}

// --- Expiration helpers ---
function expirationClass(dateStr) {
    const days = Math.floor((new Date(dateStr) - new Date()) / 86400000);
    if (days < 0) return 'exp-red';
    if (days <= 30) return 'exp-red';
    if (days <= 60) return 'exp-orange';
    if (days <= 90) return 'exp-yellow';
    return 'exp-green';
}

function severityBadge(severity) {
    return html`<span class="badge badge-${severity}">${severity}</span>`;
}

// --- Inventory Tab ---
function InventoryPanel() {
    const [meds, setMeds] = useState([]);
    const [search, setSearch] = useState('');
    const [selected, setSelected] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [showLotForm, setShowLotForm] = useState(false);

    const load = () => api(`/api/inventory/medications?search=${search}`).then(setMeds).catch(() => {});
    useEffect(() => { load(); }, [search]);

    const createMed = async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const data = Object.fromEntries(fd);
        await api('/api/inventory/medications', { method: 'POST', body: JSON.stringify(data) });
        e.target.reset();
        setShowForm(false);
        load();
    };

    const createLot = async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const data = Object.fromEntries(fd);
        data.medication_id = parseInt(data.medication_id);
        data.quantity = parseInt(data.quantity);
        await api('/api/inventory/lots', { method: 'POST', body: JSON.stringify(data) });
        e.target.reset();
        setShowLotForm(false);
        if (selected) setSelected(await api(`/api/inventory/medications/${selected.id}`));
        load();
    };

    return html`
        <div class="search-bar">
            <input type="text" placeholder="Search medications..." value=${search}
                onInput=${e => setSearch(e.target.value)} />
            <button onClick=${() => setShowForm(!showForm)}>+ Medication</button>
            <button class="btn-secondary" onClick=${() => setShowLotForm(!showLotForm)}>+ Lot</button>
        </div>

        ${showForm && html`
            <form class="card" onSubmit=${createMed}>
                <h3>Add Medication</h3>
                <div class="form-row">
                    <div class="form-group"><label>Name</label><input name="name" required /></div>
                    <div class="form-group"><label>Generic Name</label><input name="generic_name" /></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Category</label><input name="category" /></div>
                    <div class="form-group">
                        <label>Form</label>
                        <select name="form">
                            <option>tablet</option><option>capsule</option><option>liquid</option>
                            <option>injection</option><option>topical</option><option>cream</option>
                            <option>drops</option><option>inhaler</option>
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Strength</label><input name="strength" /></div>
                    <div class="form-group"><label>Unit</label><input name="unit" /></div>
                </div>
                <button type="submit">Save</button>
            </form>
        `}

        ${showLotForm && html`
            <form class="card" onSubmit=${createLot}>
                <h3>Add Inventory Lot</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>Medication</label>
                        <select name="medication_id" required>
                            <option value="">Select...</option>
                            ${meds.map(m => html`<option value=${m.id}>${m.name} ${m.strength}</option>`)}
                        </select>
                    </div>
                    <div class="form-group"><label>Lot Number</label><input name="lot_number" /></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Quantity</label><input name="quantity" type="number" required /></div>
                    <div class="form-group"><label>Expiration Date</label><input name="expiration_date" type="date" required /></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Supplier</label><input name="supplier" /></div>
                    <div class="form-group"><label>Storage Location</label><input name="storage_location" /></div>
                </div>
                <button type="submit">Save Lot</button>
            </form>
        `}

        <table>
            <thead><tr><th>Name</th><th>Generic</th><th>Category</th><th>Form</th><th>Strength</th><th>Stock</th></tr></thead>
            <tbody>
                ${meds.map(m => html`
                    <tr style="cursor:pointer" onClick=${async () => setSelected(await api('/api/inventory/medications/' + m.id))}>
                        <td>${m.name}</td><td>${m.generic_name}</td><td>${m.category}</td>
                        <td>${m.form}</td><td>${m.strength}</td>
                        <td>${m.total_stock}</td>
                    </tr>
                `)}
                ${meds.length === 0 && html`<tr><td colspan="6" class="empty-state">No medications found</td></tr>`}
            </tbody>
        </table>

        ${selected && html`
            <div class="card">
                <h3>${selected.name} (${selected.generic_name})</h3>
                <p>${selected.category} - ${selected.form} ${selected.strength}</p>
                <h4 style="margin-top:1rem">Inventory Lots</h4>
                <table>
                    <thead><tr><th>Lot</th><th>Qty</th><th>Expires</th><th>Location</th></tr></thead>
                    <tbody>
                        ${(selected.lots || []).map(l => html`
                            <tr>
                                <td>${l.lot_number}</td>
                                <td>${l.quantity}</td>
                                <td class=${expirationClass(l.expiration_date)}>${l.expiration_date}</td>
                                <td>${l.storage_location}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
                <button class="btn-sm btn-secondary" onClick=${() => setSelected(null)}>Close</button>
            </div>
        `}
    `;
}

// --- Prescriptions Tab ---
function PrescriptionsPanel() {
    const [rxList, setRxList] = useState([]);
    const [patientId, setPatientId] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [meds, setMeds] = useState([]);

    const load = () => {
        const q = patientId ? `?patient_id=${patientId}` : '';
        api(`/api/prescriptions${q}`).then(setRxList).catch(() => {});
    };
    useEffect(() => { load(); api('/api/inventory/medications').then(setMeds).catch(() => {}); }, []);

    const createRx = async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const data = Object.fromEntries(fd);
        data.medication_id = parseInt(data.medication_id);
        data.refills_remaining = parseInt(data.refills_remaining || '0');
        await api('/api/prescriptions', { method: 'POST', body: JSON.stringify(data) });
        e.target.reset();
        setShowForm(false);
        load();
    };

    return html`
        <div class="search-bar">
            <input type="text" placeholder="Patient ID..." value=${patientId}
                onInput=${e => setPatientId(e.target.value)} />
            <button class="btn-secondary" onClick=${load}>Search</button>
            <button onClick=${() => setShowForm(!showForm)}>+ Prescription</button>
        </div>

        ${showForm && html`
            <form class="card" onSubmit=${createRx}>
                <h3>New Prescription</h3>
                <div class="form-row">
                    <div class="form-group"><label>Patient ID</label><input name="patient_id" required /></div>
                    <div class="form-group">
                        <label>Medication</label>
                        <select name="medication_id" required>
                            <option value="">Select...</option>
                            ${meds.map(m => html`<option value=${m.id}>${m.name} ${m.strength}</option>`)}
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Dosage</label><input name="dosage" required placeholder="e.g. 500mg" /></div>
                    <div class="form-group"><label>Frequency</label><input name="frequency" required placeholder="e.g. 3x daily" /></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Duration</label><input name="duration" placeholder="e.g. 7 days" /></div>
                    <div class="form-group"><label>Prescriber</label><input name="prescriber" required /></div>
                </div>
                <div class="form-group"><label>Refills</label><input name="refills_remaining" type="number" value="0" /></div>
                <button type="submit">Create Prescription</button>
            </form>
        `}

        <table>
            <thead><tr><th>Patient</th><th>Medication</th><th>Dosage</th><th>Frequency</th><th>Prescriber</th><th>Status</th></tr></thead>
            <tbody>
                ${rxList.map(rx => html`
                    <tr>
                        <td>${rx.patient_id}</td>
                        <td>${rx.medication_name} ${rx.strength}</td>
                        <td>${rx.dosage}</td>
                        <td>${rx.frequency}</td>
                        <td>${rx.prescriber}</td>
                        <td><span class="badge badge-${rx.status === 'active' ? 'minor' : 'moderate'}">${rx.status}</span></td>
                    </tr>
                `)}
                ${rxList.length === 0 && html`<tr><td colspan="6" class="empty-state">No prescriptions found</td></tr>`}
            </tbody>
        </table>
    `;
}

// --- Interactions Tab ---
function InteractionsPanel() {
    const [drugs, setDrugs] = useState('');
    const [results, setResults] = useState(null);

    const check = async () => {
        const meds = drugs.split(',').map(s => s.trim()).filter(Boolean);
        if (meds.length < 2) return;
        const data = await api('/api/interactions/check', {
            method: 'POST', body: JSON.stringify({ medications: meds }),
        });
        setResults(data);
    };

    return html`
        <div class="card">
            <h3>Drug Interaction Checker</h3>
            <div class="form-group">
                <label>Enter medications (comma-separated)</label>
                <input type="text" value=${drugs} onInput=${e => setDrugs(e.target.value)}
                    placeholder="e.g. Warfarin, Ibuprofen, Aspirin" />
            </div>
            <button onClick=${check}>Check Interactions</button>
        </div>

        ${results !== null && html`
            <div style="margin-top:1rem">
                ${results.length === 0 && html`<div class="result-card"><h4>No interactions found</h4></div>`}
                ${results.map(i => html`
                    <div class="interaction-item">
                        <div class="drugs">${i.drug_a} + ${i.drug_b} ${severityBadge(i.severity)}</div>
                        <div class="desc">${i.description}</div>
                        <div class="desc"><strong>Mechanism:</strong> ${i.mechanism}</div>
                        <div class="desc"><strong>Recommendation:</strong> ${i.recommendation}</div>
                    </div>
                `)}
            </div>
        `}
    `;
}

// --- Natural Medicine Tab ---
function NaturalPanel() {
    const [items, setItems] = useState([]);
    const [search, setSearch] = useState('');

    useEffect(() => {
        api(`/api/natural?search=${search}`).then(setItems).catch(() => {});
    }, [search]);

    return html`
        <div class="search-bar">
            <input type="text" placeholder="Search remedies..." value=${search}
                onInput=${e => setSearch(e.target.value)} />
        </div>
        ${items.map(nm => html`
            <div class="remedy-card">
                <h3>${nm.name}</h3>
                <div class="field"><span class="field-label">Also known as: </span>${nm.common_names}</div>
                <div class="field"><span class="field-label">Uses: </span>${nm.uses}</div>
                <div class="field"><span class="field-label">Preparation: </span>${nm.preparation}</div>
                <div class="field"><span class="field-label">Dosage: </span>${nm.dosage}</div>
                <div class="field"><span class="field-label">Contraindications: </span>${nm.contraindications}</div>
                <div class="field"><span class="field-label">Drug Interactions: </span>${nm.drug_interactions}</div>
                <div class="field"><span class="field-label">Habitat: </span>${nm.habitat}</div>
                <div class="field"><span class="field-label">Identification: </span>${nm.identification}</div>
                ${nm.notes && html`<div class="field"><span class="field-label">Notes: </span>${nm.notes}</div>`}
            </div>
        `)}
        ${items.length === 0 && html`<div class="empty-state">No remedies found</div>`}
    `;
}

// --- Dosage Calculator Tab ---
function DosagePanel() {
    const [medication, setMedication] = useState('');
    const [weight, setWeight] = useState('');
    const [ageMonths, setAgeMonths] = useState('');
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    const calculate = async () => {
        setError('');
        setResult(null);
        try {
            const data = await api('/api/dosage/calculate', {
                method: 'POST',
                body: JSON.stringify({
                    medication,
                    weight_kg: parseFloat(weight),
                    age_months: parseInt(ageMonths),
                }),
            });
            setResult(data);
        } catch (e) {
            setError(e.message);
        }
    };

    return html`
        <div class="card">
            <h3>Dosage Calculator</h3>
            <div class="form-row">
                <div class="form-group">
                    <label>Medication</label>
                    <input type="text" value=${medication} onInput=${e => setMedication(e.target.value)}
                        placeholder="e.g. Acetaminophen" />
                </div>
                <div class="form-group">
                    <label>Weight (kg)</label>
                    <input type="number" step="0.1" value=${weight} onInput=${e => setWeight(e.target.value)} />
                </div>
            </div>
            <div class="form-group">
                <label>Age (months)</label>
                <input type="number" value=${ageMonths} onInput=${e => setAgeMonths(e.target.value)} />
            </div>
            <button onClick=${calculate}>Calculate</button>
        </div>

        ${error && html`<div class="result-card" style="border-color:var(--danger)"><h4>${error}</h4></div>`}

        ${result && html`
            <div class="result-card">
                <h4>${result.medication}</h4>
                <div class="value">${result.recommended_dose_mg} mg</div>
                <div class="detail">Every ${result.frequency_hours} hours</div>
                <div class="detail">Daily total: ${result.calculated_daily_total_mg} mg</div>
                ${result.max_single_dose_mg > 0 && html`<div class="detail">Max single dose: ${result.max_single_dose_mg} mg</div>`}
                ${result.max_daily_dose_mg > 0 && html`<div class="detail">Max daily: ${result.max_daily_dose_mg} mg</div>`}
                ${result.indication && html`<div class="detail">Indication: ${result.indication}</div>`}
                ${result.notes && html`<div class="detail" style="margin-top:0.5rem">${result.notes}</div>`}
            </div>
        `}
    `;
}

// --- Main App ---
function App() {
    const [tab, setTab] = useState('inventory');
    const tabs = [
        ['inventory', 'Inventory'],
        ['prescriptions', 'Prescriptions'],
        ['interactions', 'Interactions'],
        ['natural', 'Natural Medicine'],
        ['dosage', 'Dosage Calculator'],
    ];

    return html`
        <header>
            <h1>SURVIVE OS Pharmacy</h1>
        </header>
        <div class="tabs">
            ${tabs.map(([id, label]) => html`
                <button class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</button>
            `)}
        </div>
        <div class="panel ${tab === 'inventory' ? 'active' : ''}"><${InventoryPanel} /></div>
        <div class="panel ${tab === 'prescriptions' ? 'active' : ''}"><${PrescriptionsPanel} /></div>
        <div class="panel ${tab === 'interactions' ? 'active' : ''}"><${InteractionsPanel} /></div>
        <div class="panel ${tab === 'natural' ? 'active' : ''}"><${NaturalPanel} /></div>
        <div class="panel ${tab === 'dosage' ? 'active' : ''}"><${DosagePanel} /></div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
