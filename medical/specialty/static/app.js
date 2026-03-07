import { h, render, Component } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const api = (path, opts = {}) =>
  fetch(path, {
    headers: { 'Content-Type': 'application/json', 'X-User-Role': 'medical', ...opts.headers },
    ...opts,
  }).then(r => r.json());

// --- Prenatal Section ---
function Prenatal() {
  const [patients, setPatients] = useState([]);
  const [selected, setSelected] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [visits, setVisits] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showVisitForm, setShowVisitForm] = useState(false);
  const [showDeliveryForm, setShowDeliveryForm] = useState(false);

  const load = () => api('/api/prenatal/patients').then(setPatients);
  useEffect(() => { load(); }, []);

  const selectPatient = async (p) => {
    setSelected(p);
    const [sched, vis, del] = await Promise.all([
      api(`/api/prenatal/patients/${p.id}/schedule`),
      api(`/api/prenatal/patients/${p.id}/visits`),
      api(`/api/prenatal/patients/${p.id}/deliveries`),
    ]);
    setSchedule(sched);
    setVisits(vis);
    setDeliveries(del);
  };

  const createPatient = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await api('/api/prenatal/patients', {
      method: 'POST',
      body: JSON.stringify({
        patient_id: fd.get('patient_id'),
        estimated_due_date: fd.get('edd'),
        gravida: parseInt(fd.get('gravida')) || 1,
        para: parseInt(fd.get('para')) || 0,
        blood_type: fd.get('blood_type'),
        rh_factor: fd.get('rh_factor'),
      }),
    });
    setShowForm(false);
    load();
  };

  const createVisit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await api(`/api/prenatal/patients/${selected.id}/visits`, {
      method: 'POST',
      body: JSON.stringify({
        visit_date: fd.get('visit_date'),
        week_number: parseInt(fd.get('week_number')),
        fundal_height: parseFloat(fd.get('fundal_height')) || null,
        fetal_heart_rate: parseFloat(fd.get('fhr')) || null,
        maternal_weight: parseFloat(fd.get('weight')) || null,
        blood_pressure: fd.get('bp'),
        provider: fd.get('provider'),
      }),
    });
    setShowVisitForm(false);
    selectPatient(selected);
  };

  const createDelivery = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await api(`/api/prenatal/patients/${selected.id}/deliveries`, {
      method: 'POST',
      body: JSON.stringify({
        delivery_date: fd.get('delivery_date'),
        delivery_type: fd.get('delivery_type'),
        birth_weight: parseFloat(fd.get('birth_weight')) || null,
        apgar_1min: parseInt(fd.get('apgar_1')) || null,
        apgar_5min: parseInt(fd.get('apgar_5')) || null,
        provider: fd.get('provider'),
        notes: fd.get('notes'),
      }),
    });
    setShowDeliveryForm(false);
    selectPatient(selected);
  };

  return html`
    <div>
      <div class="card">
        <h2>Prenatal Patients</h2>
        <button class="btn btn-small" onClick=${() => setShowForm(!showForm)}>+ New Patient</button>
        ${showForm && html`
          <form onSubmit=${createPatient} style="margin-top: 0.75rem">
            <div class="form-row">
              <div><label>Patient ID</label><input name="patient_id" required /></div>
              <div><label>Due Date</label><input name="edd" type="date" required /></div>
              <div><label>Gravida</label><input name="gravida" type="number" value="1" /></div>
              <div><label>Para</label><input name="para" type="number" value="0" /></div>
            </div>
            <div class="form-row">
              <div><label>Blood Type</label><select name="blood_type"><option>A</option><option>B</option><option>AB</option><option>O</option></select></div>
              <div><label>Rh Factor</label><select name="rh_factor"><option>positive</option><option>negative</option></select></div>
            </div>
            <button class="btn" type="submit">Create</button>
          </form>
        `}
        ${patients.length === 0 && html`<p class="empty-state">No patients registered</p>`}
        ${patients.length > 0 && html`
          <table>
            <thead><tr><th>ID</th><th>Patient</th><th>EDD</th><th>G/P</th></tr></thead>
            <tbody>
              ${patients.map(p => html`
                <tr style="cursor:pointer" onClick=${() => selectPatient(p)}>
                  <td>${p.id}</td><td>${p.patient_id}</td><td>${p.estimated_due_date}</td>
                  <td>G${p.gravida}P${p.para}</td>
                </tr>
              `)}
            </tbody>
          </table>
        `}
      </div>

      ${selected && html`
        <div class="grid">
          <div class="card">
            <h2>Visit Schedule - ${selected.patient_id}</h2>
            ${schedule && schedule.schedule.map(s => html`
              <div style="display:flex;align-items:center;gap:0.5rem;padding:0.25rem 0;border-bottom:1px solid var(--border)">
                <span class="status-indicator" style="background:${s.completed ? 'var(--accent)' : 'var(--border)'}"></span>
                <span>Week ${s.week}</span>
                <span style="color:var(--text-dim);margin-left:auto">${s.date}</span>
              </div>
            `)}
          </div>
          <div class="card">
            <h2>Growth Tracking</h2>
            <button class="btn btn-small" onClick=${() => setShowVisitForm(!showVisitForm)}>+ Record Visit</button>
            ${showVisitForm && html`
              <form onSubmit=${createVisit} style="margin-top:0.75rem">
                <div class="form-row">
                  <div><label>Date</label><input name="visit_date" type="date" required /></div>
                  <div><label>Week</label><input name="week_number" type="number" required /></div>
                </div>
                <div class="form-row">
                  <div><label>Fundal Height (cm)</label><input name="fundal_height" type="number" step="0.1" /></div>
                  <div><label>FHR (bpm)</label><input name="fhr" type="number" /></div>
                </div>
                <div class="form-row">
                  <div><label>Weight (kg)</label><input name="weight" type="number" step="0.1" /></div>
                  <div><label>BP</label><input name="bp" placeholder="120/80" /></div>
                </div>
                <div class="form-group"><label>Provider</label><input name="provider" /></div>
                <button class="btn" type="submit">Save Visit</button>
              </form>
            `}
            ${visits.length > 0 && html`
              <table>
                <thead><tr><th>Week</th><th>FH</th><th>FHR</th><th>Weight</th></tr></thead>
                <tbody>${visits.map(v => html`
                  <tr><td>${v.week_number}</td><td>${v.fundal_height || '-'}</td>
                  <td>${v.fetal_heart_rate || '-'}</td><td>${v.maternal_weight || '-'}</td></tr>
                `)}</tbody>
              </table>
            `}
          </div>
        </div>
        <div class="card">
          <h2>Delivery Log</h2>
          <button class="btn btn-small" onClick=${() => setShowDeliveryForm(!showDeliveryForm)}>+ Record Delivery</button>
          ${showDeliveryForm && html`
            <form onSubmit=${createDelivery} style="margin-top:0.75rem">
              <div class="form-row">
                <div><label>Date</label><input name="delivery_date" type="date" required /></div>
                <div><label>Type</label><select name="delivery_type"><option>vaginal</option><option>cesarean</option><option>assisted</option></select></div>
              </div>
              <div class="form-row">
                <div><label>Birth Weight (kg)</label><input name="birth_weight" type="number" step="0.01" /></div>
                <div><label>Apgar 1min</label><input name="apgar_1" type="number" min="0" max="10" /></div>
                <div><label>Apgar 5min</label><input name="apgar_5" type="number" min="0" max="10" /></div>
              </div>
              <div class="form-row">
                <div><label>Provider</label><input name="provider" /></div>
                <div><label>Notes</label><input name="notes" /></div>
              </div>
              <button class="btn" type="submit">Save Delivery</button>
            </form>
          `}
          ${deliveries.map(d => html`
            <div style="padding:0.5rem 0;border-bottom:1px solid var(--border)">
              <strong>${d.delivery_date}</strong> - ${d.delivery_type}
              ${d.birth_weight ? html` | ${d.birth_weight}kg` : ''}
              ${d.apgar_1min != null ? html` | Apgar: ${d.apgar_1min}/${d.apgar_5min}` : ''}
            </div>
          `)}
        </div>
      `}
    </div>
  `;
}

