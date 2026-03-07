import { html, Component } from '../lib.js';

/**
 * Login page - authenticates user against LLDAP via the server API.
 */
export class LoginPage extends Component {
  constructor() {
    super();
    this.state = {
      username: '',
      password: '',
      error: '',
      loading: false,
    };
  }

  handleSubmit = async (e) => {
    e.preventDefault();
    const { username, password } = this.state;

    if (!username || !password) {
      this.setState({ error: 'Username and password are required' });
      return;
    }

    this.setState({ loading: true, error: '' });

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();

      if (!res.ok) {
        this.setState({ error: data.error || 'Authentication failed', loading: false });
        return;
      }

      this.props.onLogin(data);
    } catch {
      this.setState({ error: 'Connection failed. Is the server running?', loading: false });
    }
  };

  render() {
    const { username, password, error, loading } = this.state;

    return html`
      <div class="login-page">
        <div class="login-card">
          <h1>SURVIVE OS</h1>
          <form onSubmit=${this.handleSubmit}>
            <div class="form-group">
              <label for="username">Username</label>
              <input
                id="username"
                type="text"
                value=${username}
                onInput=${(e) => this.setState({ username: e.target.value })}
                placeholder="Enter username"
                autocomplete="username"
                disabled=${loading}
              />
            </div>
            <div class="form-group">
              <label for="password">Password</label>
              <input
                id="password"
                type="password"
                value=${password}
                onInput=${(e) => this.setState({ password: e.target.value })}
                placeholder="Enter password"
                autocomplete="current-password"
                disabled=${loading}
              />
            </div>
            <button class="btn btn-primary" type="submit" disabled=${loading}>
              ${loading ? 'Authenticating...' : 'Login'}
            </button>
            ${error && html`<div class="login-error">${error}</div>`}
          </form>
        </div>
      </div>
    `;
  }
}
