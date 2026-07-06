import { useState } from "react";
import { login } from "../api";
import PasswordField from "./PasswordField";

function Login({ onLoggedIn }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { access_token } = await login(username, password);
      onLoggedIn(access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <div className="app-shell narrow-shell login-shell">
        <section className="card">
          <p className="eyebrow">Aletheia Investigation Workbench</p>
          <h2>Sign in</h2>
          <form onSubmit={handleSubmit}>
            <label>
              Username
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
              />
            </label>
            <PasswordField
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button type="submit" disabled={loading || !username || !password}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
            {error && <p className="error-text">{error}</p>}
          </form>
        </section>
      </div>
    </main>
  );
}

export default Login;
