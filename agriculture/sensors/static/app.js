import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect } from 'https://esm.sh/preact@10.19.3/hooks';
import { html } from 'https://esm.sh/htm@3.1.1/preact';

const REFRESH_INTERVAL = 30000;

function App() {
    const [tab, setTab] = useState('dashboard');
    const [dashboard, setDashboard] = useState(null);
    const [nodes, setNodes] = useState([]);
    const [soilData, setSoilData] = useState([]);
    const [weatherData, setWeatherData] = useState([]);
    const [alerts, setAlerts] = useState([]);

    const fetchData = async () => {
        try {
            const [dashRes, nodesRes, soilRes, wxRes, alertRes] = await Promise.all([
                fetch('/api/dashboard').then(r => r.json()),
                fetch('/api/nodes').then(r => r.json()),
                fetch('/api/readings/soil?limit=100').then(r => r.json()),
                fetch('/api/readings/weather?limit=100').then(r => r.json()),
                fetch('/api/alerts/frost').then(r => r.json()),
            ]);
            setDashboard(dashRes);
            setNodes(nodesRes);
            setSoilData(soilRes);
            setWeatherData(wxRes);
            setAlerts(alertRes);
        } catch (e) {
            console.error('Fetch error:', e);
        }
    };

    useEffect(() => {
        fetchData();
        const id = setInterval(fetchData, REFRESH_INTERVAL);
        return () => clearInterval(id);
    }, []);

    useEffect(() => {
        document.querySelectorAll('.tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
            btn.onclick = () => setTab(btn.dataset.tab);
        });
    }, [tab]);

    if (!dashboard) return html`<div class="empty">Loading...</div>`;

    return html`
        <div class="refresh-note">Auto-refresh every 30s</div>
        ${tab === 'dashboard' && html`<${Dashboard} data=${dashboard} nodes=${nodes} alerts=${alerts} />`}
        ${tab === 'nodes' && html`<${Nodes} nodes=${nodes} />`}
        ${tab === 'soil' && html`<${Soil} data=${soilData} />`}
        ${tab === 'weather' && html`<${Weather} data=${weatherData} />`}
        ${tab === 'alerts' && html`<${Alerts} alerts=${alerts} />`}
    `;
}

function Dashboard({ data, nodes, alerts }) {
    const onlineCount = nodes.filter(n => n.status === 'online').length;
    const offlineCount = nodes.filter(n => n.status === 'offline').length;
    const lowBattery = nodes.filter(n => n.battery_level != null && n.battery_level < 20).length;
    const latestTemp = data.weather?.[0]?.temperature_c;
    const latestHumidity = data.weather?.[0]?.humidity_pct;
    const latestMoisture = data.soil?.[0]?.moisture_pct;
    const activeAlerts = alerts.filter(a => {
        const d = new Date(a.created_at);
        return (Date.now() - d.getTime()) < 3600000;
    });

    return html`
        <h2 class="section-title">Overview</h2>
        <div class="cards">
            <div class="card">
                <h3>Nodes Online</h3>
                <div class="value status-online">${onlineCount}</div>
                <div class="meta">${offlineCount} offline${lowBattery ? `, ${lowBattery} low battery` : ''}</div>
            </div>
            <div class="card">
                <h3>Temperature</h3>
                <div class="value">${latestTemp != null ? latestTemp.toFixed(1) : '--'}<span class="unit">°C</span></div>
                <div class="meta">${data.weather?.[0]?.node_name || ''} - ${data.weather?.[0]?.location || ''}</div>
            </div>
            <div class="card">
                <h3>Humidity</h3>
                <div class="value">${latestHumidity != null ? latestHumidity.toFixed(0) : '--'}<span class="unit">%</span></div>
            </div>
            <div class="card">
                <h3>Soil Moisture</h3>
                <div class="value">${latestMoisture != null ? latestMoisture.toFixed(1) : '--'}<span class="unit">%</span></div>
                <div class="meta">${data.soil?.[0]?.location || ''}</div>
            </div>
            <div class="card">
                <h3>Frost Alerts</h3>
                <div class="value ${activeAlerts.length > 0 ? 'status-offline' : 'status-online'}">${activeAlerts.length}</div>
                <div class="meta">active in last hour</div>
            </div>
        </div>

        ${data.weather?.length > 0 && html`
            <h2 class="section-title">Latest Weather Readings</h2>
            <table>
                <thead><tr><th>Node</th><th>Location</th><th>Temp</th><th>Humidity</th><th>Pressure</th><th>Time</th></tr></thead>
                <tbody>
                    ${data.weather.map(r => html`
                        <tr>
                            <td>${r.node_name}</td><td>${r.location}</td>
                            <td>${r.temperature_c?.toFixed(1)}°C</td>
                            <td>${r.humidity_pct?.toFixed(0)}%</td>
                            <td>${r.pressure_hpa?.toFixed(1)} hPa</td>
                            <td>${new Date(r.timestamp).toLocaleString()}</td>
                        </tr>
                    `)}
                </tbody>
            </table>
        `}
    `;
}

