import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

async function api(path, opts = {}) {
    const res = await fetch(`/api${path}`, {
        headers: { 'Content-Type': 'application/json', ...opts.headers },
        ...opts,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
}

function App() {
    const [view, setView] = useState('topics');
    const [topicId, setTopicId] = useState(null);
    const [threadId, setThreadId] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');

    const navigate = (v, tid, thid) => { setView(v); setTopicId(tid || null); setThreadId(thid || null); };

    return html`
        <header>
            <h1>SURVIVE OS // Community BBS</h1>
            <nav>
                <a href="#" onClick=${() => navigate('topics')}>Topics</a>
                <a href="#" onClick=${() => navigate('search')}>Search</a>
            </nav>
        </header>
        <div class="container">
            ${view === 'topics' && html`<${TopicList} onSelect=${id => navigate('threads', id)} />`}
            ${view === 'threads' && html`<${ThreadList} topicId=${topicId} onSelect=${id => navigate('thread', topicId, id)} onBack=${() => navigate('topics')} />`}
            ${view === 'thread' && html`<${ThreadView} threadId=${threadId} onBack=${() => navigate('threads', topicId)} />`}
            ${view === 'search' && html`<${SearchView} />`}
        </div>
    `;
}

function TopicList({ onSelect }) {
    const [topics, setTopics] = useState([]);
    useEffect(() => { api('/topics').then(setTopics); }, []);

    return html`
        <h2>Topics</h2>
        <ul class="topic-list">
            ${topics.map(t => html`
                <li class="topic-item" onClick=${() => onSelect(t.id)}>
                    <div>
                        <strong>${t.name}</strong>
                        ${t.description && html`<div style="font-size:0.85rem;color:var(--text-muted)">${t.description}</div>`}
                    </div>
                    <span class="count">${t.thread_count} threads</span>
                </li>
            `)}
        </ul>
    `;
}

function ThreadList({ topicId, onSelect, onBack }) {
    const [threads, setThreads] = useState([]);
    const [topic, setTopic] = useState(null);
    const [showForm, setShowForm] = useState(false);

    useEffect(() => {
        api(`/topics/${topicId}`).then(setTopic);
        api(`/topics/${topicId}/threads`).then(setThreads);
    }, [topicId]);

    const createThread = async (title, author, content) => {
        await api('/threads', { method: 'POST', body: { topic_id: topicId, title, author, content } });
        api(`/topics/${topicId}/threads`).then(setThreads);
        setShowForm(false);
    };

    return html`
        <div class="breadcrumb"><a href="#" onClick=${onBack}>Topics</a> / ${topic?.name || '...'}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
            <h2>${topic?.name || 'Loading...'}</h2>
            <button class="btn" onClick=${() => setShowForm(!showForm)}>New Thread</button>
        </div>
        ${showForm && html`<${ComposeThread} onSubmit=${createThread} onCancel=${() => setShowForm(false)} />`}
        <ul class="thread-list">
            ${threads.map(t => html`
                <li class="thread-item" onClick=${() => onSelect(t.id)}>
                    <div>
                        ${t.pinned ? html`<span class="badge badge-pinned">PIN</span> ` : ''}
                        ${t.locked ? html`<span class="badge badge-locked">LOCKED</span> ` : ''}
                        <strong>${t.title}</strong>
                        <div style="font-size:0.85rem;color:var(--text-muted)">by ${t.author}</div>
                    </div>
                    <span class="meta">${t.post_count} posts</span>
                </li>
            `)}
            ${threads.length === 0 && html`<li style="color:var(--text-muted);padding:1rem">No threads yet.</li>`}
        </ul>
    `;
}

function ComposeThread({ onSubmit, onCancel }) {
    const [title, setTitle] = useState('');
    const [author, setAuthor] = useState('');
    const [content, setContent] = useState('');

    return html`
        <div style="background:var(--surface);border:1px solid var(--border);padding:1rem;margin-bottom:1rem;border-radius:4px">
            <div class="form-group"><label>Author</label><input value=${author} onInput=${e => setAuthor(e.target.value)} placeholder="Your name" /></div>
            <div class="form-group"><label>Title</label><input value=${title} onInput=${e => setTitle(e.target.value)} placeholder="Thread title" /></div>
            <div class="form-group"><label>Message</label><textarea value=${content} onInput=${e => setContent(e.target.value)} placeholder="Your message..." /></div>
            <button class="btn" onClick=${() => title && author && content && onSubmit(title, author, content)}>Post</button>
            <button class="btn btn-danger" style="margin-left:0.5rem" onClick=${onCancel}>Cancel</button>
        </div>
    `;
}

function ThreadView({ threadId, onBack }) {
    const [thread, setThread] = useState(null);
    const [posts, setPosts] = useState([]);
    const [replyAuthor, setReplyAuthor] = useState('');
    const [replyContent, setReplyContent] = useState('');
    const [replyTo, setReplyTo] = useState(null);

    const load = () => {
        api(`/threads/${threadId}`).then(setThread);
        api(`/threads/${threadId}/posts`).then(setPosts);
    };
    useEffect(load, [threadId]);

    const submitReply = async () => {
        if (!replyAuthor || !replyContent) return;
        await api(`/threads/${threadId}/posts`, {
            method: 'POST',
            body: { author: replyAuthor, content: replyContent, parent_id: replyTo },
        });
        setReplyContent('');
        setReplyTo(null);
        load();
    };

    return html`
        <div class="breadcrumb"><a href="#" onClick=${onBack}>Back</a> / ${thread?.title || '...'}</div>
        <h2>${thread?.title || 'Loading...'}</h2>
        <div style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem">by ${thread?.author} in ${thread?.topic_name}</div>
        <div class="post-list">
            ${posts.map(p => html`
                <div class="post-item ${p.parent_id ? 'reply' : ''}">
                    <div class="post-header">
                        <span><strong>${p.author}</strong></span>
                        <span>${new Date(p.created_at).toLocaleString()}</span>
                    </div>
                    <div class="post-content">${p.content}</div>
                    ${!thread?.locked && html`
                        <div class="post-actions">
                            <a href="#" onClick=${() => setReplyTo(p.id)}>Reply</a>
                        </div>
                    `}
                </div>
            `)}
        </div>
        ${!thread?.locked && html`
            <div style="margin-top:1rem;background:var(--surface);border:1px solid var(--border);padding:1rem;border-radius:4px">
                <h3 style="margin-bottom:0.5rem">${replyTo ? `Replying to post #${replyTo}` : 'Reply'}</h3>
                ${replyTo && html`<a href="#" style="font-size:0.85rem" onClick=${() => setReplyTo(null)}>Cancel reply</a>`}
                <div class="form-group"><label>Author</label><input value=${replyAuthor} onInput=${e => setReplyAuthor(e.target.value)} placeholder="Your name" /></div>
                <div class="form-group"><label>Message</label><textarea value=${replyContent} onInput=${e => setReplyContent(e.target.value)} placeholder="Your reply..." /></div>
                <button class="btn" onClick=${submitReply}>Post Reply</button>
            </div>
        `}
    `;
}

function SearchView() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [searched, setSearched] = useState(false);

    const doSearch = async () => {
        if (!query) return;
        const r = await api(`/search?q=${encodeURIComponent(query)}`);
        setResults(r);
        setSearched(true);
    };

    return html`
        <h2>Search</h2>
        <div class="search-bar" style="display:flex;gap:0.5rem">
            <input value=${query} onInput=${e => setQuery(e.target.value)} onKeyDown=${e => e.key === 'Enter' && doSearch()} placeholder="Search posts..." />
            <button class="btn" onClick=${doSearch}>Search</button>
        </div>
        ${searched && html`<p style="color:var(--text-muted);margin-bottom:1rem">${results.length} result(s)</p>`}
        <div class="post-list">
            ${results.map(r => html`
                <div class="post-item">
                    <div class="post-header">
                        <span><strong>${r.author}</strong> in ${r.topic_name} / ${r.thread_title}</span>
                    </div>
                    <div class="post-content">${r.content}</div>
                </div>
            `)}
        </div>
    `;
}

render(html`<${App} />`, document.getElementById('app'));
