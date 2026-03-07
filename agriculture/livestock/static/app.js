/** Livestock Management Frontend */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const show = (el) => el.classList.remove("hidden");
const hide = (el) => el.classList.add("hidden");

async function api(url, opts = {}) {
    const res = await fetch(url, {
        headers: { "Content-Type": "application/json", ...opts.headers },
        ...opts,
    });
    if (res.status === 204) return null;
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

// --- Tab Navigation ---
let currentTab = "herd";

document.addEventListener("click", (e) => {
    const navItem = e.target.closest(".nav-item");
    if (navItem) {
        const tab = navItem.dataset.tab;
        switchTab(tab);
    }
});

function switchTab(tab) {
    currentTab = tab;
    $$(".nav-item").forEach(el => el.classList.toggle("active", el.dataset.tab === tab));
    $$(".tab-content").forEach(el => hide(el));
    show($(`#tab-${tab}`));
    loaders[tab]();
}

// --- Herd Tab ---
let herdSpeciesFilter = "";
let herdStatusFilter = "";

async function loadHerd() {
    let url = "/api/animals?";
    if (herdSpeciesFilter) url += `species=${herdSpeciesFilter}&`;
    if (herdStatusFilter) url += `status=${herdStatusFilter}&`;
    const animals = await api(url);

    const species = [...new Set(animals.map(a => a.species))];

    $("#tab-herd").innerHTML = `
        <div class="tab-header">
            <h1>Herd Management</h1>
            <button class="btn btn-primary" onclick="showAnimalForm()">Add Animal</button>
        </div>
        <div class="filters">
            <select onchange="herdSpeciesFilter=this.value;loadHerd()">
                <option value="">All Species</option>
                ${species.map(s => `<option value="${s}" ${s===herdSpeciesFilter?'selected':''}>${s}</option>`).join("")}
            </select>
            <select onchange="herdStatusFilter=this.value;loadHerd()">
                <option value="">All Status</option>
                <option value="active" ${herdStatusFilter==='active'?'selected':''}>Active</option>
                <option value="sold" ${herdStatusFilter==='sold'?'selected':''}>Sold</option>
                <option value="deceased" ${herdStatusFilter==='deceased'?'selected':''}>Deceased</option>
            </select>
        </div>
        <div class="stats-row">
            <div class="stat-card"><div class="stat-value">${animals.length}</div><div class="stat-label">Total Animals</div></div>
            <div class="stat-card"><div class="stat-value">${animals.filter(a=>a.status==='active').length}</div><div class="stat-label">Active</div></div>
            <div class="stat-card"><div class="stat-value">${species.length}</div><div class="stat-label">Species</div></div>
        </div>
        ${animals.map(a => `
            <div class="card" onclick="showAnimalDetail(${a.id})">
                <h3>${a.name} ${a.tag ? `<span class="meta">#${a.tag}</span>` : ''}</h3>
                <div class="meta">
                    ${a.species} ${a.breed ? '- '+a.breed : ''} | ${a.sex}
                    <span class="badge badge-${a.status}">${a.status}</span>
                </div>
            </div>
        `).join("")}
        ${animals.length === 0 ? '<p style="color:var(--text-secondary)">No animals found.</p>' : ''}
    `;
}

async function showAnimalDetail(id) {
    const animal = await api(`/api/animals/${id}`);
    const pedigree = await api(`/api/animals/${id}/pedigree`);
    const offspring = await api(`/api/animals/${id}/offspring`);

    $("#tab-herd").innerHTML = `
        <div class="detail-header">
            <button class="btn" onclick="loadHerd()">Back</button>
            <h1>${animal.name}</h1>
            <span class="badge badge-${animal.status}">${animal.status}</span>
        </div>
        <div class="detail-grid">
            <div class="detail-field"><label>Tag</label><span>${animal.tag || '-'}</span></div>
            <div class="detail-field"><label>Species</label><span>${animal.species}</span></div>
            <div class="detail-field"><label>Breed</label><span>${animal.breed || '-'}</span></div>
            <div class="detail-field"><label>Sex</label><span>${animal.sex}</span></div>
            <div class="detail-field"><label>Birth Date</label><span>${animal.birth_date || '-'}</span></div>
            <div class="detail-field"><label>Acquired</label><span>${animal.acquisition_date || '-'}</span></div>
        </div>
        ${animal.notes ? `<p style="margin-bottom:16px;color:var(--text-secondary)">${animal.notes}</p>` : ''}
        <h2 style="font-size:16px;margin-bottom:12px">Pedigree</h2>
        <div class="pedigree">${renderPedigreeNode(pedigree)}</div>
        ${offspring.length > 0 ? `
            <h2 style="font-size:16px;margin:16px 0 12px">Offspring (${offspring.length})</h2>
            ${offspring.map(o => `
                <div class="card" onclick="showAnimalDetail(${o.id})">
                    <h3>${o.name}</h3><div class="meta">${o.species} | ${o.sex} | ${o.birth_date || ''}</div>
                </div>
            `).join("")}
        ` : ''}
        <div style="margin-top:16px;display:flex;gap:8px">
            <button class="btn" onclick="showAnimalForm(${id})">Edit</button>
            <button class="btn btn-danger" onclick="deleteAnimal(${id})">Delete</button>
        </div>
    `;
}

function renderPedigreeNode(node) {
    if (!node) return '<div class="pedigree-node">Unknown</div>';
    return `
        <div style="display:flex;align-items:center;gap:16px">
            <div class="pedigree-node ${node.sex}">
                <strong>${node.name}</strong><br>
                <span style="font-size:11px;color:var(--text-secondary)">${node.breed || node.species || ''}</span>
            </div>
            ${(node.sire || node.dam) ? `
                <div class="pedigree-branch">
                    ${renderPedigreeNode(node.sire)}
                    ${renderPedigreeNode(node.dam)}
                </div>
            ` : ''}
        </div>
    `;
}

function showAnimalForm(editId) {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <h2>${editId ? 'Edit' : 'Add'} Animal</h2>
            <div class="form-row">
                <div class="form-group"><label>Name</label><input id="f-name" required></div>
                <div class="form-group"><label>Tag</label><input id="f-tag"></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Species</label>
                    <select id="f-species"><option>cattle</option><option>goat</option><option>sheep</option><option>chicken</option><option>pig</option><option>horse</option><option>rabbit</option><option>duck</option><option>turkey</option></select>
                </div>
                <div class="form-group"><label>Breed</label><input id="f-breed"></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Sex</label>
                    <select id="f-sex"><option value="female">Female</option><option value="male">Male</option><option value="unknown">Unknown</option></select>
                </div>
                <div class="form-group"><label>Status</label>
                    <select id="f-status"><option value="active">Active</option><option value="sold">Sold</option><option value="deceased">Deceased</option></select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Birth Date</label><input id="f-birth" type="date"></div>
                <div class="form-group"><label>Acquisition Date</label><input id="f-acq" type="date"></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Sire ID</label><input id="f-sire" type="number"></div>
                <div class="form-group"><label>Dam ID</label><input id="f-dam" type="number"></div>
            </div>
            <div class="form-group"><label>Notes</label><textarea id="f-notes"></textarea></div>
            <div class="form-actions">
                <button class="btn" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="saveAnimal(${editId||'null'})">Save</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
    if (editId) {
        api(`/api/animals/${editId}`).then(a => {
            $("#f-name").value = a.name;
            $("#f-tag").value = a.tag || "";
            $("#f-species").value = a.species;
            $("#f-breed").value = a.breed || "";
            $("#f-sex").value = a.sex;
            $("#f-status").value = a.status;
            $("#f-birth").value = a.birth_date || "";
            $("#f-acq").value = a.acquisition_date || "";
            $("#f-sire").value = a.sire_id || "";
            $("#f-dam").value = a.dam_id || "";
            $("#f-notes").value = a.notes || "";
        });
    }
}

async function saveAnimal(editId) {
    const data = {
        name: $("#f-name").value,
        tag: $("#f-tag").value || null,
        species: $("#f-species").value,
        breed: $("#f-breed").value,
        sex: $("#f-sex").value,
        status: $("#f-status").value,
        birth_date: $("#f-birth").value || null,
        acquisition_date: $("#f-acq").value || null,
        sire_id: $("#f-sire").value ? parseInt($("#f-sire").value) : null,
        dam_id: $("#f-dam").value ? parseInt($("#f-dam").value) : null,
        notes: $("#f-notes").value,
    };
    if (editId) {
        await api(`/api/animals/${editId}`, { method: "PUT", body: JSON.stringify(data) });
    } else {
        await api("/api/animals", { method: "POST", body: JSON.stringify(data) });
    }
    $(".modal-overlay").remove();
    loadHerd();
}

async function deleteAnimal(id) {
    if (!confirm("Delete this animal?")) return;
    await api(`/api/animals/${id}`, { method: "DELETE" });
    loadHerd();
}

// --- Breeding Tab ---
async function loadBreeding() {
    const events = await api("/api/breeding/events");
    const gestation = await api("/api/breeding/gestation");

    $("#tab-breeding").innerHTML = `
        <div class="tab-header">
            <h1>Breeding Planner</h1>
            <div style="display:flex;gap:8px">
                <button class="btn" onclick="showInbreedingCheck()">Check Inbreeding</button>
                <button class="btn" onclick="showPairingSuggestions()">Suggest Pairings</button>
                <button class="btn btn-primary" onclick="showBreedingForm()">Record Breeding</button>
            </div>
        </div>
        <div id="breeding-alerts"></div>
        <h2 style="font-size:16px;margin-bottom:12px">Breeding Events</h2>
        <table>
            <thead><tr><th>Sire</th><th>Dam</th><th>Date Bred</th><th>Due Date</th><th>Outcome</th></tr></thead>
            <tbody>
                ${events.map(e => `<tr>
                    <td>${e.sire_name}</td><td>${e.dam_name}</td>
                    <td>${e.date_bred}</td><td>${e.expected_due_date || '-'}</td>
                    <td><span class="badge badge-${e.outcome==='pending'?'warning':e.outcome==='success'?'ok':'danger'}">${e.outcome}</span></td>
                </tr>`).join("")}
                ${events.length === 0 ? '<tr><td colspan="5" style="color:var(--text-secondary)">No breeding events recorded.</td></tr>' : ''}
            </tbody>
        </table>
        <h2 style="font-size:16px;margin:16px 0 12px">Gestation Periods</h2>
        <table>
            <thead><tr><th>Species</th><th>Days</th></tr></thead>
            <tbody>${Object.entries(gestation).map(([s,d]) => `<tr><td>${s}</td><td>${d}</td></tr>`).join("")}</tbody>
        </table>
    `;
}

function showBreedingForm() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <h2>Record Breeding Event</h2>
            <div class="form-row">
                <div class="form-group"><label>Sire ID</label><input id="fb-sire" type="number" required></div>
                <div class="form-group"><label>Dam ID</label><input id="fb-dam" type="number" required></div>
            </div>
            <div class="form-group"><label>Date Bred</label><input id="fb-date" type="date" required></div>
            <div class="form-group"><label>Notes</label><textarea id="fb-notes"></textarea></div>
            <div class="form-actions">
                <button class="btn" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="saveBreeding()">Save</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
}