function Nodes({ nodes }) {
    if (!nodes.length) return html`<div class="empty">No sensor nodes registered</div>`;
    return html`
        <h2 class="section-title">Sensor Nodes</h2>
        <table>
            <thead><tr><th>ID</th><th>Name</th><th>Location</th><th>Type</th><th>Status</th><th>Battery</th><th>Last Seen</th></tr></thead>
            <tbody>
                ${nodes.map(n => html`
                    <tr>
                        <td>${n.node_id}</td><td>${n.name}</td><td>${n.location}</td><td>${n.type}</td>
                        <td class="status-${n.status}">${n.status}</td>
                        <td class="${n.battery_level != null && n.battery_level < 20 ? 'status-low-battery' : ''}">
                            ${n.battery_level != null ? n.battery_level.toFixed(0) + '%' : '--'}
                        </td>
                        <td>${n.last_seen ? new Date(n.last_seen).toLocaleString() : '--'}</td>
                    </tr>
                `)}
            </tbody>
        </table>
    `;
}

function Soil({ data }) {
    if (!data.length) return html`<div class="empty">No soil readings yet</div>`;
    return html`
        <h2 class="section-title">Soil Moisture Readings</h2>
        <table>
            <thead><tr><th>Node</th><th>Moisture</th><th>Depth</th><th>Temp</th><th>Time</th></tr></thead>
            <tbody>
                ${data.map(r => html`
                    <tr>
                        <td>${r.node_id}</td>
                        <td>${r.moisture_pct?.toFixed(1)}%</td>
                        <td>${r.depth_cm != null ? r.depth_cm + ' cm' : '--'}</td>
                        <td>${r.temperature_c != null ? r.temperature_c.toFixed(1) + '°C' : '--'}</td>
                        <td>${new Date(r.timestamp).toLocaleString()}</td>
                    </tr>
                `)}
            </tbody>
        </table>
    `;
}

function Weather({ data }) {
    if (!data.length) return html`<div class="empty">No weather readings yet</div>`;
    return html`
        <h2 class="section-title">Weather Readings</h2>
        <table>
            <thead><tr><th>Node</th><th>Temp</th><th>Humidity</th><th>Pressure</th><th>Time</th></tr></thead>
            <tbody>
                ${data.map(r => html`
                    <tr>
                        <td>${r.node_id}</td>
                        <td>${r.temperature_c?.toFixed(1)}°C</td>
                        <td>${r.humidity_pct?.toFixed(0)}%</td>
                        <td>${r.pressure_hpa?.toFixed(1)} hPa</td>
                        <td>${new Date(r.timestamp).toLocaleString()}</td>
                    </tr>
                `)}
            </tbody>
        </table>
    `;
}

function Alerts({ alerts }) {
    if (!alerts.length) return html`<div class="empty">No frost alerts recorded</div>`;
    return html`
        <h2 class="section-title">Frost Alert History</h2>
        <table>
            <thead><tr><th>Status</th><th>Node</th><th>Location</th><th>Temperature</th><th>Trend</th><th>Time</th></tr></thead>
            <tbody>
                ${alerts.map(a => html`
                    <tr class="alert-row">
                        <td><span class="alert-badge">FROST</span></td>
                        <td>${a.node_id}</td>
                        <td>${a.location}</td>
                        <td>${a.temperature_c.toFixed(1)}°C</td>
                        <td class="trend-${a.trend}">${a.trend}</td>
                        <td>${new Date(a.created_at).toLocaleString()}</td>
                    </tr>
                `)}
            </tbody>
        </table>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
