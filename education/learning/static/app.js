import { h, render } from 'https://esm.sh/preact';
import { useState, useEffect } from 'https://esm.sh/preact/hooks';
import htm from 'https://esm.sh/htm';

const html = htm.bind(h);

const api = (path, opts) => fetch(path, { headers: { 'Content-Type': 'application/json' }, ...opts }).then(r => r.json());

function App() {
    const [tab, setTab] = useState('apprenticeships');
    const tabs = [
        ['apprenticeships', 'Apprenticeships'],
        ['lessons', 'Lessons'],
        ['kids', 'Kids Corner'],
        ['library', 'Library'],
    ];

    return html`
        <div class="app-header"><h1>Education & Learning</h1></div>
        <div class="tabs">
            ${tabs.map(([id, label]) => html`
                <div class="tab ${tab === id ? 'active' : ''}" onClick=${() => setTab(id)}>${label}</div>
            `)}
        </div>
        <div class="content">
            ${tab === 'apprenticeships' && html`<${ApprenticeshipTab} />`}
            ${tab === 'lessons' && html`<${LessonsTab} />`}
            ${tab === 'kids' && html`<${KidsTab} />`}
            ${tab === 'library' && html`<${LibraryTab} />`}
        </div>
    `;
}

function ApprenticeshipTab() {
    const [apprentices, setApprentices] = useState([]);
    const [selected, setSelected] = useState(null);
    const [showForm, setShowForm] = useState(false);

    const load = () => api('/api/apprentices').then(setApprentices);
    useEffect(load, []);

    const addApprentice = (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        api('/api/apprentices', {
            method: 'POST',
            body: JSON.stringify(Object.fromEntries(fd)),
        }).then(() => { load(); setShowForm(false); });
    };

    const viewDetail = (id) => api(`/api/apprentices/${id}`).then(setSelected);

    const updateSkill = (apprenticeId, skillId, status) => {
        api(`/api/apprentices/${apprenticeId}/skills/${skillId}`, {
            method: 'PUT',
            body: JSON.stringify({ status }),
        }).then(setSelected);
    };

    const statusCycle = { not_started: 'in_progress', in_progress: 'demonstrated', demonstrated: 'certified', certified: 'not_started' };

    return html`
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
            <h2>Apprenticeships</h2>
            <button onClick=${() => setShowForm(!showForm)}>${showForm ? 'Cancel' : 'Add Apprentice'}</button>
        </div>

        ${showForm && html`
            <div class="card">
                <form onSubmit=${addApprentice}>
                    <div class="form-row">
                        <div><label>Name</label><input name="person_name" required /></div>
                        <div><label>Trade</label><input name="trade" required placeholder="farming, medical, mechanical..." /></div>
                        <div><label>Mentor</label><input name="mentor_name" /></div>
                    </div>
                    <button type="submit">Enroll Apprentice</button>
                </form>
            </div>
        `}

        ${selected ? html`
            <button class="secondary" onClick=${() => setSelected(null)} style="margin-bottom:1rem">Back to list</button>
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <h3>${selected.person_name}</h3>
                    <span class="badge badge-${selected.status}">${selected.status}</span>
                </div>
                <div style="font-size:0.85rem;color:#8b949e;margin-bottom:0.5rem">
                    Trade: ${selected.trade} | Mentor: ${selected.mentor_name || 'None'} | Started: ${selected.start_date}
                </div>
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem">
                    <span style="font-size:0.85rem">Progress: ${selected.progress_pct}%</span>
                </div>
                <div class="progress-bar"><div class="progress-fill" style="width:${selected.progress_pct}%"></div></div>

                <h4 style="margin-top:1rem;margin-bottom:0.5rem">Skills Checklist</h4>
                ${(selected.skills || []).map(s => html`
                    <div class="skill-item" key=${s.skill_id}>
                        <span>${s.skill_name}</span>
                        <span class="skill-status skill-${s.status}" onClick=${() => updateSkill(selected.id, s.skill_id, statusCycle[s.status] || 'not_started')}>
                            ${s.status.replace(/_/g, ' ')}
                        </span>
                    </div>
                `)}
            </div>
        ` : html`
            <div class="grid">
                ${apprentices.map(a => html`
                    <div class="card" onClick=${() => viewDetail(a.id)} style="cursor:pointer" key=${a.id}>
                        <div style="display:flex;justify-content:space-between">
                            <h3>${a.person_name}</h3>
                            <span class="badge badge-${a.status}">${a.status}</span>
                        </div>
                        <div style="font-size:0.85rem;color:#8b949e">${a.trade} | Mentor: ${a.mentor_name || 'None'}</div>
                    </div>
                `)}
            </div>
            ${apprentices.length === 0 && html`<div class="empty">No apprentices enrolled yet.</div>`}
        `}
    `;
}