async function saveBreeding() {
    await api("/api/breeding/events", {
        method: "POST",
        body: JSON.stringify({
            sire_id: parseInt($("#fb-sire").value),
            dam_id: parseInt($("#fb-dam").value),
            date_bred: $("#fb-date").value,
            notes: $("#fb-notes").value,
        }),
    });
    $(".modal-overlay").remove();
    loadBreeding();
}

async function showInbreedingCheck() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <h2>Inbreeding Check</h2>
            <div class="form-row">
                <div class="form-group"><label>Sire ID</label><input id="fi-sire" type="number" required></div>
                <div class="form-group"><label>Dam ID</label><input id="fi-dam" type="number" required></div>
            </div>
            <div class="form-actions">
                <button class="btn" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="checkInbreeding()">Check</button>
            </div>
            <div id="inbreeding-result" style="margin-top:12px"></div>
        </div>
    `;
    document.body.appendChild(overlay);
}

async function checkInbreeding() {
    const sireId = $("#fi-sire").value;
    const damId = $("#fi-dam").value;
    const data = await api(`/api/breeding/inbreeding?sire_id=${sireId}&dam_id=${damId}`);
    const pct = (data.coefficient * 100).toFixed(2);
    $("#inbreeding-result").innerHTML = `
        <div class="alert ${data.warning ? 'alert-danger' : 'alert-warning'}">
            <strong>${data.sire_name} x ${data.dam_name}</strong><br>
            Inbreeding coefficient: ${pct}% ${data.warning ? '(EXCEEDS THRESHOLD)' : '(within limits)'}
        </div>
    `;
}

async function showPairingSuggestions() {
    const pairings = await api("/api/breeding/suggestions");
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <h2>Suggested Pairings (Lowest Inbreeding)</h2>
            <table>
                <thead><tr><th>Sire</th><th>Dam</th><th>Coefficient</th><th>Status</th></tr></thead>
                <tbody>
                    ${pairings.slice(0, 20).map(p => `<tr>
                        <td>${p.sire_name}</td><td>${p.dam_name}</td>
                        <td>${(p.coefficient * 100).toFixed(2)}%</td>
                        <td>${p.warning ? '<span class="badge badge-danger">High</span>' : '<span class="badge badge-ok">OK</span>'}</td>
                    </tr>`).join("")}
                    ${pairings.length === 0 ? '<tr><td colspan="4">No pairings available.</td></tr>' : ''}
                </tbody>
            </table>
            <div class="form-actions"><button class="btn" onclick="this.closest('.modal-overlay').remove()">Close</button></div>
        </div>
    `;
    document.body.appendChild(overlay);
}

