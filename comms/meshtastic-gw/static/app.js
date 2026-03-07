import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

async function fetchJSON(url, opts) {
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

function StatusBar({ status }) {
    if (!status) return html`<div class="status-bar loading">Loading...</div>`;
    const connected = status.radio_connected;
    return html`
        <div class="status-bar ${connected ? 'connected' : 'disconnected'}">
            <span class="status-dot"></span>
            Radio: ${connected ? 'Connected' : 'Disconnected'}
            (${status.connection_type} - ${status.serial_port || status.ble_address})
            | Messages: ${status.message_count} | Nodes: ${status.node_count}
        </div>
    `;
}

function MessageList({ messages }) {
    if (!messages.length) return html`<p class="empty">No messages yet.</p>`;
    return html`
        <div class="message-list">
            ${messages.map(m => html`
                <div class="message ${m.direction}">
                    <div class="message-header">
                        <span class="sender">${m.sender}</span>
                        <span class="direction-badge">${m.direction.toUpperCase()}</span>
                        <span class="channel">CH${m.channel}</span>
                        <span class="timestamp">${new Date(m.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="message-content">${m.content}</div>
                    ${m.recipient !== '^all' ? html`<div class="recipient">To: ${m.recipient}</div>` : null}
                </div>
            `)}
        </div>
    `;
}

function SendForm({ onSend }) {
    const [content, setContent] = useState('');
    const [recipient, setRecipient] = useState('^all');
    const [channel, setChannel] = useState(0);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!content.trim()) return;
        await onSend({ content, recipient, channel });
        setContent('');
    };

    return html`
        <form class="send-form" onSubmit=${handleSubmit}>
            <div class="send-inputs">
                <input type="text" value=${content} onInput=${e => setContent(e.target.value)}
                       placeholder="Type a message..." class="message-input" />
                <input type="text" value=${recipient} onInput=${e => setRecipient(e.target.value)}
                       placeholder="Recipient" class="recipient-input" title="Recipient (^all for broadcast)" />
                <input type="number" value=${channel} onInput=${e => setChannel(parseInt(e.target.value) || 0)}
                       min="0" max="7" class="channel-input" title="Channel" />
                <button type="submit">Send</button>
            </div>
        </form>
    `;
}

function RadioList({ radios, users, onAssign, onScan }) {
    return html`
        <div class="radio-section">
            <div class="section-header">
                <h3>Known Radios</h3>
                <button onClick=${onScan} class="scan-btn">Scan</button>
            </div>
            ${radios.length === 0 ? html`<p class="empty">No radios found. Click Scan to discover.</p>` : null}
            <div class="radio-grid">
                ${radios.map(r => html`
                    <div class="radio-card">
                        <div class="radio-header">
                            <strong>${r.long_name || r.node_id}</strong>
                            <span class="hw-model">${r.hw_model}</span>
                        </div>
                        <div class="radio-details">
                            <span>ID: ${r.node_id}</span>
                            <span>Battery: ${r.battery_level}%</span>
                            <span>SNR: ${r.snr}dB</span>
                            <span>Last seen: ${r.last_seen ? new Date(r.last_seen).toLocaleString() : 'Never'}</span>
                        </div>
                        <div class="radio-assign">
                            <select onChange=${e => onAssign(r.node_id, e.target.value)}
                                    value=${r.assigned_user || ''}>
                                <option value="">Unassigned</option>
                                ${users.map(u => html`<option value=${u.name}>${u.name}</option>`)}
                            </select>
                        </div>
                    </div>
                `)}
            </div>
        </div>
    `;
}

function Topology({ nodes }) {
    if (!nodes.length) return html`<p class="empty">No topology data available.</p>`;
    return html`
        <div class="topology">
            <h3>Mesh Topology</h3>
            <div class="topology-grid">
                ${nodes.map(n => html`
                    <div class="topo-node">
                        <div class="topo-name">${n.long_name || n.short_name || n.node_id}</div>
                        <div class="topo-stats">
                            SNR: ${n.snr}dB | Bat: ${n.battery_level}%
                        </div>
                        ${n.latitude && n.longitude ? html`
                            <div class="topo-coords">${n.latitude.toFixed(4)}, ${n.longitude.toFixed(4)}</div>
                        ` : null}
                    </div>
                `)}
            </div>
        </div>
    `;
}

function App() {
    const [tab, setTab] = useState('messages');
    const [status, setStatus] = useState(null);
    const [messages, setMessages] = useState([]);
    const [radios, setRadios] = useState([]);
    const [users, setUsers] = useState([]);
    const [topology, setTopology] = useState({ nodes: [] });

    const refresh = useCallback(async () => {
        try {
            const s = await fetchJSON('/api/status');
            setStatus(s);
        } catch (e) { console.error('Status fetch failed:', e); }

        if (tab === 'messages') {
            try {
                const m = await fetchJSON('/api/messages?limit=100');
                setMessages(m);
            } catch (e) { console.error('Messages fetch failed:', e); }
        }
    }, [tab]);

    useEffect(() => {
        refresh();
        const interval = setInterval(refresh, 5000);
        return () => clearInterval(interval);
    }, [refresh]);

    useEffect(() => {
        if (tab === 'radios') {
            fetchJSON('/api/provisioning/radios').then(setRadios).catch(() => {});
            fetchJSON('/api/provisioning/users').then(setUsers).catch(() => setUsers([]));
        } else if (tab === 'topology') {
            fetchJSON('/api/provisioning/topology').then(setTopology).catch(() => {});
        }
    }, [tab]);

    const sendMessage = async (msg) => {
        try {
            await fetchJSON('/api/messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(msg),
            });
            refresh();
        } catch (e) { console.error('Send failed:', e); }
    };

    const scanRadios = async () => {
        try {
            const r = await fetchJSON('/api/provisioning/radios/scan');
            setRadios(r);
        } catch (e) { console.error('Scan failed:', e); }
    };

    const assignRadio = async (nodeId, user) => {
        try {
            await fetchJSON('/api/provisioning/radios/assign', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ node_id: nodeId, user }),
            });
            const r = await fetchJSON('/api/provisioning/radios');
            setRadios(r);
        } catch (e) { console.error('Assign failed:', e); }
    };

    return html`
        <div class="container">
            <header>
                <h1>Meshtastic Gateway</h1>
                <nav class="tabs">
                    <button class=${tab === 'messages' ? 'active' : ''} onClick=${() => setTab('messages')}>Messages</button>
                    <button class=${tab === 'radios' ? 'active' : ''} onClick=${() => setTab('radios')}>Radios</button>
                    <button class=${tab === 'topology' ? 'active' : ''} onClick=${() => setTab('topology')}>Topology</button>
                </nav>
            </header>
            <${StatusBar} status=${status} />
            <main>
                ${tab === 'messages' && html`
                    <${SendForm} onSend=${sendMessage} />
                    <${MessageList} messages=${messages} />
                `}
                ${tab === 'radios' && html`
                    <${RadioList} radios=${radios} users=${users}
                                  onAssign=${assignRadio} onScan=${scanRadios} />
                `}
                ${tab === 'topology' && html`
                    <${Topology} nodes=${topology.nodes || []} />
                `}
            </main>
        </div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