// --- Dental Section ---
function Dental() {
  const [patients, setPatients] = useState([]);
  const [selected, setSelected] = useState(null);
  const [chart, setChart] = useState(null);
  const [treatments, setTreatments] = useState([]);
  const [protocols, setProtocols] = useState([]);
  const [selectedTooth, setSelectedTooth] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const load = () => api('/api/dental/patients').then(setPatients);
  useEffect(() => {
    load();
    api('/api/dental/emergency-protocols').then(setProtocols);
  }, []);

  const selectPatient = async (p) => {
    setSelected(p);
    const [ch, tr] = await Promise.all([
      api(`/api/dental/patients/${p.id}/chart`),
      api(`/api/dental/patients/${p.id}/treatments`),
    ]);
    setChart(ch);
    setTreatments(tr);
  };

  const updateTooth = async (num, status) => {
    await api(`/api/dental/patients/${selected.id}/chart/${num}`, {
      method: 'PUT',
      body: JSON.stringify({ status, notes: '' }),
    });
    selectPatient(selected);
    setSelectedTooth(null);
  };

  const createPatient = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await api('/api/dental/patients', {
      method: 'POST',
      body: JSON.stringify({ patient_id: fd.get('patient_id'), is_pediatric: fd.get('pediatric') === 'on' }),
    });
    setShowForm(false);
    load();
  };

  const statuses = ['healthy', 'cavity', 'filling', 'crown', 'extraction', 'missing', 'root_canal'];

  return html`
    <div>
      <div class="card">
        <h2>Dental Patients</h2>
        <button class="btn btn-small" onClick=${() => setShowForm(!showForm)}>+ New Patient</button>
        ${showForm && html`
          <form onSubmit=${createPatient} style="margin-top:0.75rem">
            <div class="form-row">
              <div><label>Patient ID</label><input name="patient_id" required /></div>
              <div><label><input type="checkbox" name="pediatric" /> Pediatric</label></div>
            </div>
            <button class="btn" type="submit">Create</button>
          </form>
        `}
        ${patients.length > 0 && html`
          <table>
            <thead><tr><th>ID</th><th>Patient</th><th>Type</th></tr></thead>
            <tbody>${patients.map(p => html`
              <tr style="cursor:pointer" onClick=${() => selectPatient(p)}>
                <td>${p.id}</td><td>${p.patient_id}</td><td>${p.is_pediatric ? 'Pediatric' : 'Adult'}</td>
              </tr>
            `)}</tbody>
          </table>
        `}
      </div>

      ${chart && html`
        <div class="card">
          <h2>Tooth Chart - ${selected.patient_id}</h2>
          <div style="margin-bottom:0.5rem;font-size:0.75rem;color:var(--text-dim)">Click a tooth to update status</div>
          <div style="text-align:center;font-size:0.75rem;color:var(--text-dim);margin-bottom:4px">UPPER</div>
          <div class="tooth-chart">
            ${chart.teeth.slice(0, chart.teeth.length / 2).map(t => html`
              <div class="tooth ${t.status}" onClick=${() => setSelectedTooth(t.tooth_number)} title="Tooth ${t.tooth_number}: ${t.status}">
                <span>${t.tooth_number}</span>
                <span class="tooth-label">${t.status[0].toUpperCase()}</span>
              </div>
            `)}
          </div>
          <div style="text-align:center;font-size:0.75rem;color:var(--text-dim);margin:4px 0">LOWER</div>
          <div class="tooth-chart">
            ${chart.teeth.slice(chart.teeth.length / 2).map(t => html`
              <div class="tooth ${t.status}" onClick=${() => setSelectedTooth(t.tooth_number)} title="Tooth ${t.tooth_number}: ${t.status}">
                <span>${t.tooth_number}</span>
                <span class="tooth-label">${t.status[0].toUpperCase()}</span>
              </div>
            `)}
          </div>

          ${selectedTooth && html`
            <div style="margin-top:1rem;padding:0.75rem;background:var(--bg);border-radius:var(--radius)">
              <h3>Tooth #${selectedTooth} - Set Status</h3>
              <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.5rem">
                ${statuses.map(s => html`
                  <button class="btn btn-small" onClick=${() => updateTooth(selectedTooth, s)}>
                    <span class="badge badge-${s}">${s}</span>
                  </button>
                `)}
              </div>
            </div>
          `}
        </div>

        <div class="card">
          <h2>Treatment History</h2>
          ${treatments.length === 0 && html`<p class="empty-state">No treatments recorded</p>`}
          ${treatments.map(t => html`
            <div style="padding:0.5rem 0;border-bottom:1px solid var(--border)">
              Tooth #${t.tooth_number} - <strong>${t.procedure_type}</strong> (${t.treatment_date})
              ${t.provider && html` by ${t.provider}`}
            </div>
          `)}
        </div>
      `}

      <div class="card">
        <h2>Emergency Protocols</h2>
        ${protocols.map(p => html`
          <div class="resource-card">
            <h4>${p.condition}</h4>
            <ol style="padding-left:1.2rem;font-size:0.8rem;color:var(--text-dim)">
              ${p.steps.map(s => html`<li style="margin-bottom:0.25rem">${s}</li>`)}
            </ol>
          </div>
        `)}
      </div>
    </div>
  `;
}

