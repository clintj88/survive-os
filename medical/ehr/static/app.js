import { h, render, Component } from 'https://esm.sh/preact@10.19.3';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const HEADERS = { 'Content-Type': 'application/json', 'X-User': 'admin', 'X-Role': 'medical' };

async function api(path, opts = {}) {
    const res = await fetch(path, { headers: HEADERS, ...opts });
    if (res.status === 204) return null;
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    const ct = res.headers.get('content-type') || '';
    return ct.includes('json') ? res.json() : res.text();
}

class App extends Component {
    constructor() {
        super();
        this.state = {
            tab: 'patients', health: null,
            patients: [], selectedPatient: null,
            visits: [], vitals: [], wounds: [], vaccinations: [],
            showForm: null, searchQuery: '',
        };
    }

    componentDidMount() {
        api('/health').then(h => this.setState({ health: h }));
        this.loadPatients();
    }

    async loadPatients() {
        const q = this.state.searchQuery ? `?name=${encodeURIComponent(this.state.searchQuery)}` : '';
        this.setState({ patients: await api(`/api/patients${q}`) });
    }

    async selectPatient(id) {
        const p = await api(`/api/patients/${id}`);
        const [visits, vitals, wounds, vaccinations] = await Promise.all([
            api(`/api/patients/${id}/visits`),
            api(`/api/patients/${id}/vitals`),
            api(`/api/patients/${id}/wounds`),
            api(`/api/patients/${id}/vaccinations`),
        ]);
        this.setState({ selectedPatient: p, visits, vitals, wounds, vaccinations });
    }

    async savePatient(data) {
        if (data.id) {
            await api(`/api/patients/${data.id}`, { method: 'PUT', body: JSON.stringify(data) });
        } else {
            await api('/api/patients', { method: 'POST', body: JSON.stringify(data) });
        }
        this.setState({ showForm: null });
        this.loadPatients();
    }

    async saveVisit(patientId, data) {
        await api(`/api/patients/${patientId}/visits`, { method: 'POST', body: JSON.stringify(data) });
        this.setState({ showForm: null });
        this.selectPatient(patientId);
    }

    async saveVitals(patientId, data) {
        await api(`/api/patients/${patientId}/vitals`, { method: 'POST', body: JSON.stringify(data) });
        this.setState({ showForm: null });
        this.selectPatient(patientId);
    }

    async saveWound(patientId, data) {
        await api(`/api/patients/${patientId}/wounds`, { method: 'POST', body: JSON.stringify(data) });
        this.setState({ showForm: null });
        this.selectPatient(patientId);
    }

    async saveVaccination(patientId, data) {
        await api(`/api/patients/${patientId}/vaccinations`, { method: 'POST', body: JSON.stringify(data) });
        this.setState({ showForm: null });
        this.selectPatient(patientId);
    }

    renderTabs() {
        const tabs = ['patients', 'visits', 'vitals', 'wounds', 'vaccinations'];
        return html`<div class="tabs">${tabs.map(t =>
            html`<div class="tab ${this.state.tab === t ? 'active' : ''}"
                 onclick=${() => this.setState({ tab: t })}>${t.charAt(0).toUpperCase() + t.slice(1)}</div>`
        )}</div>`;
    }

