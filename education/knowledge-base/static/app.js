/** @type {Array<{id:number, name:string, slug:string, description:string}>} */
let categories = [];

const $ = (sel) => document.querySelector(sel);
const show = (el) => el.classList.remove("hidden");
const hide = (el) => el.classList.add("hidden");

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

/** Simple markdown to HTML converter for article content. */
function renderMarkdown(text) {
    let html = text
        // Escape HTML
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Code blocks (``` ... ```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
        `<pre><code>${code.trim()}</code></pre>`
    );

    // Inline code
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Headers
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

    // Bold and italic
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

    // Blockquotes
    html = html.replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>");

    // Horizontal rules
    html = html.replace(/^---$/gm, "<hr>");

    // Tables
    html = html.replace(/^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)/gm, (_, header, sep, body) => {
        const ths = header.split("|").filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join("");
        const rows = body.trim().split("\n").map(row => {
            const tds = row.split("|").filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join("");
            return `<tr>${tds}</tr>`;
        }).join("");
        return `<table><thead><tr>${ths}</tr></thead><tbody>${rows}</tbody></table>`;
    });

    // Unordered lists
    html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`);

    // Ordered lists
    html = html.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");
    // Wrap consecutive <li> not already in <ul> into <ol>
    html = html.replace(/(?<!<\/ul>)\n?(<li>.*<\/li>\n?)+/g, (match) => {
        if (match.includes("<ul>")) return match;
        return `<ol>${match}</ol>`;
    });

    // Paragraphs - wrap remaining lines
    html = html.replace(/^(?!<[hupoltb]|<\/|<hr|<blockquote|<pre)(.+)$/gm, "<p>$1</p>");

    // Clean up double marks from seed data that uses <mark>
    html = html.replace(/&lt;mark&gt;/g, "<mark>");
    html = html.replace(/&lt;\/mark&gt;/g, "</mark>");

    return html;
}

function showView(viewId) {
    ["#welcome", "#article-list", "#article-view", "#search-results"].forEach(id => {
        hide($(id));
    });
    show($(viewId));
}

async function loadCategories() {
    categories = await fetchJSON("/api/categories");
    const sidebar = $("#categories");
    const cards = $("#category-cards");

    sidebar.innerHTML = categories.map(c =>
        `<div class="category-item" data-slug="${c.slug}">${c.name}</div>`
    ).join("");

    cards.innerHTML = categories.map(c =>
        `<div class="category-card" data-slug="${c.slug}">
            <h3>${c.name}</h3>
            <p>${c.description}</p>
        </div>`
    ).join("");

    sidebar.addEventListener("click", (e) => {
        const item = e.target.closest(".category-item");
        if (item) loadCategory(item.dataset.slug);
    });

    cards.addEventListener("click", (e) => {
        const card = e.target.closest(".category-card");
        if (card) loadCategory(card.dataset.slug);
    });
}

function setActiveCategory(slug) {
    document.querySelectorAll(".category-item").forEach(el => {
        el.classList.toggle("active", el.dataset.slug === slug);
    });
}

async function loadCategory(slug) {
    setActiveCategory(slug);
    const articles = await fetchJSON(`/api/articles?category=${slug}`);
    const cat = categories.find(c => c.slug === slug);
    const container = $("#article-list");

    container.innerHTML = `
        <div class="article-list-header">
            <button class="back-btn" onclick="goHome()">Back</button>
            <h2>${cat ? cat.name : slug}</h2>
        </div>
        ${articles.map(a => `
            <div class="article-card" onclick="loadArticle(${a.id})">
                <h3>${a.title}</h3>
                <div class="summary">${a.summary}</div>
            </div>
        `).join("")}
        ${articles.length === 0 ? "<p>No articles in this category yet.</p>" : ""}
    `;
    showView("#article-list");
}

async function loadArticle(id) {
    const article = await fetchJSON(`/api/articles/${id}`);
    const container = $("#article-view");

    container.innerHTML = `
        <div class="article-header">
            <button class="back-btn" onclick="loadCategory('${article.category_slug}')">Back to ${article.category}</button>
            <span class="category-tag">${article.category}</span>
            <h1>${article.title}</h1>
            <div class="meta">By ${article.author} | Updated ${article.updated_at}</div>
        </div>
        <div class="article-body">${renderMarkdown(article.content)}</div>
    `;
    showView("#article-view");
}

async function doSearch(query) {
    if (!query.trim()) {
        goHome();
        return;
    }
    setActiveCategory("");
    const results = await fetchJSON(`/api/search?q=${encodeURIComponent(query)}`);
    const container = $("#search-results");

    container.innerHTML = `
        <div class="article-list-header">
            <button class="back-btn" onclick="goHome()">Back</button>
            <h2>Search: "${query}" (${results.length} results)</h2>
        </div>
        ${results.map(a => `
            <div class="article-card" onclick="loadArticle(${a.id})">
                <h3>${a.title}</h3>
                <div class="summary">${a.summary}</div>
                <div class="search-snippet">${a.snippet || ""}</div>
                <div class="meta">${a.category}</div>
            </div>
        `).join("")}
        ${results.length === 0 ? "<p>No results found.</p>" : ""}
    `;
    showView("#search-results");
}

function goHome() {
    setActiveCategory("");
    showView("#welcome");
    $("#search-input").value = "";
}

// Initialize
let searchTimeout;
$("#search-input").addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => doSearch(e.target.value), 300);
});

$("#search-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        clearTimeout(searchTimeout);
        doSearch(e.target.value);
    }
});

loadCategories();
