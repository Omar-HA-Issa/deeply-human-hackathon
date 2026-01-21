import { useEffect, useMemo, useState } from "react";
import { AuthUser, logout, me } from "./api/auth";
import { AuthScreen } from "./screens/AuthScreen";
import { MapScreen } from "./screens/MapScreen";

export function App() {
  const [hash, setHash] = useState(window.location.hash);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const handleHashChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    me()
      .then((response) => setUser(response.user))
      .catch(() => setUser(null));
  }, []);

  const view = useMemo(() => hash.replace("#", ""), [hash]);

  const handleLogout = async () => {
    await logout();
    setUser(null);
  };

  if (view.startsWith("auth")) {
    return <AuthScreen onAuthSuccess={setUser} />;
  }

  return (
    <MapScreen
      user={user}
      onSignIn={() => {
        window.location.hash = "auth";
      }}
      onSignOut={handleLogout}
    />
  );
}