// --- Feed Tab ---
async function loadFeed() {
    const types = await api("/api/feed/types");
    const inventory = await api("/api/feed/inventory");
    const alerts = await api("/api/feed/inventory/alerts");

    $("#tab-feed").innerHTML = `
        <div class="tab-header">
            <h1>Feed Management</h1>
        </div>
        ${alerts.length > 0 ? alerts.map(a => `
            <div class="alert alert-warning">Low stock: ${a.feed_name} - ${a.quantity} ${a.unit} remaining (threshold: ${a.low_threshold})</div>
        `).join("") : ''}
        <h2 style="font-size:16px;margin-bottom:12px">Feed Calculator</h2>
        <div class="filters">
            <select id="fc-species">
                <option value="cattle">Cattle</option><option value="goat">Goat</option>
                <option value="sheep">Sheep</option><option value="chicken">Chicken</option>
                <option value="pig">Pig</option>
            </select>
            <input id="fc-weight" type="number" placeholder="Weight (kg)" style="width:120px">
            <select id="fc-stage">
                <option value="maintenance">Maintenance</option><option value="growing">Growing</option>
                <option value="pregnant">Pregnant</option><option value="lactating">Lactating</option>
            </select>
            <button class="btn btn-primary" onclick="calculateFeed()">Calculate</button>
        </div>
        <div id="feed-result"></div>
        <h2 style="font-size:16px;margin:16px 0 12px">Feed Inventory</h2>
        <table>
            <thead><tr><th>Feed</th><th>Quantity</th><th>Unit</th><th>Status</th></tr></thead>
            <tbody>
                ${inventory.map(i => `<tr>
                    <td>${i.feed_name}</td><td>${i.quantity}</td><td>${i.unit}</td>
                    <td>${i.quantity <= i.low_threshold ? '<span class="badge badge-danger">Low</span>' : '<span class="badge badge-ok">OK</span>'}</td>
                </tr>`).join("")}
                ${inventory.length === 0 ? '<tr><td colspan="4" style="color:var(--text-secondary)">No inventory tracked.</td></tr>' : ''}
            </tbody>
        </table>
    `;
}

