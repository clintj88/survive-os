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
            tab: 'dashboard', health: null,
            dashboard: [], programs: [], enrollments: [],
            selectedProgram: null, selectedEnrollment: null,
            showForm: null, error: null,
        };
    }

    componentDidMount() {
        api('/health').then(h => this.setState({ health: h }));
        this.loadDashboard();
        this.loadPrograms();
    }

    async loadDashboard() {
        try {
            this.setState({ dashboard: await api('/api/programs/dashboard') });
        } catch (e) { this.setState({ error: e.message }); }
    }

    async loadPrograms() {
        try {
            this.setState({ programs: await api('/api/programs') });
        } catch (e) { this.setState({ error: e.message }); }
    }

    async loadEnrollments(programId) {
        try {
            this.setState({ enrollments: await api(`/api/programs/${programId}/enrollments`) });
        } catch (e) { this.setState({ error: e.message }); }
    }

    async selectProgram(id) {
        const prog = await api(`/api/programs/${id}`);
        const workflows = await api(`/api/workflows?program_id=${id}`);
        const enrollments = await api(`/api/programs/${id}/enrollments`);
        prog.workflows = workflows;
        this.setState({ selectedProgram: prog, enrollments, tab: 'programs' });
    }

    renderTabs() {
        const tabs = ['dashboard', 'programs', 'enrollments'];
        return html`<div class="tabs">${tabs.map(t =>
            html`<div class="tab ${this.state.tab === t ? 'active' : ''}"
                 onclick=${() => this.setState({ tab: t })}>${t.charAt(0).toUpperCase() + t.slice(1)}</div>`
        )}</div>`;
    }

    renderDashboard() {
        const { dashboard } = this.state;
        if (!dashboard.length) return html`<div class="empty">No active programs</div>`;
        return html`
            ${dashboard.map(d => html`
                <div class="dashboard-card" onclick=${() => this.selectProgram(d.program_id)}>
                    <h3>${d.program_name}</h3>
                    <div class="count">${d.active_enrollments} active</div>
                    <div class="state-flow">
                        ${Object.entries(d.states || {}).map(([name, count]) => html`
                            <span class="state-badge">${name}: ${count}</span>
                        `)}
                    </div>
                </div>
            `)}
        `;
    }

    renderPrograms() {
        const { programs, selectedProgram } = this.state;
        if (selectedProgram) return this.renderProgramDetail();
        return html`
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'program' })}>+ New Program</button>
            </div>
            ${programs.length === 0 ? html`<div class="empty">No programs defined</div>` : html`
            <table>
                <thead><tr><th>Name</th><th>Description</th><th>Status</th></tr></thead>
                <tbody>${programs.map(p => html`
                    <tr onclick=${() => this.selectProgram(p.id)}>
                        <td>${p.name}</td>
                        <td>${p.description}</td>
                        <td><span class="tag ${p.active ? 'active' : ''}">${p.active ? 'Active' : 'Inactive'}</span></td>
                    </tr>
                `)}</tbody>
            </table>`}
        `;
    }

    renderProgramDetail() {
        const { selectedProgram: p, enrollments } = this.state;
        return html`
            <div style="margin-bottom:12px">
                <button class="btn btn-sm" onclick=${() => this.setState({ selectedProgram: null })}>Back</button>
            </div>
            <h2 style="color:#4fc3f7;margin-bottom:8px">${p.name}</h2>
            <p style="color:#999;margin-bottom:16px">${p.description}</p>
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'enroll' })}>+ Enroll Patient</button>
            </div>
            <h3 style="margin:16px 0 8px;font-size:0.9rem">Active Enrollments</h3>
            ${enrollments.length === 0 ? html`<div class="empty">No enrollments</div>` : html`
            <table>
                <thead><tr><th>Patient</th><th>Enrolled</th><th>State</th><th>Outcome</th></tr></thead>
                <tbody>${enrollments.map(e => html`
                    <tr>
                        <td>${e.patient_id}</td>
                        <td>${e.enrollment_date}</td>
                        <td><span class="state-badge current">${e.current_state || '-'}</span></td>
                        <td><span class="tag ${e.outcome === 'active' ? 'active' : 'completed'}">${e.outcome}</span></td>
                    </tr>
                `)}</tbody>
            </table>`}
        `;
    }

    renderEnrollments() {
        const { enrollments } = this.state;
        return html`
            ${enrollments.length === 0 ? html`<div class="empty">Select a program to view enrollments</div>` : html`
            <table>
                <thead><tr><th>Patient</th><th>Program</th><th>Enrolled</th><th>State</th><th>Outcome</th></tr></thead>
                <tbody>${enrollments.map(e => html`
                    <tr>
                        <td>${e.patient_id}</td>
                        <td>${e.program_id}</td>
                        <td>${e.enrollment_date}</td>
                        <td>${e.current_state || '-'}</td>
                        <td>${e.outcome}</td>
                    </tr>
                `)}</tbody>
            </table>`}
        `;
    }

    renderFormModal() {
        const { showForm, selectedProgram } = this.state;
        if (!showForm) return '';
        const close = () => this.setState({ showForm: null });

        if (showForm === 'program') return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>New Program</h3>
                    <form onSubmit=${async e => { e.preventDefault(); const fd = new FormData(e.target);
                        await api('/api/programs', { method: 'POST', body: JSON.stringify({
                            name: fd.get('name'), description: fd.get('description'),
                        })});
                        close(); this.loadPrograms(); this.loadDashboard();
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>Name</label><input name="name" required /></div>
                            <div class="form-group full"><label>Description</label><input name="description" /></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Save</button></div>
                    </form>
                </div>
            </div>`;

        if (showForm === 'enroll' && selectedProgram) return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>Enroll Patient in ${selectedProgram.name}</h3>
                    <form onSubmit=${async e => { e.preventDefault(); const fd = new FormData(e.target);
                        await api('/api/enrollments', { method: 'POST', body: JSON.stringify({
                            patient_id: fd.get('patient_id'), program_id: selectedProgram.id,
                            enrolled_by: fd.get('enrolled_by'),
                        })});
                        close(); this.loadEnrollments(selectedProgram.id); this.loadDashboard();
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>Patient ID</label><input name="patient_id" required /></div>
                            <div class="form-group"><label>Enrolled By</label><input name="enrolled_by" required /></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Enroll</button></div>
                    </form>
                </div>
            </div>`;

        return '';
    }

    render() {
        const { health, tab } = this.state;
        return html`
            <header>
                <h1>Program Enrollment</h1>
                ${health ? html`<span class="health-badge">${health.status} v${health.version}</span>` : ''}
            </header>
            ${this.renderTabs()}
            <div class="panel">
                ${tab === 'dashboard' ? this.renderDashboard() : ''}
                ${tab === 'programs' ? this.renderPrograms() : ''}
                ${tab === 'enrollments' ? this.renderEnrollments() : ''}
            </div>
            ${this.renderFormModal()}
        `;
    }
}

render(html`<${App} />`, document.getElementById('app'));