// --- Mental Health Section ---
function MentalHealth() {
  const [patientId, setPatientId] = useState('');
  const [checkins, setCheckins] = useState([]);
  const [trends, setTrends] = useState(null);
  const [resources, setResources] = useState(null);
  const [mood, setMood] = useState(3);
  const [sleep, setSleep] = useState(3);
  const [appetite, setAppetite] = useState(3);
  const [energy, setEnergy] = useState(3);
  const [anxiety, setAnxiety] = useState(3);
  const [notes, setNotes] = useState('');
  const [view, setView] = useState('checkin');

  useEffect(() => { api('/api/mental/resources').then(setResources); }, []);

  const loadData = async (pid) => {
    if (!pid) return;
    const [ci, tr] = await Promise.all([
      api(`/api/mental/checkins/${pid}`),
      api(`/api/mental/checkins/${pid}/trends?days=30`),
    ]);
    setCheckins(ci);
    setTrends(tr);
  };

  const submitCheckin = async () => {
    if (!patientId) return;
    await api('/api/mental/checkins', {
      method: 'POST',
      body: JSON.stringify({
        patient_id: patientId, mood, sleep_quality: sleep,
        appetite, energy, anxiety_level: anxiety, notes,
      }),
    });
    setNotes('');
    loadData(patientId);
  };

  const deleteCheckin = async (id) => {
    await api(`/api/mental/checkins/${id}?patient_id=${patientId}`, { method: 'DELETE' });
    loadData(patientId);
  };

  const labels = { 1: 'Very Low', 2: 'Low', 3: 'Moderate', 4: 'Good', 5: 'Excellent' };

  return html`
    <div>
      <div class="card" style="border-color:var(--mental)">
        <h2 style="color:var(--mental)">Mental Health & Wellness</h2>
        <p style="font-size:0.8rem;color:var(--text-dim);margin-bottom:0.75rem">
          Privacy-first. All data is voluntary. You control your information.
        </p>
        <div class="form-row" style="align-items:flex-end">
          <div>
            <label>Your ID</label>
            <input value=${patientId} onInput=${e => setPatientId(e.target.value)}
              placeholder="Enter your patient ID" />
          </div>
          <button class="btn" onClick=${() => loadData(patientId)}>Load</button>
        </div>
        <nav class="tab-row">
          <button class=${view === 'checkin' ? 'btn' : 'btn btn-small'} onClick=${() => setView('checkin')}>Check-in</button>
          <button class=${view === 'trends' ? 'btn' : 'btn btn-small'} onClick=${() => setView('trends')}>Trends</button>
          <button class=${view === 'resources' ? 'btn' : 'btn btn-small'} onClick=${() => setView('resources')}>Resources</button>
        </nav>
      </div>

      ${view === 'checkin' && html`
        <div class="card">
          <h2>Wellness Check-in</h2>
          <div class="slider-group"><label>Mood</label><input type="range" min="1" max="5" value=${mood} onInput=${e => setMood(+e.target.value)} /><span class="value">${mood}</span></div>
          <div class="slider-group"><label>Sleep Quality</label><input type="range" min="1" max="5" value=${sleep} onInput=${e => setSleep(+e.target.value)} /><span class="value">${sleep}</span></div>
          <div class="slider-group"><label>Appetite</label><input type="range" min="1" max="5" value=${appetite} onInput=${e => setAppetite(+e.target.value)} /><span class="value">${appetite}</span></div>
          <div class="slider-group"><label>Energy</label><input type="range" min="1" max="5" value=${energy} onInput=${e => setEnergy(+e.target.value)} /><span class="value">${energy}</span></div>
          <div class="slider-group"><label>Anxiety Level</label><input type="range" min="1" max="5" value=${anxiety} onInput=${e => setAnxiety(+e.target.value)} /><span class="value">${anxiety}</span></div>
          <div class="form-group"><label>Notes (optional)</label><textarea value=${notes} onInput=${e => setNotes(e.target.value)}></textarea></div>
          <button class="btn" onClick=${submitCheckin}>Submit Check-in</button>
        </div>

        ${checkins.length > 0 && html`
          <div class="card">
            <h2>Recent Check-ins</h2>
            <table>
              <thead><tr><th>Date</th><th>Mood</th><th>Sleep</th><th>Energy</th><th>Anxiety</th><th></th></tr></thead>
              <tbody>${checkins.slice(0, 10).map(c => html`
                <tr>
                  <td>${c.checkin_date}</td><td>${c.mood}</td><td>${c.sleep_quality}</td>
                  <td>${c.energy}</td><td>${c.anxiety_level}</td>
                  <td><button class="btn btn-small btn-danger" onClick=${() => deleteCheckin(c.id)}>Del</button></td>
                </tr>
              `)}</tbody>
            </table>
          </div>
        `}
      `}

      ${view === 'trends' && trends && html`
        <div class="card">
          <h2>Mood Trend (30 days)</h2>
          <div class="trend-chart">
            ${trends.data.map(d => html`
              <div class="trend-bar" style="height:${d.mood * 20}%" title="Mood: ${d.mood}"></div>
            `)}
          </div>
          ${Object.keys(trends.averages).length > 0 && html`
            <div class="grid" style="margin-top:1rem">
              ${Object.entries(trends.averages).map(([k, v]) => html`
                <div class="resource-card">
                  <h4>${k.replace('_', ' ')}</h4>
                  <p style="font-size:1.2rem;color:var(--mental)">${v.toFixed(1)} / 5</p>
                </div>
              `)}
            </div>
          `}
        </div>
      `}

      ${view === 'resources' && resources && html`
        <div class="card">
          <h2>Coping Strategies</h2>
          ${resources.coping_strategies.map(s => html`
            <div class="resource-card"><h4>${s.title}</h4><p>${s.description}</p></div>
          `)}
        </div>
        <div class="card">
          <h2>Self-Care Tips</h2>
          <ul style="padding-left:1.2rem">${resources.self_care_tips.map(t => html`<li style="margin-bottom:0.5rem;font-size:0.85rem">${t}</li>`)}</ul>
        </div>
        <div class="card">
          <h2>Crisis Information</h2>
          ${resources.crisis_info.map(c => html`
            <div class="resource-card"><h4>${c.title}</h4><p>${c.description}</p></div>
          `)}
        </div>
      `}
    </div>
  `;
}