async function calculateFeed() {
    const species = $("#fc-species").value;
    const weight = $("#fc-weight").value;
    const stage = $("#fc-stage").value;
    if (!weight) { alert("Enter weight"); return; }
    const data = await api(`/api/feed/calculate?species=${species}&weight_kg=${weight}&production_stage=${stage}`);
    $("#feed-result").innerHTML = `
        <div class="card" style="cursor:default">
            <h3>Daily Feed Requirements</h3>
            <div class="detail-grid">
                <div class="detail-field"><label>Dry Matter</label><span>${data.daily_dry_matter_kg} kg/day</span></div>
                <div class="detail-field"><label>Crude Protein</label><span>${data.daily_crude_protein_kg} kg/day</span></div>
                <div class="detail-field"><label>DM % Body Weight</label><span>${data.dm_pct_body_weight}%</span></div>
                <div class="detail-field"><label>CP %</label><span>${data.crude_protein_pct}%</span></div>
            </div>
            ${data.notes ? `<p class="meta">${data.notes}</p>` : ''}
        </div>
    `;
}

// --- Vet Tab ---
async function loadVet() {
    const treatments = await api("/api/vet/treatments");
    const withdrawals = await api("/api/vet/withdrawals");
    const meds = await api("/api/vet/medications");
    const medAlerts = await api("/api/vet/medications/alerts");
    const vacDue = await api("/api/vet/vaccinations/due");

    $("#tab-vet").innerHTML = `
        <div class="tab-header">
            <h1>Veterinary</h1>
            <div style="display:flex;gap:8px">
                <button class="btn" onclick="showMedForm()">Add Medication</button>
                <button class="btn" onclick="showVaxForm()">Record Vaccination</button>
                <button class="btn btn-primary" onclick="showTreatmentForm()">Record Treatment</button>
            </div>
        </div>
        ${withdrawals.length > 0 ? withdrawals.map(w => `
            <div class="alert alert-danger">Withdrawal: ${w.animal_name} - ${w.medication} until ${w.withdrawal_end_date}</div>
        `).join("") : ''}
        ${medAlerts.length > 0 ? medAlerts.map(m => `
            <div class="alert alert-warning">Low medication: ${m.name} - ${m.quantity} ${m.unit} remaining</div>
        `).join("") : ''}
        ${vacDue.length > 0 ? `<h2 style="font-size:16px;margin-bottom:8px">Vaccinations Due</h2>
            <table><thead><tr><th>Animal</th><th>Vaccine</th><th>Due Date</th></tr></thead><tbody>
            ${vacDue.map(v => `<tr><td>${v.animal_name}</td><td>${v.vaccine}</td><td>${v.next_due_date}</td></tr>`).join("")}
            </tbody></table>` : ''}
        <h2 style="font-size:16px;margin:12px 0">Treatment Log</h2>
        <table>
            <thead><tr><th>Date</th><th>Animal</th><th>Condition</th><th>Treatment</th><th>Medication</th><th>Withdrawal</th></tr></thead>
            <tbody>
                ${treatments.map(t => `<tr>
                    <td>${t.date}</td><td>${t.animal_name}</td><td>${t.condition}</td>
                    <td>${t.treatment}</td><td>${t.medication || '-'}</td>
                    <td>${t.withdrawal_end_date || '-'}</td>
                </tr>`).join("")}
                ${treatments.length === 0 ? '<tr><td colspan="6" style="color:var(--text-secondary)">No treatments recorded.</td></tr>' : ''}
            </tbody>
        </table>
        <h2 style="font-size:16px;margin:16px 0 12px">Medication Inventory</h2>
        <table>
            <thead><tr><th>Name</th><th>Type</th><th>Quantity</th><th>Withdrawal Days</th></tr></thead>
            <tbody>
                ${meds.map(m => `<tr><td>${m.name}</td><td>${m.type}</td><td>${m.quantity} ${m.unit}</td><td>${m.default_withdrawal_days}</td></tr>`).join("")}
                ${meds.length === 0 ? '<tr><td colspan="4" style="color:var(--text-secondary)">No medications tracked.</td></tr>' : ''}
            </tbody>
        </table>
    `;
}

