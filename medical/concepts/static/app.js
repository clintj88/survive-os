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
            tab: 'concepts', health: null,
            concepts: [], selectedConcept: null,
            sets: [], selectedSet: null,
            showForm: null, searchQuery: '', classFilter: '',
        };
    }

    componentDidMount() {
        api('/health').then(h => this.setState({ health: h }));
        this.loadConcepts();
        this.loadSets();
    }

    async loadConcepts() {
        const { searchQuery, classFilter } = this.state;
        const params = new URLSearchParams();
        if (searchQuery) params.set('q', searchQuery);
        if (classFilter) params.set('class', classFilter);
        const qs = params.toString();
        const url = qs ? `/api/concepts/search?${qs}` : '/api/concepts';
        this.setState({ concepts: await api(url) });
    }

    async loadSets() {
        this.setState({ sets: await api('/api/sets') });
    }

    async selectConcept(id) {
        const c = await api(`/api/concepts/${id}`);
        this.setState({ selectedConcept: c });
    }

    async selectSet(id) {
        const s = await api(`/api/sets/${id}`);
        this.setState({ selectedSet: s });
    }

    async saveConcept(data) {
        await api('/api/concepts', { method: 'POST', body: JSON.stringify(data) });
        this.setState({ showForm: null });
        this.loadConcepts();
    }

    async saveSet(data) {
        await api('/api/sets', { method: 'POST', body: JSON.stringify(data) });
        this.setState({ showForm: null });
        this.loadSets();
    }

    async retireConcept(id) {
        await api(`/api/concepts/${id}/retire`, { method: 'POST' });
        this.selectConcept(id);
        this.loadConcepts();
    }

    async unretireConcept(id) {
        await api(`/api/concepts/${id}/unretire`, { method: 'POST' });
        this.selectConcept(id);
        this.loadConcepts();
    }

    renderTabs() {
        const tabs = ['concepts', 'sets'];
        return html`<div class="tabs">${tabs.map(t =>
            html`<div class="tab ${this.state.tab === t ? 'active' : ''}"
                 onclick=${() => this.setState({ tab: t, selectedConcept: null, selectedSet: null })}>${t.charAt(0).toUpperCase() + t.slice(1)}</div>`
        )}</div>`;
    }

    renderConceptList() {
        const { concepts, searchQuery, classFilter } = this.state;
        return html`
            <div class="search-bar">
                <input type="text" placeholder="Search concepts..." value=${searchQuery}
                    onInput=${e => this.setState({ searchQuery: e.target.value })}
                    onKeyDown=${e => e.key === 'Enter' && this.loadConcepts()} />
                <select value=${classFilter} onChange=${e => { this.setState({ classFilter: e.target.value }); setTimeout(() => this.loadConcepts(), 0); }}>
                    <option value="">All Classes</option>
                    <option value="diagnosis">Diagnosis</option>
                    <option value="symptom">Symptom</option>
                    <option value="test">Test</option>
                    <option value="drug">Drug</option>
                    <option value="procedure">Procedure</option>
                    <option value="finding">Finding</option>
                    <option value="misc">Misc</option>
                </select>
                <button class="btn btn-primary" onclick=${() => this.loadConcepts()}>Search</button>
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'concept' })}>+ New Concept</button>
            </div>
            ${concepts.length === 0 ? html`<div class="empty">No concepts found</div>` : html`
            <table>
                <thead><tr><th>Name</th><th>Datatype</th><th>Class</th><th>Units</th><th>Status</th></tr></thead>
                <tbody>${concepts.map(c => html`
                    <tr onclick=${() => this.selectConcept(c.id)}>
                        <td>${c.name}</td>
                        <td>${c.datatype}</td>
                        <td>${c.concept_class}</td>
                        <td>${c.units || '-'}</td>
                        <td>${c.retired ? html`<span class="tag retired">Retired</span>` : 'Active'}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderConceptDetail() {
        const { selectedConcept: c } = this.state;
        if (!c) return '';
        return html`
            <div class="detail-header">
                <div>
                    <button class="back-btn" onclick=${() => this.setState({ selectedConcept: null })}>< Back</button>
                    <h2>${c.name} ${c.retired ? html`<span class="tag retired">Retired</span>` : ''}</h2>
                </div>
                <div class="actions">
                    ${c.retired
                        ? html`<button class="btn btn-primary btn-sm" onclick=${() => this.unretireConcept(c.id)}>Unretire</button>`
                        : html`<button class="btn btn-danger btn-sm" onclick=${() => this.retireConcept(c.id)}>Retire</button>`}
                </div>
            </div>
            <div class="info-grid">
                <div class="info-item"><label>Short Name</label><span>${c.short_name || '-'}</span></div>
                <div class="info-item"><label>Datatype</label><span>${c.datatype}</span></div>
                <div class="info-item"><label>Class</label><span>${c.concept_class}</span></div>
                <div class="info-item"><label>Units</label><span>${c.units || '-'}</span></div>
                <div class="info-item"><label>Description</label><span>${c.description || '-'}</span></div>
            </div>
            ${c.answers && c.answers.length > 0 ? html`
                <h3 style="margin:12px 0 8px;font-size:0.9rem;color:#999">Answers</h3>
                <table>
                    <thead><tr><th>Answer Concept ID</th><th>Sort Order</th></tr></thead>
                    <tbody>${c.answers.map(a => html`
                        <tr><td>${a.answer_concept_id}</td><td>${a.sort_order}</td></tr>
                    `)}</tbody>
                </table>` : ''}
            ${c.mappings && c.mappings.length > 0 ? html`
                <h3 style="margin:12px 0 8px;font-size:0.9rem;color:#999">Mappings</h3>
                <table>
                    <thead><tr><th>Source</th><th>Code</th><th>Name</th></tr></thead>
                    <tbody>${c.mappings.map(m => html`
                        <tr><td>${m.source}</td><td>${m.code}</td><td>${m.name || '-'}</td></tr>
                    `)}</tbody>
                </table>` : ''}
        `;
    }

    renderSetList() {
        const { sets } = this.state;
        return html`
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'set' })}>+ New Set</button>
            </div>
            ${sets.length === 0 ? html`<div class="empty">No concept sets defined</div>` : html`
            <table>
                <thead><tr><th>Name</th><th>Description</th></tr></thead>
                <tbody>${sets.map(s => html`
                    <tr onclick=${() => this.selectSet(s.id)}>
                        <td>${s.name}</td>
                        <td>${s.description || '-'}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderSetDetail() {
        const { selectedSet: s } = this.state;
        if (!s) return '';
        return html`
            <div class="detail-header">
                <button class="back-btn" onclick=${() => this.setState({ selectedSet: null })}>< Back</button>
                <h2>${s.name}</h2>
            </div>
            <p style="margin-bottom:12px;color:#999">${s.description || ''}</p>
            ${s.members && s.members.length > 0 ? html`
            <table>
                <thead><tr><th>Concept</th><th>Datatype</th><th>Class</th><th>Order</th></tr></thead>
                <tbody>${s.members.map(m => html`
                    <tr onclick=${() => { this.setState({ tab: 'concepts' }); this.selectConcept(m.concept_id); }}>
                        <td>${m.concept_name}</td>
                        <td>${m.datatype}</td>
                        <td>${m.concept_class}</td>
                        <td>${m.sort_order}</td>
                    </tr>
                `)}</tbody>
            </table>` : html`<div class="empty">No members in this set</div>`}`;
    }

    renderFormModal() {
        const { showForm } = this.state;
        if (!showForm) return '';
        const close = () => this.setState({ showForm: null });

        if (showForm === 'concept') return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>New Concept</h3>
                    <form onSubmit=${e => { e.preventDefault(); const fd = new FormData(e.target);
                        this.saveConcept({
                            name: fd.get('name'), short_name: fd.get('short_name'),
                            datatype: fd.get('datatype'), concept_class: fd.get('concept_class'),
                            description: fd.get('description'), units: fd.get('units'),
                        });
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>Name</label><input name="name" required /></div>
                            <div class="form-group"><label>Short Name</label><input name="short_name" /></div>
                            <div class="form-group"><label>Datatype</label><select name="datatype">
                                <option>numeric</option><option>coded</option><option>text</option><option>boolean</option><option>date</option><option>datetime</option>
                            </select></div>
                            <div class="form-group"><label>Class</label><select name="concept_class">
                                <option>diagnosis</option><option>symptom</option><option>test</option><option>drug</option><option>procedure</option><option>finding</option><option>misc</option>
                            </select></div>
                            <div class="form-group"><label>Units</label><input name="units" /></div>
                            <div class="form-group full"><label>Description</label><textarea name="description"></textarea></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Save</button></div>
                    </form>
                </div>
            </div>`;

        if (showForm === 'set') return html`
            <div class="modal-overlay" onclick=${e => e.target === e.currentTarget && close()}>
                <div class="modal">
                    <h3>New Concept Set</h3>
                    <form onSubmit=${e => { e.preventDefault(); const fd = new FormData(e.target);
                        this.saveSet({ name: fd.get('name'), description: fd.get('description') });
                    }}>
                        <div class="form-grid">
                            <div class="form-group"><label>Name</label><input name="name" required /></div>
                            <div class="form-group full"><label>Description</label><textarea name="description"></textarea></div>
                        </div>
                        <div class="modal-actions"><button type="button" class="btn" onclick=${close}>Cancel</button><button type="submit" class="btn btn-primary">Save</button></div>
                    </form>
                </div>
            </div>`;

        return '';
    }

    render() {
        const { health, tab, selectedConcept, selectedSet } = this.state;
        return html`
            <header>
                <h1>Clinical Concepts</h1>
                ${health ? html`<span class="health-badge">${health.status} v${health.version}</span>` : ''}
            </header>
            ${this.renderTabs()}
            <div class="panel">
                ${tab === 'concepts' ? (selectedConcept ? this.renderConceptDetail() : this.renderConceptList()) : ''}
                ${tab === 'sets' ? (selectedSet ? this.renderSetDetail() : this.renderSetList()) : ''}
            </div>
            ${this.renderFormModal()}
        `;
    }
}

render(html`<${App} />`, document.getElementById('app'));
