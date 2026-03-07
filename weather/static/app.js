import { h, render, Component } from 'https://esm.sh/preact@10.19.3';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const TABS = ['Current', 'Observations', 'Forecast', 'Planting', 'Storms', 'Trends'];

async function api(path, opts) {
  const res = await fetch(`/api/${path}`, opts);
  if (!res.ok && res.status !== 204) throw new Error(`API error: ${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

class App extends Component {
  state = { tab: 'Current', latest: null, forecast: null, observations: [],
    storms: [], stormHistory: [], frostDates: [], windows: [], advisories: [],
    monthly: [], seasonal: [], annual: [], pressure: null, error: null };

  componentDidMount() { this.load(); this._interval = setInterval(() => this.load(), 60000); }
  componentWillUnmount() { clearInterval(this._interval); }

  async load() {
    try {
      const [latest, forecast, obs, storms, stormHistory, pressure] = await Promise.all([
        api('observations/latest').catch(() => null),
        api('forecast').catch(() => null),
        api('observations?limit=20').catch(() => []),
        api('storms/active').catch(() => []),
        api('storms/history?limit=10').catch(() => []),
        api('analysis/pressure').catch(() => null),
      ]);
      this.setState({ latest, forecast, observations: obs, storms,
        stormHistory, pressure, error: null });
    } catch (e) { this.setState({ error: e.message }); }
  }

  async loadTab(tab) {
    this.setState({ tab });
    if (tab === 'Planting') {
      const [frostDates, windows, advisories] = await Promise.all([
        api('planting/frost-dates').catch(() => []),
        api('planting/windows').catch(() => []),
        api('planting/advisories').catch(() => []),
      ]);
      this.setState({ frostDates, windows, advisories });
    } else if (tab === 'Trends') {
      const [monthly, seasonal, annual] = await Promise.all([
        api('trends/monthly').catch(() => []),
        api('trends/seasonal').catch(() => []),
        api('trends/annual').catch(() => []),
      ]);
      this.setState({ monthly, seasonal, annual });
    }
  }

  render(_, s) {
    return html`
      <header>
        <h1>Weather Station</h1>
        <span class="status">${s.latest ? 'ONLINE' : 'NO DATA'}</span>
      </header>
      <div class="tabs">
        ${TABS.map(t => html`
          <button class="tab ${s.tab === t ? 'active' : ''}"
            onClick=${() => this.loadTab(t)}>${t}</button>
        `)}
      </div>
      <main>
        ${s.error && html`<div class="card" style="color:var(--danger)">${s.error}</div>`}
        ${s.tab === 'Current' && this.renderCurrent(s)}
        ${s.tab === 'Observations' && this.renderObservations(s)}
        ${s.tab === 'Forecast' && this.renderForecast(s)}
        ${s.tab === 'Planting' && this.renderPlanting(s)}
        ${s.tab === 'Storms' && this.renderStorms(s)}
        ${s.tab === 'Trends' && this.renderTrends(s)}
      </main>
    `;
  }

  renderCurrent(s) {
    const l = s.latest;
    if (!l) return html`<div class="empty">No observations yet. Add one in the Observations tab.</div>`;
    return html`
      <div class="grid">
        <div class="stat"><div class="value">${l.temperature_c != null ? l.temperature_c + 'C' : '--'}</div><div class="label">Temperature</div></div>
        <div class="stat"><div class="value">${l.humidity_pct != null ? l.humidity_pct + '%' : '--'}</div><div class="label">Humidity</div></div>
        <div class="stat"><div class="value">${l.pressure_hpa != null ? l.pressure_hpa : '--'}</div><div class="label">Pressure (hPa)</div></div>
        <div class="stat"><div class="value">${l.wind_speed_kph != null ? l.wind_speed_kph : '--'}</div><div class="label">Wind (kph)</div></div>
        <div class="stat"><div class="value">${l.cloud_type || '--'}</div><div class="label">Clouds</div></div>
        <div class="stat"><div class="value">${l.visibility || '--'}</div><div class="label">Visibility</div></div>
      </div>
      <div class="card" style="margin-top:1rem">
        <h2>Pressure Trends</h2>
        ${s.pressure ? html`
          <table>
            <tr><th>Period</th><th>Trend</th><th>Change</th></tr>
            ${['3_hour','6_hour','12_hour'].map(k => html`
              <tr>
                <td>${k.replace('_',' ')}</td>
                <td class="${s.pressure[k].trend.includes('falling') ? 'trend-down' : s.pressure[k].trend.includes('rising') ? 'trend-up' : 'trend-steady'}">${s.pressure[k].trend}</td>
                <td>${s.pressure[k].change_hpa} hPa</td>
              </tr>
            `)}
          </table>
        ` : html`<div class="empty">No pressure data</div>`}
      </div>
      ${s.forecast && html`
        <div class="card">
          <h2>Forecast Summary</h2>
          <p>${s.forecast.summary}</p>
          <p style="color:var(--text-dim);margin-top:0.5rem">Confidence: ${s.forecast.confidence_pct}%</p>
        </div>
      `}
    `;
  }

  renderObservations(s) {
    return html`
      <div class="card">
        <h2>New Observation</h2>
        <${ObservationForm} onSubmit=${() => this.load()} />
      </div>
      <div class="card">
        <h2>Recent Observations</h2>
        ${s.observations.length === 0 ? html`<div class="empty">No observations</div>` : html`
          <table>
            <tr><th>Time</th><th>Temp</th><th>Humidity</th><th>Pressure</th><th>Wind</th><th>Source</th></tr>
            ${s.observations.map(o => html`
              <tr>
                <td>${new Date(o.observed_at).toLocaleString()}</td>
                <td>${o.temperature_c != null ? o.temperature_c + 'C' : '--'}</td>
                <td>${o.humidity_pct != null ? o.humidity_pct + '%' : '--'}</td>
                <td>${o.pressure_hpa || '--'}</td>
                <td>${o.wind_speed_kph != null ? o.wind_speed_kph + ' kph' : '--'}</td>
                <td>${o.source}</td>
              </tr>
            `)}
          </table>
        `}
      </div>
    `;
  }

  renderForecast(s) {
    const f = s.forecast;
    return html`
      <div class="card">
        <h2>24-48 Hour Outlook</h2>
        ${f ? html`
          <p style="font-size:1.1rem;margin-bottom:1rem">${f.summary}</p>
          <div class="grid">
            <div class="stat"><div class="value">${f.confidence_pct}%</div><div class="label">Confidence</div></div>
          </div>
          ${f.pressure_trends && html`
            <h2 style="margin-top:1rem">Pressure Trends</h2>
            <table>
              <tr><th>Period</th><th>Trend</th><th>Change</th><th>Readings</th></tr>
              ${Object.entries(f.pressure_trends).map(([k, v]) => html`
                <tr><td>${k.replace('_',' ')}</td><td>${v.trend}</td><td>${v.change_hpa} hPa</td><td>${v.readings}</td></tr>
              `)}
            </table>
          `}
          ${f.moving_averages && html`
            <h2 style="margin-top:1rem">Moving Averages</h2>
            <table>
              <tr><th>Field</th><th>7-day</th><th>30-day</th><th>Seasonal</th></tr>
              ${Object.entries(f.moving_averages).map(([k, v]) => html`
                <tr><td>${k}</td><td>${v['7_day'] ?? '--'}</td><td>${v['30_day'] ?? '--'}</td><td>${v.seasonal ?? '--'}</td></tr>
              `)}
            </table>
          `}
        ` : html`<div class="empty">No forecast available</div>`}
      </div>
    `;
  }

  renderPlanting(s) {
    return html`
      <div class="card">
        <h2>Frost Dates</h2>
        ${s.frostDates.length ? html`
          <table>
            <tr><th>Year</th><th>Type</th><th>Date</th></tr>
            ${s.frostDates.map(f => html`<tr><td>${f.year}</td><td>${f.frost_type}</td><td>${f.frost_date}</td></tr>`)}
          </table>
        ` : html`<div class="empty">No frost dates recorded. Configure defaults in weather.yml.</div>`}
      </div>
      <div class="card">
        <h2>Planting Windows</h2>
        ${s.windows.length ? html`
          <table>
            <tr><th>Crop Type</th><th>Start</th><th>End</th><th>Notes</th></tr>
            ${s.windows.map(w => html`<tr><td>${w.label}</td><td>${w.start}</td><td>${w.end}</td><td>${w.notes}</td></tr>`)}
          </table>
        ` : html`<div class="empty">No planting data</div>`}
      </div>
      <div class="card">
        <h2>Advisories</h2>
        ${s.advisories.length ? html`
          <table>
            <tr><th>Date</th><th>Type</th><th>Message</th></tr>
            ${s.advisories.map(a => html`<tr><td>${a.created_at}</td><td>${a.advisory_type}</td><td>${a.message}</td></tr>`)}
          </table>
        ` : html`<div class="empty">No advisories</div>`}
      </div>
    `;
  }

  renderStorms(s) {
    return html`
      <div class="card">
        <h2>Active Alerts</h2>
        ${s.storms.length ? s.storms.map(st => html`
          <div class="alert ${st.severity}">
            <strong>[${st.severity.toUpperCase()}]</strong> ${st.description}
            <div style="color:var(--text-dim);font-size:0.8rem">${st.event_type} - ${st.detected_at}</div>
          </div>
        `) : html`<div class="empty">No active alerts</div>`}
        <button class="btn" style="margin-top:0.5rem"
          onClick=${async () => { await api('storms/check', {method:'POST'}); this.load(); }}>
          Run Storm Check</button>
      </div>
      <div class="card">
        <h2>Storm History</h2>
        ${s.stormHistory.length ? html`
          <table>
            <tr><th>Date</th><th>Type</th><th>Severity</th><th>Description</th><th>Active</th></tr>
            ${s.stormHistory.map(st => html`
              <tr>
                <td>${st.detected_at}</td><td>${st.event_type}</td>
                <td>${st.severity}</td><td>${st.description}</td>
                <td>${st.active ? 'Yes' : 'No'}</td>
              </tr>
            `)}
          </table>
        ` : html`<div class="empty">No storm history</div>`}
      </div>
    `;
  }

  renderTrends(s) {
    return html`
      <div class="card">
        <h2>Monthly Averages</h2>
        ${s.monthly.length ? html`
          <table>
            <tr><th>Year</th><th>Month</th><th>Avg Temp</th><th>Min</th><th>Max</th><th>Humidity</th><th>Rainfall</th></tr>
            ${s.monthly.map(m => html`
              <tr><td>${m.year}</td><td>${m.month}</td><td>${m.avg_temp_c}C</td>
                <td>${m.min_temp_c}C</td><td>${m.max_temp_c}C</td>
                <td>${m.avg_humidity_pct || '--'}%</td><td>${m.total_rainfall_mm}mm</td></tr>
            `)}
          </table>
        ` : html`<div class="empty">No trend data</div>`}
      </div>
      <div class="card">
        <h2>Seasonal Summary</h2>
        ${s.seasonal.length ? html`
          <table>
            <tr><th>Year</th><th>Season</th><th>Avg Temp</th><th>Rainfall</th></tr>
            ${s.seasonal.map(m => html`
              <tr><td>${m.year}</td><td>${m.season}</td><td>${m.avg_temp_c}C</td><td>${m.total_rainfall_mm}mm</td></tr>
            `)}
          </table>
        ` : html`<div class="empty">No seasonal data</div>`}
      </div>
      <div class="card">
        <h2>Annual Summary</h2>
        ${s.annual.length ? html`
          <table>
            <tr><th>Year</th><th>Avg Temp</th><th>Min</th><th>Max</th><th>Total Rain</th><th>Observations</th></tr>
            ${s.annual.map(m => html`
              <tr><td>${m.year}</td><td>${m.avg_temp_c}C</td><td>${m.min_temp_c}C</td>
                <td>${m.max_temp_c}C</td><td>${m.total_rainfall_mm}mm</td><td>${m.observation_count}</td></tr>
            `)}
          </table>
        ` : html`<div class="empty">No annual data</div>`}
      </div>
    `;
  }
}

class ObservationForm extends Component {
  state = { submitting: false };

  async submit(e) {
    e.preventDefault();
    this.setState({ submitting: true });
    const fd = new FormData(e.target);
    const data = {};
    for (const [k, v] of fd.entries()) {
      if (v === '') continue;
      data[k] = ['temperature_c','humidity_pct','pressure_hpa','wind_speed_kph','rainfall_mm'].includes(k) ? parseFloat(v) : v;
    }
    if (!data.observed_at) data.observed_at = new Date().toISOString();
    await fetch('/api/observations', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) });
    e.target.reset();
    this.setState({ submitting: false });
    this.props.onSubmit();
  }

  render(_, s) {
    return html`
      <form onSubmit=${(e) => this.submit(e)}>
        <div class="form-row">
          <div><label>Date/Time</label><input type="datetime-local" name="observed_at" /></div>
          <div><label>Observer</label><input name="observer" placeholder="Your name" /></div>
        </div>
        <div class="form-row">
          <div><label>Temperature (C)</label><input type="number" step="0.1" name="temperature_c" /></div>
          <div><label>Humidity (%)</label><input type="number" step="0.1" name="humidity_pct" /></div>
          <div><label>Pressure (hPa)</label><input type="number" step="0.1" name="pressure_hpa" /></div>
        </div>
        <div class="form-row">
          <div><label>Wind Speed (kph)</label><input type="number" step="0.1" name="wind_speed_kph" /></div>
          <div><label>Wind Direction</label>
            <select name="wind_direction"><option value="">--</option>
              ${['N','NE','E','SE','S','SW','W','NW'].map(d => html`<option value=${d}>${d}</option>`)}
            </select></div>
          <div><label>Pressure Feel</label>
            <select name="pressure_feel"><option value="">--</option>
              <option>rising</option><option>steady</option><option>falling</option>
            </select></div>
        </div>
        <div class="form-row">
          <div><label>Cloud Type</label>
            <select name="cloud_type"><option value="">--</option>
              ${['clear','cumulus','stratus','cirrus','nimbus','cumulonimbus'].map(c => html`<option value=${c}>${c}</option>`)}
            </select></div>
          <div><label>Precipitation</label>
            <select name="precipitation"><option value="none">none</option>
              <option>light</option><option>moderate</option><option>heavy</option>
            </select></div>
          <div><label>Visibility</label>
            <select name="visibility"><option value="good">good</option>
              <option>moderate</option><option>poor</option>
            </select></div>
        </div>
        <div class="form-row">
          <div><label>Rainfall (mm)</label><input type="number" step="0.1" name="rainfall_mm" value="0" /></div>
          <div><label>Notes</label><input name="notes" placeholder="Additional notes" /></div>
        </div>
        <button class="btn" type="submit" disabled=${s.submitting}>
          ${s.submitting ? 'Saving...' : 'Record Observation'}
        </button>
      </form>
    `;
  }
}

render(html`<${App} />`, document.getElementById('app'));