// --- Veterinary Section ---
function Veterinary() {
  const [visits, setVisits] = useState([]);
  const [herdHealth, setHerdHealth] = useState(null);
  const [conditions, setConditions] = useState([]);
  const [protocols, setProtocols] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [animalInfo, setAnimalInfo] = useState(null);
  const [searchId, setSearchId] = useState('');
  const [view, setView] = useState('visits');

  const load = () => {
    api('/api/vet/visits').then(setVisits);
    api('/api/vet/herd-health').then(setHerdHealth);
  };

  useEffect(() => {
    load();
    api('/api/vet/conditions').then(setConditions);
    api('/api/vet/protocols').then(setProtocols);
  }, []);

  const createVisit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await api('/api/vet/visits', {
      method: 'POST',
      body: JSON.stringify({
        animal_id: fd.get('animal_id'),
        condition: fd.get('condition'),
        treatment: fd.get('treatment'),
        provider: fd.get('provider'),
        notes: fd.get('notes'),
      }),
    });
    setShowForm(false);
    load();
  };

  const lookupAnimal = async () => {
    if (!searchId) return;
    const info = await api(`/api/vet/animals/${searchId}`);
    setAnimalInfo(info);
  };

  return html`
    <div>
      <div class="card">
        <nav class="tab-row">
          <button class=${view === 'visits' ? 'btn' : 'btn btn-small'} onClick=${() => setView('visits')}>Visits</button>
          <button class=${view === 'herd' ? 'btn' : 'btn btn-small'} onClick=${() => setView('herd')}>Herd Health</button>
          <button class=${view === 'lookup' ? 'btn' : 'btn btn-small'} onClick=${() => setView('lookup')}>Animal Lookup</button>
          <button class=${view === 'ref' ? 'btn' : 'btn btn-small'} onClick=${() => setView('ref')}>Reference</button>
        </nav>
      </div>

      ${view === 'visits' && html`
        <div class="card">
          <h2>Veterinary Visits</h2>
          <button class="btn btn-small" onClick=${() => setShowForm(!showForm)}>+ New Visit</button>
          ${showForm && html`
            <form onSubmit=${createVisit} style="margin-top:0.75rem">
              <div class="form-row">
                <div><label>Animal ID</label><input name="animal_id" required /></div>
                <div><label>Condition</label>
                  <select name="condition">
                    ${conditions.map(c => html`<option value=${c.name}>${c.name}</option>`)}
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div class="form-group"><label>Treatment</label><textarea name="treatment"></textarea></div>
              <div class="form-row">
                <div><label>Provider</label><input name="provider" /></div>
                <div><label>Notes</label><input name="notes" /></div>
              </div>
              <button class="btn" type="submit">Save Visit</button>
            </form>
          `}
          ${visits.length === 0 && html`<p class="empty-state">No visits recorded</p>`}
          <table>
            <thead><tr><th>Date</th><th>Animal</th><th>Condition</th><th>Treatment</th><th>Provider</th></tr></thead>
            <tbody>${visits.map(v => html`
              <tr>
                <td>${v.visit_date}</td><td>${v.animal_id}</td><td>${v.condition}</td>
                <td>${v.treatment || '-'}</td><td>${v.provider || '-'}</td>
              </tr>
            `)}</tbody>
          </table>
        </div>
      `}

      ${view === 'herd' && herdHealth && html`
        <div class="card">
          <h2>Herd Health Dashboard</h2>
          <div class="grid">
            <div class="resource-card">
              <h4>Total Visits</h4>
              <p style="font-size:1.5rem;color:var(--vet)">${herdHealth.total_visits}</p>
            </div>
            <div class="resource-card">
              <h4>Unique Animals</h4>
              <p style="font-size:1.5rem;color:var(--vet)">${herdHealth.unique_animals}</p>
            </div>
          </div>
          ${herdHealth.conditions.length > 0 && html`
            <h3 style="margin-top:1rem">Conditions Breakdown</h3>
            <table>
              <thead><tr><th>Condition</th><th>Count</th></tr></thead>
              <tbody>${herdHealth.conditions.map(c => html`
                <tr><td>${c.condition}</td><td>${c.count}</td></tr>
              `)}</tbody>
            </table>
          `}
        </div>
      `}

      ${view === 'lookup' && html`
        <div class="card">
          <h2>Animal Lookup</h2>
          <div class="form-row" style="align-items:flex-end">
            <div><label>Animal ID</label><input value=${searchId} onInput=${e => setSearchId(e.target.value)} /></div>
            <button class="btn" onClick=${lookupAnimal}>Search</button>
          </div>
          ${animalInfo && html`
            <div style="margin-top:1rem">
              <h3>${animalInfo.animal_id} <span style="font-size:0.75rem;color:var(--text-dim)">(${animalInfo.source})</span></h3>
              ${animalInfo.vet_visits && animalInfo.vet_visits.length > 0 ? html`
                <table>
                  <thead><tr><th>Date</th><th>Condition</th><th>Treatment</th></tr></thead>
                  <tbody>${animalInfo.vet_visits.map(v => html`
                    <tr><td>${v.visit_date}</td><td>${v.condition}</td><td>${v.treatment || '-'}</td></tr>
                  `)}</tbody>
                </table>
              ` : html`<p class="empty-state">No vet visits for this animal</p>`}
            </div>
          `}
        </div>
      `}

      ${view === 'ref' && html`
        <div class="card">
          <h2>Common Conditions</h2>
          ${conditions.map(c => html`
            <div class="resource-card">
              <h4>${c.name} <span class="badge" style="background:${c.severity === 'high' ? 'var(--danger)' : 'var(--warning)'}33;color:${c.severity === 'high' ? 'var(--danger)' : 'var(--warning)'}">${c.severity}</span></h4>
              <p>Species: ${c.species.join(', ')}</p>
              <p>Symptoms: ${c.symptoms.join(', ')}</p>
            </div>
          `)}
        </div>
        <div class="card">
          <h2>Treatment Protocols</h2>
          ${protocols.map(p => html`
            <div class="resource-card">
              <h4>${p.condition}</h4>
              <ol style="padding-left:1.2rem;font-size:0.8rem;color:var(--text-dim)">
                ${p.treatments.map(t => html`<li style="margin-bottom:0.25rem">${t}</li>`)}
              </ol>
            </div>
          `)}
        </div>
      `}
    </div>
  `;
}

// --- Main App ---
function App() {
  const [section, setSection] = useState('prenatal');

  const sections = { prenatal: Prenatal, dental: Dental, mental: MentalHealth, vet: Veterinary };
  const Content = sections[section];

  return html`
    <header>
      <h1>[SURVIVE OS] Medical Specialty</h1>
      <nav>
        <button data-section="prenatal" class=${section === 'prenatal' ? 'active' : ''} onClick=${() => setSection('prenatal')}>Prenatal</button>
        <button data-section="dental" class=${section === 'dental' ? 'active' : ''} onClick=${() => setSection('dental')}>Dental</button>
        <button data-section="mental" class=${section === 'mental' ? 'active' : ''} onClick=${() => setSection('mental')}>Mental Health</button>
        <button data-section="vet" class=${section === 'vet' ? 'active' : ''} onClick=${() => setSection('vet')}>Veterinary</button>
      </nav>
    </header>
    <${Content} />
  `;
}

render(html`<${App} />`, document.getElementById('app'));
