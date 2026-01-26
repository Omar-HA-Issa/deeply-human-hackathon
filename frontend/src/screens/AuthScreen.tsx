import { useState } from "react";
import { AuthUser, login, register } from "../api/auth";
import { sendFriendRequest } from "../api/social";
import "./AuthScreen.css";

type AuthMode = "login" | "register";

type AuthScreenProps = {
  onAuthSuccess: (user: AuthUser) => void;
  initialMode?: AuthMode;
  inviteFrom?: string | null;
};

export function AuthScreen({
  onAuthSuccess,
  initialMode = "login",
  inviteFrom = null,
}: AuthScreenProps) {
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response =
        mode === "login"
          ? await login(username, password)
          : await register(username, email, password);
      onAuthSuccess(response.user);
      if (inviteFrom && response.user.username.toLowerCase() !== inviteFrom.toLowerCase()) {
        try {
          await sendFriendRequest(inviteFrom);
        } catch {
          // Ignore invite errors to avoid blocking auth flow.
        }
      }
      window.location.hash = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-header">
          <h1>WorldQuest</h1>
          <p>
            {mode === "login" ? "Welcome back" : "Create your account"}
            {inviteFrom ? ` to connect with ${inviteFrom}` : ""}
          </p>
        </div>

        <div className="auth-toggle">
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => setMode("login")}
            type="button"
          >
            Login
          </button>
          <button
            className={mode === "register" ? "active" : ""}
            onClick={() => setMode("register")}
            type="button"
          >
            Register
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="jane" />
          </label>

          {mode === "register" && (
            <label>
              Email
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                placeholder="jane@worldquest.com"
              />
            </label>
          )}

          <label>
            Password
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              placeholder="••••••••"
            />
          </label>

          {error && <div className="auth-error">{error}</div>}

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? "Working..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
