import { html } from '../lib.js';

/**
 * Sidebar navigation listing all modules with health indicators.
 * @param {{
 *   modules: Array<{id: string, name: string, port: number, icon: string}>,
 *   activeModule: string|null,
 *   health: Record<string, string>,
 *   open: boolean,
 *   onSelect: (id: string) => void,
 *   onClose: () => void,
 * }} props
 */
export function Sidebar({ modules, activeModule, health, open, onSelect, onClose }) {
  const statusClass = (id) => {
    const h = health[id];
    if (h === 'online') return 'status-online';
    if (h === 'offline') return 'status-offline';
    return 'status-unknown';
  };

  return html`
    <div class="sidebar-overlay ${open ? 'open' : ''}" onClick=${onClose}></div>
    <nav class="sidebar ${open ? 'open' : ''}">
      <div class="sidebar-section">
        <div class="sidebar-section-title">Modules</div>
        ${modules.map(
          (mod) => html`
            <button
              key=${mod.id}
              class="nav-item ${activeModule === mod.id ? 'active' : ''}"
              onClick=${() => onSelect(mod.id)}
            >
              <span style="font-family: var(--font-mono); font-size: var(--font-size-sm); opacity: 0.6; width: 24px;">
                ${mod.icon}
              </span>
              <span>${mod.name}</span>
              <span class="nav-item-status">
                <span class="status-dot ${statusClass(mod.id)}"></span>
              </span>
            </button>
          `
        )}
      </div>
    </nav>
  `;
}