    renderPatientList() {
        const { patients, searchQuery } = this.state;
        return html`
            <div class="search-bar">
                <input type="text" placeholder="Search patients..." value=${searchQuery}
                    onInput=${e => this.setState({ searchQuery: e.target.value })}
                    onKeyDown=${e => e.key === 'Enter' && this.loadPatients()} />
                <button class="btn btn-primary" onclick=${() => this.loadPatients()}>Search</button>
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'patient' })}>+ New Patient</button>
            </div>
            ${patients.length === 0 ? html`<div class="empty">No patients found</div>` : html`
            <table>
                <thead><tr><th>Name</th><th>DOB</th><th>Sex</th><th>Blood Type</th><th>ID</th></tr></thead>
                <tbody>${patients.map(p => html`
                    <tr onclick=${() => this.selectPatient(p.id)}>
                        <td>${p.last_name}, ${p.first_name}</td>
                        <td>${p.date_of_birth}</td>
                        <td>${p.sex}</td>
                        <td>${p.blood_type || '-'}</td>
                        <td>${p.patient_id}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderPatientDetail() {
        const { selectedPatient: p, visits, vitals, wounds, vaccinations, tab } = this.state;
        if (!p) return html`<div class="empty">Select a patient to view details</div>`;

        return html`
            <div class="detail-header">
                <div>
                    <button class="back-btn" onclick=${() => this.setState({ selectedPatient: null })}>< Back</button>
                    <h2>${p.first_name} ${p.last_name}</h2>
                </div>
                <a href="/api/patients/${p.id}/summary" target="_blank" class="btn btn-primary btn-sm">Print Summary</a>
            </div>
            <div class="info-grid">
                <div class="info-item"><label>Patient ID</label><span>${p.patient_id}</span></div>
                <div class="info-item"><label>DOB</label><span>${p.date_of_birth}</span></div>
                <div class="info-item"><label>Sex</label><span>${p.sex}</span></div>
                <div class="info-item"><label>Blood Type</label><span>${p.blood_type || 'N/A'}</span></div>
                <div class="info-item"><label>Emergency Contact</label><span>${p.emergency_contact || 'N/A'}</span></div>
            </div>
            <div style="margin-bottom:12px">
                <label style="font-size:0.7rem;color:#999">ALLERGIES</label>
                <div class="tags">${(p.allergies || []).length ? p.allergies.map(a => html`<span class="tag alert">${a}</span>`) : 'None known'}</div>
            </div>
            <div style="margin-bottom:12px">
                <label style="font-size:0.7rem;color:#999">CHRONIC CONDITIONS</label>
                <div class="tags">${(p.chronic_conditions || []).length ? p.chronic_conditions.map(c => html`<span class="tag">${c}</span>`) : 'None'}</div>
            </div>

            ${tab === 'visits' ? this.renderVisits(p.id, visits) : ''}
            ${tab === 'vitals' ? this.renderVitals(p.id, vitals) : ''}
            ${tab === 'wounds' ? this.renderWounds(p.id, wounds) : ''}
            ${tab === 'vaccinations' ? this.renderVaccinations(p.id, vaccinations) : ''}
            ${tab === 'patients' ? this.renderVisits(p.id, visits) : ''}
        `;
    }

    renderVisits(patientId, visits) {
        return html`
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'visit' })}>+ New Visit</button>
            </div>
            ${visits.length === 0 ? html`<div class="empty">No visits recorded</div>` : html`
            <div class="timeline">${visits.map(v => html`
                <div class="timeline-item">
                    <div class="date">${v.visit_date}</div>
                    <div class="provider">${v.provider}</div>
                    <div><strong>S:</strong> ${v.subjective || '-'}</div>
                    <div><strong>O:</strong> ${v.objective || '-'}</div>
                    <div><strong>A:</strong> ${v.assessment || '-'}</div>
                    <div><strong>P:</strong> ${v.plan || '-'}</div>
                    ${v.notes ? html`<div style="color:#999;margin-top:4px">${v.notes}</div>` : ''}
                </div>
            `)}</div>`}`;
    }

    renderVitals(patientId, vitals) {
        return html`
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'vitals' })}>+ Record Vitals</button>
            </div>
            ${vitals.length === 0 ? html`<div class="empty">No vitals recorded</div>` : html`
            <table>
                <thead><tr><th>Date</th><th>Temp</th><th>Pulse</th><th>BP</th><th>Resp</th><th>SpO2</th><th>Weight</th></tr></thead>
                <tbody>${vitals.map(v => html`
                    <tr>
                        <td>${v.recorded_at}</td>
                        <td>${v.temperature ?? '-'}</td>
                        <td>${v.pulse ?? '-'}</td>
                        <td>${v.bp_systolic ?? '-'}/${v.bp_diastolic ?? '-'}</td>
                        <td>${v.respiration_rate ?? '-'}</td>
                        <td>${v.spo2 ?? '-'}</td>
                        <td>${v.weight ?? '-'}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderWounds(patientId, wounds) {
        return html`
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'wound' })}>+ New Wound</button>
            </div>
            ${wounds.length === 0 ? html`<div class="empty">No wounds recorded</div>` : html`
            <table>
                <thead><tr><th>Location</th><th>Type</th><th>Size</th><th>Status</th><th>Date</th></tr></thead>
                <tbody>${wounds.map(w => html`
                    <tr>
                        <td>${w.body_location}</td>
                        <td>${w.wound_type}</td>
                        <td>${w.size || '-'}</td>
                        <td>${w.status}</td>
                        <td>${w.created_at}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderVaccinations(patientId, vaccinations) {
        return html`
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'vaccination' })}>+ Record Vaccination</button>
            </div>
            ${vaccinations.length === 0 ? html`<div class="empty">No vaccinations recorded</div>` : html`
            <table>
                <thead><tr><th>Vaccine</th><th>Date</th><th>Lot #</th><th>Site</th><th>By</th><th>Next Due</th></tr></thead>
                <tbody>${vaccinations.map(v => html`
                    <tr>
                        <td>${v.vaccine_name}</td>
                        <td>${v.date_administered}</td>
                        <td>${v.lot_number || '-'}</td>
                        <td>${v.site || '-'}</td>
                        <td>${v.administered_by || '-'}</td>
                        <td>${v.next_dose_due || '-'}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderFormModal() {
        const { showForm, selectedPatient } = this.state;
        if (!showForm) return '';

        const close = () => this.setState({ showForm: null });

        if (showForm === 'patient') return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>New Patient</h3>
                    <form onSubmit=${e => { e.preventDefault(); const fd = new FormData(e.target);
                        this.savePatient({
                            first_name: fd.get('first_name'), last_name: fd.get('last_name'),
                            date_of_birth: fd.get('dob'), sex: fd.get('sex'), blood_type: fd.get('blood_type'),
                            allergies: fd.get('allergies') ? fd.get('allergies').split(',').map(s=>s.trim()) : [],
                            chronic_conditions: fd.get('conditions') ? fd.get('conditions').split(',').map(s=>s.trim()) : [],
                            emergency_contact: fd.get('emergency_contact'),
                        });
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>First Name</label><input name="first_name" required /></div>
                            <div class="form-group"><label>Last Name</label><input name="last_name" required /></div>
                            <div class="form-group"><label>Date of Birth</label><input name="dob" type="date" required /></div>
                            <div class="form-group"><label>Sex</label><select name="sex"><option>M</option><option>F</option><option>Other</option></select></div>
                            <div class="form-group"><label>Blood Type</label><input name="blood_type" placeholder="e.g. O+" /></div>
                            <div class="form-group"><label>Emergency Contact</label><input name="emergency_contact" /></div>
                            <div class="form-group full"><label>Allergies (comma-separated)</label><input name="allergies" /></div>
                            <div class="form-group full"><label>Chronic Conditions (comma-separated)</label><input name="conditions" /></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Save</button></div>
                    </form>
                </div>
            </div>`;

        if (showForm === 'visit' && selectedPatient) return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>New SOAP Visit Note</h3>
                    <form onSubmit=${e => { e.preventDefault(); const fd = new FormData(e.target);
                        this.saveVisit(selectedPatient.id, {
                            provider: fd.get('provider'), visit_date: fd.get('visit_date') || undefined,
                            subjective: fd.get('subjective'), objective: fd.get('objective'),
                            assessment: fd.get('assessment'), plan: fd.get('plan'), notes: fd.get('notes'),
                        });
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>Provider</label><input name="provider" required /></div>
                            <div class="form-group"><label>Visit Date</label><input name="visit_date" type="datetime-local" /></div>
                            <div class="form-group full"><label>Subjective</label><textarea name="subjective" placeholder="Patient complaints..."></textarea></div>
                            <div class="form-group full"><label>Objective</label><textarea name="objective" placeholder="Exam findings..."></textarea></div>
                            <div class="form-group full"><label>Assessment</label><textarea name="assessment" placeholder="Diagnosis..."></textarea></div>
                            <div class="form-group full"><label>Plan</label><textarea name="plan" placeholder="Treatment plan..."></textarea></div>
                            <div class="form-group full"><label>Notes</label><textarea name="notes"></textarea></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Save</button></div>
                    </form>
                </div>
            </div>`;

        if (showForm === 'vitals' && selectedPatient) return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>Record Vital Signs</h3>
                    <form onSubmit=${e => { e.preventDefault(); const fd = new FormData(e.target);
                        const data = {};
                        ['temperature','pulse','bp_systolic','bp_diastolic','respiration_rate','spo2','weight'].forEach(k => {
                            const v = fd.get(k); if (v) data[k] = parseFloat(v);
                        });
                        this.saveVitals(selectedPatient.id, data);
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>Temperature (C)</label><input name="temperature" type="number" step="0.1" /></div>
                            <div class="form-group"><label>Pulse (bpm)</label><input name="pulse" type="number" /></div>
                            <div class="form-group"><label>BP Systolic</label><input name="bp_systolic" type="number" /></div>
                            <div class="form-group"><label>BP Diastolic</label><input name="bp_diastolic" type="number" /></div>
                            <div class="form-group"><label>Respiration Rate</label><input name="respiration_rate" type="number" /></div>
                            <div class="form-group"><label>SpO2 (%)</label><input name="spo2" type="number" step="0.1" /></div>
                            <div class="form-group"><label>Weight (kg)</label><input name="weight" type="number" step="0.1" /></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Save</button></div>
                    </form>
                </div>
            </div>`;

        if (showForm === 'wound' && selectedPatient) return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>New Wound Record</h3>
                    <form onSubmit=${e => { e.preventDefault(); const fd = new FormData(e.target);
                        this.saveWound(selectedPatient.id, {
                            body_location: fd.get('body_location'), wound_type: fd.get('wound_type'), size: fd.get('size'),
                        });
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>Body Location</label><input name="body_location" required /></div>
                            <div class="form-group"><label>Type</label><select name="wound_type">
                                <option>laceration</option><option>burn</option><option>puncture</option><option>abrasion</option><option>surgical</option><option>other</option>
                            </select></div>
                            <div class="form-group"><label>Size</label><input name="size" placeholder="e.g. 3cm x 1cm" /></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Save</button></div>
                    </form>
                </div>
            </div>`;

        if (showForm === 'vaccination' && selectedPatient) return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>Record Vaccination</h3>
                    <form onSubmit=${e => { e.preventDefault(); const fd = new FormData(e.target);
                        this.saveVaccination(selectedPatient.id, {
                            vaccine_name: fd.get('vaccine_name'), date_administered: fd.get('date_administered'),
                            lot_number: fd.get('lot_number'), site: fd.get('site'),
                            administered_by: fd.get('administered_by'), next_dose_due: fd.get('next_dose_due') || null,
                        });
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>Vaccine</label><input name="vaccine_name" required /></div>
                            <div class="form-group"><label>Date Administered</label><input name="date_administered" type="date" required /></div>
                            <div class="form-group"><label>Lot Number</label><input name="lot_number" /></div>
                            <div class="form-group"><label>Site</label><input name="site" placeholder="e.g. Left deltoid" /></div>
                            <div class="form-group"><label>Administered By</label><input name="administered_by" /></div>
                            <div class="form-group"><label>Next Dose Due</label><input name="next_dose_due" type="date" /></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Save</button></div>
                    </form>
                </div>
            </div>`;

        return '';
    }

    render() {
        const { health, selectedPatient } = this.state;
        return html`
            <header>
                <h1>EHR-Lite</h1>
                ${health ? html`<span class="health-badge">${health.status} v${health.version}</span>` : ''}
            </header>
            ${this.renderTabs()}
            <div class="panel">
                ${selectedPatient ? this.renderPatientDetail() : this.renderPatientList()}
            </div>
            ${this.renderFormModal()}
        `;
    }
}

render(html`<${App} />`, document.getElementById('app'));