function showTreatmentForm() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <h2>Record Treatment</h2>
            <div class="form-row">
                <div class="form-group"><label>Animal ID</label><input id="ft-animal" type="number" required></div>
                <div class="form-group"><label>Date</label><input id="ft-date" type="date"></div>
            </div>
            <div class="form-group"><label>Condition</label><input id="ft-cond" required></div>
            <div class="form-group"><label>Treatment</label><input id="ft-treat" required></div>
            <div class="form-row">
                <div class="form-group"><label>Medication</label><input id="ft-med"></div>
                <div class="form-group"><label>Dosage</label><input id="ft-dose"></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Administered By</label><input id="ft-admin"></div>
                <div class="form-group"><label>Withdrawal Days</label><input id="ft-wd" type="number" value="0"></div>
            </div>
            <div class="form-group"><label>Notes</label><textarea id="ft-notes"></textarea></div>
            <div class="form-actions">
                <button class="btn" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="saveTreatment()">Save</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
}

async function saveTreatment() {
    await api("/api/vet/treatments", {
        method: "POST",
        body: JSON.stringify({
            animal_id: parseInt($("#ft-animal").value),
            date: $("#ft-date").value || null,
            condition: $("#ft-cond").value,
            treatment: $("#ft-treat").value,
            medication: $("#ft-med").value,
            dosage: $("#ft-dose").value,
            administered_by: $("#ft-admin").value,
            withdrawal_days: parseInt($("#ft-wd").value) || 0,
            notes: $("#ft-notes").value,
        }),
    });
    $(".modal-overlay").remove();
    loadVet();
}

