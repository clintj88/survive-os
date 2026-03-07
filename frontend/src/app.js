import { html, Component, render } from './lib.js';
import { Header } from './components/header.js';
import { Sidebar } from './components/sidebar.js';
import { LoginPage } from './pages/login.js';
import { MODULES } from './modules.js';

/**
 * Root application component.
 * Manages authentication state and module routing.
 */
class App extends Component {
  constructor() {
    super();
    const token = localStorage.getItem('survive_token');
    const username = localStorage.getItem('survive_user');
    this.state = {
      authenticated: !!token,
      username: username || '',
      activeModule: null,
      sidebarOpen: false,
      moduleHealth: {},
    };
  }

  componentDidMount() {
    if (this.state.authenticated) {
      this.checkModuleHealth();
      this._healthInterval = setInterval(() => this.checkModuleHealth(), 30000);
    }
  }

  componentWillUnmount() {
    clearInterval(this._healthInterval);
  }

  /** Check health of all modules */
  async checkModuleHealth() {
    const health = { ...this.state.moduleHealth };
    await Promise.allSettled(
      MODULES.map(async (mod) => {
        try {
          const controller = new AbortController();
          const timeout = setTimeout(() => controller.abort(), 3000);
          const res = await fetch(`http://localhost:${mod.port}/health`, {
            signal: controller.signal,
          });
          clearTimeout(timeout);
          health[mod.id] = res.ok ? 'online' : 'offline';
        } catch {
          health[mod.id] = 'offline';
        }
      })
    );
    this.setState({ moduleHealth: health });
  }

  /** @param {{ token: string, username: string }} data */
  handleLogin = (data) => {
    localStorage.setItem('survive_token', data.token);
    localStorage.setItem('survive_user', data.username);
    this.setState({ authenticated: true, username: data.username });
    this.checkModuleHealth();
    this._healthInterval = setInterval(() => this.checkModuleHealth(), 30000);
  };

  handleLogout = () => {
    localStorage.removeItem('survive_token');
    localStorage.removeItem('survive_user');
    clearInterval(this._healthInterval);
    this.setState({ authenticated: false, username: '', activeModule: null });
  };

  /** @param {string} moduleId */
  handleModuleSelect = (moduleId) => {
    this.setState({ activeModule: moduleId, sidebarOpen: false });
  };

  toggleSidebar = () => {
    this.setState((s) => ({ sidebarOpen: !s.sidebarOpen }));
  };

  render() {
    const { authenticated, username, activeModule, sidebarOpen, moduleHealth } = this.state;

    if (!authenticated) {
      return html`<${LoginPage} onLogin=${this.handleLogin} />`;
    }

    const activeMod = MODULES.find((m) => m.id === activeModule);

    return html`
      <div class="app-shell">
        <${Sidebar}
          modules=${MODULES}
          activeModule=${activeModule}
          health=${moduleHealth}
          open=${sidebarOpen}
          onSelect=${this.handleModuleSelect}
          onClose=${() => this.setState({ sidebarOpen: false })}
        />
        <div class="main-area">
          <${Header}
            username=${username}
            onLogout=${this.handleLogout}
            onMenuToggle=${this.toggleSidebar}
          />
          <div class="content">
            ${activeMod
              ? html`<iframe
                  class="module-frame"
                  src="http://localhost:${activeMod.port}"
                  title=${activeMod.name}
                />`
              : html`
                  <div class="welcome">
                    <h1>SURVIVE OS</h1>
                    <p>
                      Post-infrastructure operating system. Select a module from the
                      sidebar to begin.
                    </p>
                  </div>
                `}
          </div>
        </div>
      </div>
    `;
  }
}

render(html`<${App} />`, document.getElementById('app'));
