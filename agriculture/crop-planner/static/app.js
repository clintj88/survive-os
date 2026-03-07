import { h, render, Component } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

async function api(path, opts = {}) {
    const res = await fetch(path, {
        headers: { 'Content-Type': 'application/json' },
        ...opts,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (res.status === 204) return null;
    return res.json();
}

// ---- Field Map Tab ----
function FieldMap() {
    const [fields, setFields] = useState([]);
    const [selected, setSelected] = useState(null);
    const [plots, setPlots] = useState([]);
    const [crops, setCrops] = useState([]);
    const [newName, setNewName] = useState('');
    const [rows, setRows] = useState(4);
    const [cols, setCols] = useState(4);
    const [assignCrop, setAssignCrop] = useState('');
    const [assignPlot, setAssignPlot] = useState(null);
    const [season, setSeason] = useState('spring');
    const [year, setYear] = useState(2026);

    const load = async () => {
        const f = await api('/api/fields');
        setFields(f);
        const c = await api('/api/crops');
        setCrops(c);
    };
    useEffect(() => { load(); }, []);

    const selectField = async (f) => {
        setSelected(f);
        const p = await api(`/api/fields/${f.id}/plots`);
        setPlots(p);
    };

    const createField = async () => {
        if (!newName) return;
        await api('/api/fields', { method: 'POST', body: { name: newName, rows, cols } });
        setNewName('');
        load();
    };

    const assign = async () => {
        if (!assignPlot || !assignCrop) return;
        await api(`/api/fields/${selected.id}/plots/${assignPlot}/assign`, {
            method: 'POST', body: { crop_id: parseInt(assignCrop), season, year: parseInt(year) }
        });
        selectField(selected);
        setAssignPlot(null);
    };

    const getGroup = (plotData) => {
        if (!plotData.crop_id) return '';
        const crop = crops.find(c => c.id === plotData.crop_id);
        return crop ? crop.rotation_group : '';
    };

    return html`
        <div class="panel">
            <h2>Fields</h2>
            <div class="form-row">
                <input placeholder="Field name" value=${newName} onInput=${e => setNewName(e.target.value)} />
                <input type="number" value=${rows} min="1" max="20" style="width:60px" onInput=${e => setRows(+e.target.value)} />
                <span style="align-self:center">x</span>
                <input type="number" value=${cols} min="1" max="20" style="width:60px" onInput=${e => setCols(+e.target.value)} />
                <button onClick=${createField}>Add Field</button>
            </div>
            <div class="form-row" style="gap:0.5rem;margin-top:0.5rem">
                ${fields.map(f => html`
                    <button class=${selected?.id === f.id ? '' : 'secondary'} onClick=${() => selectField(f)}>${f.name}</button>
                `)}
            </div>
        </div>

        ${selected && html`
            <div class="panel">
                <h2>${selected.name}</h2>
                <div class="form-row">
                    <select value=${season} onChange=${e => setSeason(e.target.value)}>
                        <option value="spring">Spring</option>
                        <option value="summer">Summer</option>
                        <option value="fall">Fall</option>
                    </select>
                    <input type="number" value=${year} style="width:80px" onInput=${e => setYear(+e.target.value)} />
                </div>
                <div class="field-grid" style=${`grid-template-columns: repeat(${selected.cols}, 1fr)`}>
                    ${plots.map(p => html`
                        <div class="plot-cell ${getGroup(p)}"
                             onClick=${() => setAssignPlot(p.id)}>
                            <span class="label">${p.label}</span>
                            <span class="crop">${p.crop_name || '-'}</span>
                        </div>
                    `)}
                </div>
                ${assignPlot && html`
                    <div class="form-row" style="margin-top:0.5rem">
                        <select value=${assignCrop} onChange=${e => setAssignCrop(e.target.value)}>
                            <option value="">Select crop...</option>
                            ${crops.map(c => html`<option value=${c.id}>${c.name} (${c.rotation_group})</option>`)}
                        </select>
                        <button onClick=${assign}>Assign</button>
                        <button class="secondary" onClick=${() => setAssignPlot(null)}>Cancel</button>
                    </div>
                `}
            </div>
        `}
    `;
}

// ---- Rotation Plans Tab ----
function RotationPlans() {
    const [templates, setTemplates] = useState([]);
    useEffect(() => { api('/api/rotations/templates').then(setTemplates); }, []);

    return html`
        <div class="panel">
            <h2>Rotation Templates</h2>
            ${templates.map(t => html`
                <div style="margin-bottom:1rem">
                    <h3 style="font-size:0.95rem">${t.name} <span style="color:var(--text-muted);font-size:0.8rem">(${t.climate_zone})</span></h3>
                    <p style="font-size:0.8rem;color:var(--text-muted)">${t.description}</p>
                    <div class="timeline">
                        ${t.steps.map(s => html`
                            <div class="timeline-year">
                                <div class="year">Year ${s.year_offset + 1}</div>
                                <div class="group">${s.rotation_group}</div>
                                <div style="font-size:0.7rem;color:var(--text-muted)">${s.notes}</div>
                            </div>
                        `)}
                    </div>
                </div>
            `)}
        </div>
    `;
}

// ---- Companions Tab ----
function Companions() {
    const [companions, setCompanions] = useState([]);
    const [filter, setFilter] = useState('');
    const [cropA, setCropA] = useState('');
    const [cropB, setCropB] = useState('');
    const [checkResult, setCheckResult] = useState(null);

    const load = () => {
        const url = filter ? `/api/companions?crop=${encodeURIComponent(filter)}` : '/api/companions';
        api(url).then(setCompanions);
    };
    useEffect(load, [filter]);

    const check = async () => {
        if (!cropA || !cropB) return;
        const r = await api(`/api/companions/check?crop_a=${encodeURIComponent(cropA)}&crop_b=${encodeURIComponent(cropB)}`);
        setCheckResult(r);
    };

    return html`
        <div class="panel">
            <h2>Companion Planting Guide</h2>
            <div class="form-row">
                <input placeholder="Filter by crop..." value=${filter} onInput=${e => setFilter(e.target.value)} />
            </div>
            <table>
                <thead><tr><th>Crop A</th><th>Crop B</th><th>Relationship</th><th>Notes</th></tr></thead>
                <tbody>
                    ${companions.map(c => html`
                        <tr>
                            <td>${c.crop_a}</td>
                            <td>${c.crop_b}</td>
                            <td><span class="badge ${c.relationship}">${c.relationship}</span></td>
                            <td style="font-size:0.8rem;color:var(--text-muted)">${c.notes}</td>
                        </tr>
                    `)}
                </tbody>
            </table>
        </div>
        <div class="panel">
            <h2>Check Compatibility</h2>
            <div class="form-row">
                <input placeholder="Crop A" value=${cropA} onInput=${e => setCropA(e.target.value)} />
                <input placeholder="Crop B" value=${cropB} onInput=${e => setCropB(e.target.value)} />
                <button onClick=${check}>Check</button>
            </div>
            ${checkResult && html`
                <p style="margin-top:0.5rem">
                    <span class="badge ${checkResult.relationship}">${checkResult.relationship}</span>
                    <span style="margin-left:0.5rem;font-size:0.85rem">${checkResult.notes}</span>
                </p>
            `}
        </div>
    `;
}

// ---- Calendar Tab ----
function Calendar() {
    const [year, setYear] = useState(2026);
    const [month, setMonth] = useState(new Date().getMonth() + 1);
    const [events, setEvents] = useState([]);
    const [frost, setFrost] = useState(null);

    useEffect(() => {
        api(`/api/calendar/month/${year}/${month}`).then(setEvents);
        api(`/api/calendar/frost-dates?year=${year}`).then(setFrost);
    }, [year, month]);

    const daysInMonth = new Date(year, month, 0).getDate();
    const firstDay = new Date(year, month - 1, 1).getDay();
    const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
    const blanks = Array.from({ length: firstDay }, () => null);
    const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

    const getEvents = (day) => {
        const d = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
        return events.filter(e => e.date === d);
    };

    return html`
        <div class="panel">
            <h2>Planting Calendar</h2>
            ${frost && html`
                <p style="font-size:0.85rem;margin-bottom:0.5rem">
                    Last Spring Frost: <strong>${frost.last_spring_frost}</strong> |
                    First Fall Frost: <strong>${frost.first_fall_frost}</strong> |
                    Growing Season: <strong>${frost.growing_season_days} days</strong>
                </p>
            `}
            <div class="form-row">
                <button class="secondary" onClick=${() => { if (month === 1) { setMonth(12); setYear(y => y-1); } else setMonth(m => m-1); }}>Prev</button>
                <span style="align-self:center;font-weight:bold">${monthNames[month-1]} ${year}</span>
                <button class="secondary" onClick=${() => { if (month === 12) { setMonth(1); setYear(y => y+1); } else setMonth(m => m+1); }}>Next</button>
            </div>
            <div class="cal-grid" style="margin-top:0.5rem">
                ${['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => html`<div class="cal-header">${d}</div>`)}
                ${blanks.map(() => html`<div></div>`)}
                ${days.map(d => html`
                    <div class="cal-day">
                        <div class="day-num">${d}</div>
                        ${getEvents(d).map(e => html`<div class="cal-event">${e.crop_name}: ${e.event}</div>`)}
                    </div>
                `)}
            </div>
        </div>
    `;
}

// ---- Yields Tab ----
function Yields() {
    const [yields, setYields] = useState([]);
    const [crops, setCrops] = useState([]);
    const [prediction, setPrediction] = useState(null);
    const [predPlot, setPredPlot] = useState('');
    const [predCrop, setPredCrop] = useState('');

    useEffect(() => {
        api('/api/yields').then(setYields);
        api('/api/crops').then(setCrops);
    }, []);

    const predict = async () => {
        if (!predPlot || !predCrop) return;
        const r = await api(`/api/yields/predict?plot_id=${predPlot}&crop_id=${predCrop}`);
        setPrediction(r);
    };

    return html`
        <div class="panel">
            <h2>Yield History</h2>
            <table>
                <thead><tr><th>Crop</th><th>Plot</th><th>Year</th><th>Season</th><th>Amount</th></tr></thead>
                <tbody>
                    ${yields.map(y => html`
                        <tr>
                            <td>${y.crop_name}</td>
                            <td>${y.plot_label}</td>
                            <td>${y.year}</td>
                            <td>${y.season}</td>
                            <td>${y.amount} ${y.unit}</td>
                        </tr>
                    `)}
                    ${yields.length === 0 && html`<tr><td colspan="5" style="color:var(--text-muted)">No yield data recorded yet</td></tr>`}
                </tbody>
            </table>
        </div>
        <div class="panel">
            <h2>Yield Prediction</h2>
            <div class="form-row">
                <input type="number" placeholder="Plot ID" value=${predPlot} onInput=${e => setPredPlot(e.target.value)} style="width:80px" />
                <select value=${predCrop} onChange=${e => setPredCrop(e.target.value)}>
                    <option value="">Select crop...</option>
                    ${crops.map(c => html`<option value=${c.id}>${c.name}</option>`)}
                </select>
                <button onClick=${predict}>Predict</button>
            </div>
            ${prediction && html`
                <div style="margin-top:0.75rem">
                    <p><strong>${prediction.crop_name}</strong></p>
                    ${prediction.predicted_yield != null ? html`
                        <p>Predicted: <strong>${prediction.predicted_yield} ${prediction.unit}</strong> (${prediction.confidence} confidence)</p>
                        <p style="font-size:0.8rem;color:var(--text-muted)">Average: ${prediction.average_yield} ${prediction.unit} | Trend: ${prediction.trend > 0 ? '+' : ''}${prediction.trend} | Data points: ${prediction.data_points}</p>
                    ` : html`<p style="color:var(--text-muted)">${prediction.message}</p>`}
                </div>
            `}
        </div>
    `;
}

// ---- App Shell ----
function App() {
    const [tab, setTab] = useState('fields');
    const tabs = [
        { id: 'fields', label: 'Field Map' },
        { id: 'rotations', label: 'Rotation Plans' },
        { id: 'companions', label: 'Companions' },
        { id: 'calendar', label: 'Calendar' },
        { id: 'yields', label: 'Yields' },
    ];

    return html`
        <header>
            <h1>Crop Rotation Planner</h1>
        </header>
        <div class="tabs">
            ${tabs.map(t => html`
                <button class="tab ${tab === t.id ? 'active' : ''}" onClick=${() => setTab(t.id)}>${t.label}</button>
            `)}
        </div>
        ${tab === 'fields' && html`<${FieldMap} />`}
        ${tab === 'rotations' && html`<${RotationPlans} />`}
        ${tab === 'companions' && html`<${Companions} />`}
        ${tab === 'calendar' && html`<${Calendar} />`}
        ${tab === 'yields' && html`<${Yields} />`}
    `;
}

render(html`<${App} />`, document.getElementById('app'));