function LessonsTab() {
    const [lessons, setLessons] = useState([]);
    const [search, setSearch] = useState('');
    const [expanded, setExpanded] = useState(null);

    useEffect(() => { api('/api/lessons').then(setLessons); }, []);

    const doSearch = () => {
        if (search) api(`/api/lessons/search?q=${encodeURIComponent(search)}`).then(setLessons);
        else api('/api/lessons').then(setLessons);
    };

    return html`
        <h2 style="margin-bottom:1rem">Lesson Plans</h2>
        <div class="search-box form-row">
            <input value=${search} onInput=${e => setSearch(e.target.value)} placeholder="Search lessons..." onKeyDown=${e => e.key === 'Enter' && doSearch()} />
            <button onClick=${doSearch}>Search</button>
        </div>
        <div class="grid">
            ${lessons.map(l => html`
                <div class="card" onClick=${() => setExpanded(expanded === l.id ? null : l.id)} style="cursor:pointer" key=${l.id}>
                    <h3>${l.title}</h3>
                    <div style="font-size:0.85rem;color:#8b949e">${l.subject} | ${l.age_group} | ${l.duration}</div>
                    ${expanded === l.id && html`
                        <div style="margin-top:0.75rem">
                            ${l.objectives.length > 0 && html`
                                <div><strong>Objectives:</strong>
                                    <ul style="padding-left:1.25rem">${l.objectives.map(o => html`<li>${o}</li>`)}</ul>
                                </div>
                            `}
                            ${l.materials_needed.length > 0 && html`
                                <div style="margin-top:0.5rem"><strong>Materials:</strong> ${l.materials_needed.join(', ')}</div>
                            `}
                            ${l.procedure.length > 0 && html`
                                <div style="margin-top:0.5rem"><strong>Procedure:</strong>
                                    <ol class="steps">${l.procedure.map(s => html`<li>${s}</li>`)}</ol>
                                </div>
                            `}
                            ${l.assessment && html`<div style="margin-top:0.5rem"><strong>Assessment:</strong> ${l.assessment}</div>`}
                        </div>
                    `}
                </div>
            `)}
        </div>
    `;
}

function KidsTab() {
    const [mode, setMode] = useState('menu');
    const [problems, setProblems] = useState([]);
    const [answers, setAnswers] = useState({});
    const [score, setScore] = useState(null);
    const [name, setName] = useState('');
    const [mathType, setMathType] = useState('addition');
    const [difficulty, setDifficulty] = useState(1);

    const startQuiz = () => {
        api(`/api/children/math?type=${mathType}&difficulty=${difficulty}&count=5`).then(p => {
            setProblems(p);
            setAnswers({});
            setScore(null);
            setMode('quiz');
        });
    };

    const submitQuiz = () => {
        const answerList = problems.map((p, i) => ({
            question: p.question,
            user_answer: parseInt(answers[i]) || 0,
            correct_answer: p.answer,
        }));
        api('/api/children/math/submit', {
            method: 'POST',
            body: JSON.stringify({ child_name: name || 'Anonymous', exercise_type: mathType, difficulty, answers: answerList }),
        }).then(r => { setScore(r); setMode('result'); });
    };

    return html`
        <div class="kids-section">
            <h2 style="margin-bottom:1rem">Kids Corner</h2>

            ${mode === 'menu' && html`
                <div class="card">
                    <h3>Math Quiz</h3>
                    <div class="form-row">
                        <div><label>Your Name</label><input value=${name} onInput=${e => setName(e.target.value)} placeholder="Enter your name" /></div>
                        <div><label>Type</label>
                            <select value=${mathType} onChange=${e => setMathType(e.target.value)}>
                                <option value="addition">Addition (+)</option>
                                <option value="subtraction">Subtraction (-)</option>
                                <option value="multiplication">Multiplication (x)</option>
                                <option value="division">Division (/)</option>
                            </select>
                        </div>
                        <div><label>Difficulty (1-5)</label>
                            <select value=${difficulty} onChange=${e => setDifficulty(+e.target.value)}>
                                ${[1,2,3,4,5].map(d => html`<option value=${d}>${d}</option>`)}
                            </select>
                        </div>
                    </div>
                    <button onClick=${startQuiz} style="margin-top:0.5rem">Start Quiz!</button>
                </div>
            `}

            ${mode === 'quiz' && html`
                <div>
                    <h3 style="margin-bottom:1rem">Solve these problems:</h3>
                    ${problems.map((p, i) => html`
                        <div class="quiz-problem" key=${i}>
                            <span class="question">${p.question} = </span>
                            <input type="number" value=${answers[i] || ''} onInput=${e => setAnswers({...answers, [i]: e.target.value})} />
                        </div>
                    `)}
                    <button onClick=${submitQuiz}>Submit Answers</button>
                    <button class="secondary" onClick=${() => setMode('menu')} style="margin-left:0.5rem">Cancel</button>
                </div>
            `}

            ${mode === 'result' && score && html`
                <div>
                    <div class="score-display">${score.score} / ${score.total} correct (${score.percentage}%)</div>
                    <div style="margin-top:1rem;display:flex;gap:0.5rem">
                        <button onClick=${startQuiz}>Try Again</button>
                        <button class="secondary" onClick=${() => setMode('menu')}>Back to Menu</button>
                    </div>
                </div>
            `}
        </div>
    `;
}

function LibraryTab() {
    const [resources, setResources] = useState([]);
    useEffect(() => { api('/api/external/resources').then(setResources); }, []);

    return html`
        <h2 style="margin-bottom:1rem">Library Resources</h2>
        <div class="grid">
            ${resources.map(r => html`
                <div class="card resource-card" key=${r.type}>
                    <div>
                        <h3>${r.name}</h3>
                        <div style="font-size:0.85rem;color:#8b949e">${r.path || 'Not configured'}</div>
                    </div>
                    <span class="badge ${r.available ? 'badge-available' : 'badge-not-installed'}">
                        ${r.available ? 'Available' : 'Not Installed'}
                    </span>
                </div>
            `)}
        </div>
        ${resources.length === 0 && html`<div class="empty">Loading resources...</div>`}
    `;
}

render(html`<${App} />`, document.getElementById('app'));
