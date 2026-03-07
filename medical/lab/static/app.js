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
            tab: 'catalog', health: null,
            catalog: [], panels: [], orders: [], alerts: [],
            showForm: null,
        };
    }

    componentDidMount() {
        api('/health').then(h => this.setState({ health: h }));
        this.loadCatalog();
    }

    async loadCatalog() { this.setState({ catalog: await api('/api/catalog') }); }
    async loadPanels() { this.setState({ panels: await api('/api/panels') }); }
    async loadOrders() { this.setState({ orders: await api('/api/orders') }); }
    async loadAlerts() { this.setState({ alerts: await api('/api/results/alerts') }); }

    switchTab(tab) {
        this.setState({ tab });
        if (tab === 'catalog') this.loadCatalog();
        if (tab === 'panels') this.loadPanels();
        if (tab === 'orders') this.loadOrders();
        if (tab === 'alerts') this.loadAlerts();
    }

    renderTabs() {
        const tabs = ['catalog', 'panels', 'orders', 'alerts'];
        return html`<div class="tabs">${tabs.map(t =>
            html`<div class="tab ${this.state.tab === t ? 'active' : ''}"
                 onclick=${() => this.switchTab(t)}>${t.charAt(0).toUpperCase() + t.slice(1)}</div>`
        )}</div>`;
    }

    renderCatalog() {
        const { catalog } = this.state;
        return html`
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'test' })}>+ New Test</button>
            </div>
            ${catalog.length === 0 ? html`<div class="empty">No tests in catalog</div>` : html`
            <table>
                <thead><tr><th>Name</th><th>Specimen</th><th>Ref Range</th><th>Units</th><th>TAT</th><th>Active</th></tr></thead>
                <tbody>${catalog.map(t => html`
                    <tr>
                        <td>${t.name}</td>
                        <td>${t.specimen_type}</td>
                        <td>${t.ref_range_min != null ? t.ref_range_min + ' - ' + t.ref_range_max : '-'}</td>
                        <td>${t.units || '-'}</td>
                        <td>${t.turnaround_hours}h</td>
                        <td>${t.active ? 'Yes' : 'No'}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderPanels() {
        const { panels } = this.state;
        return html`
            ${panels.length === 0 ? html`<div class="empty">No panels defined</div>` : html`
            <table>
                <thead><tr><th>Panel</th><th>Description</th><th>Tests</th></tr></thead>
                <tbody>${panels.map(p => html`
                    <tr>
                        <td>${p.name}</td>
                        <td>${p.description}</td>
                        <td>${(p.tests || []).map(t => t.name).join(', ')}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderOrders() {
        const { orders } = this.state;
        return html`
            <div class="actions">
                <button class="btn btn-primary" onclick=${() => this.setState({ showForm: 'order' })}>+ New Order</button>
            </div>
            ${orders.length === 0 ? html`<div class="empty">No orders</div>` : html`
            <table>
                <thead><tr><th>ID</th><th>Patient</th><th>Test</th><th>Priority</th><th>Status</th><th>Ordered</th></tr></thead>
                <tbody>${orders.map(o => html`
                    <tr>
                        <td>${o.id}</td>
                        <td>${o.patient_id}</td>
                        <td>${o.test_id || 'Panel'}</td>
                        <td>${o.priority}</td>
                        <td><span class="status-badge status-${o.status}">${o.status}</span></td>
                        <td>${o.ordered_at}</td>
                    </tr>
                `)}</tbody>
            </table>`}`;
    }

    renderAlerts() {
        const { alerts } = this.state;
        return html`
            ${alerts.length === 0 ? html`<div class="empty">No abnormal results</div>` : html`
            <div class="alert-box">
                ${alerts.map(a => html`
                    <div class="alert-item">
                        <strong>${a.test_name}</strong> - Patient ${a.patient_id}:
                        ${a.numeric_value} ${a.units} (${a.interpretation})
                    </div>
                `)}
            </div>`}`;
    }

    render() {
        const { health, tab } = this.state;
        return html`
            <header>
                <h1>Lab Results</h1>
                ${health ? html`<span class="health-badge">${health.status} v${health.version}</span>` : ''}
            </header>
            ${this.renderTabs()}
            <div class="panel">
                ${tab === 'catalog' ? this.renderCatalog() : ''}
                ${tab === 'panels' ? this.renderPanels() : ''}
                ${tab === 'orders' ? this.renderOrders() : ''}
                ${tab === 'alerts' ? this.renderAlerts() : ''}
            </div>
        `;
    }
}

render(html`<${App} />`, document.getElementById('app'));
