import { html, Component } from '../lib.js';

/**
 * Top header bar with system title, user info, and controls.
 * @param {{ username: string, onLogout: Function, onMenuToggle: Function }} props
 */
export function Header({ username, onLogout, onMenuToggle }) {
  return html`
    <header class="header">
      <div class="header-left">
        <button class="menu-toggle" onClick=${onMenuToggle} aria-label="Toggle menu">
          &#9776;
        </button>
        <span class="header-title">SURVIVE OS</span>
      </div>
      <div class="header-right">
        <span class="header-user">${username}</span>
        <button class="btn" onClick=${onLogout}>Logout</button>
      </div>
    </header>
  `;
}