function showMedForm() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <h2>Add Medication</h2>
            <div class="form-group"><label>Name</label><input id="fm-name" required></div>
            <div class="form-row">
                <div class="form-group"><label>Type</label><input id="fm-type" placeholder="antibiotic, vaccine, etc."></div>
                <div class="form-group"><label>Unit</label><input id="fm-unit" value="doses"></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Quantity</label><input id="fm-qty" type="number" value="0"></div>
                <div class="form-group"><label>Withdrawal Days</label><input id="fm-wd" type="number" value="0"></div>
            </div>
            <div class="form-actions">
                <button class="btn" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="saveMed()">Save</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
}

async function saveMed() {
    await api("/api/vet/medications", {
        method: "POST",
        body: JSON.stringify({
            name: $("#fm-name").value,
            type: $("#fm-type").value,
            quantity: parseFloat($("#fm-qty").value),
            unit: $("#fm-unit").value,
            default_withdrawal_days: parseInt($("#fm-wd").value) || 0,
        }),
    });
    $(".modal-overlay").remove();
    loadVet();
}

function showVaxForm() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <h2>Record Vaccination</h2>
            <div class="form-row">
                <div class="form-group"><label>Animal ID</label><input id="fv-animal" type="number" required></div>
                <div class="form-group"><label>Vaccine</label><input id="fv-vax" required></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Date Given</label><input id="fv-date" type="date" required></div>
                <div class="form-group"><label>Next Due</label><input id="fv-next" type="date"></div>
            </div>
            <div class="form-group"><label>Administered By</label><input id="fv-admin"></div>
            <div class="form-actions">
                <button class="btn" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="saveVax()">Save</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
}

async function saveVax() {
    await api("/api/vet/vaccinations", {
        method: "POST",
        body: JSON.stringify({
            animal_id: parseInt($("#fv-animal").value),
            vaccine: $("#fv-vax").value,
            date_given: $("#fv-date").value,
            next_due_date: $("#fv-next").value || null,
            administered_by: $("#fv-admin").value,
        }),
    });
    $(".modal-overlay").remove();
    loadVet();
}

// --- Production Tab ---
async function loadProduction() {
    const records = await api("/api/production/records");

    $("#tab-production").innerHTML = `
        <div class="tab-header">
            <h1>Production Records</h1>
            <button class="btn btn-primary" onclick="showProductionForm()">Add Record</button>
        </div>
        <h2 style="font-size:16px;margin-bottom:12px">Analytics</h2>
        <div class="filters">
            <select id="pa-type">
                <option value="milk">Milk</option><option value="eggs">Eggs</option>
                <option value="weight">Weight</option><option value="wool">Wool</option>
            </select>
            <button class="btn" onclick="showAnalytics()">View Analytics</button>
        </div>
        <div id="analytics-result"></div>
        <h2 style="font-size:16px;margin:16px 0 12px">Recent Records</h2>
        <table>
            <thead><tr><th>Date</th><th>Animal</th><th>Type</th><th>Value</th><th>Unit</th></tr></thead>
            <tbody>
                ${records.slice(0, 50).map(r => `<tr>
                    <td>${r.date}</td><td>${r.animal_name}</td><td>${r.type}</td>
                    <td>${r.value}</td><td>${r.unit}</td>
                </tr>`).join("")}
                ${records.length === 0 ? '<tr><td colspan="5" style="color:var(--text-secondary)">No production records.</td></tr>' : ''}
            </tbody>
        </table>
    `;
}

function showProductionForm() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    overlay.innerHTML = `
        <div class="modal">
            <h2>Record Production</h2>
            <div class="form-row">
                <div class="form-group"><label>Animal ID</label><input id="fp-animal" type="number" required></div>
                <div class="form-group"><label>Date</label><input id="fp-date" type="date"></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Type</label>
                    <select id="fp-type"><option value="milk">Milk</option><option value="eggs">Eggs</option><option value="weight">Weight</option><option value="wool">Wool</option><option value="other">Other</option></select>
                </div>
                <div class="form-group"><label>Value</label><input id="fp-value" type="number" step="0.1" required></div>
            </div>
            <div class="form-group"><label>Unit</label><input id="fp-unit" placeholder="liters, count, kg, etc." required></div>
            <div class="form-group"><label>Notes</label><textarea id="fp-notes"></textarea></div>
            <div class="form-actions">
                <button class="btn" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="saveProduction()">Save</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
}

async function saveProduction() {
    await api("/api/production/records", {
        method: "POST",
        body: JSON.stringify({
            animal_id: parseInt($("#fp-animal").value),
            type: $("#fp-type").value,
            value: parseFloat($("#fp-value").value),
            unit: $("#fp-unit").value,
            date: $("#fp-date").value || null,
            notes: $("#fp-notes").value,
        }),
    });
    $(".modal-overlay").remove();
    loadProduction();
}

async function showAnalytics() {
    const type = $("#pa-type").value;
    const data = await api(`/api/production/analytics?type=${type}`);
    const s = data.summary;

    $("#analytics-result").innerHTML = `
        <div class="stats-row">
            <div class="stat-card"><div class="stat-value">${s.count || 0}</div><div class="stat-label">Records</div></div>
            <div class="stat-card"><div class="stat-value">${s.total ? s.total.toFixed(1) : 0}</div><div class="stat-label">Total</div></div>
            <div class="stat-card"><div class="stat-value">${s.avg_value ? s.avg_value.toFixed(1) : 0}</div><div class="stat-label">Average</div></div>
            <div class="stat-card"><div class="stat-value">${s.max_value ? s.max_value.toFixed(1) : 0}</div><div class="stat-label">Max</div></div>
        </div>
        ${data.top_producers.length > 0 ? `
            <h3 style="font-size:14px;margin-bottom:8px">Top Producers</h3>
            <table><thead><tr><th>Animal</th><th>Records</th><th>Average</th><th>Total</th></tr></thead><tbody>
            ${data.top_producers.map(p => `<tr>
                <td>${p.name}</td><td>${p.record_count}</td>
                <td>${p.avg_value.toFixed(1)}</td><td>${p.total_value.toFixed(1)}</td>
            </tr>`).join("")}</tbody></table>
        ` : ''}
    `;
}

// --- Init ---
const loaders = { herd: loadHerd, breeding: loadBreeding, feed: loadFeed, vet: loadVet, production: loadProduction };
loadHerd();
