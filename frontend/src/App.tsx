import { useEffect, useMemo, useState } from "react";
import { AuthUser, logout, me } from "./api/auth";
import { AuthScreen } from "./screens/AuthScreen";
import { MapScreen } from "./screens/MapScreen";
import { QuizScreen } from "./screens/QuizScreen";

export function App() {
  const [hash, setHash] = useState(window.location.hash);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [completedCodes, setCompletedCodes] = useState<string[]>(["ES"]);

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
  const quizParams = useMemo(() => {
    if (!view.startsWith("quiz")) {
      return null;
    }
    const queryString = view.split("?")[1] || "";
    const params = new URLSearchParams(queryString);
    const name = params.get("name") ?? "";
    const code = params.get("code") ?? "";
    return { name, code };
  }, [view]);

  const handleLogout = async () => {
    await logout();
    setUser(null);
  };

  if (view.startsWith("auth")) {
    return <AuthScreen onAuthSuccess={setUser} />;
  }

  if (view.startsWith("quiz") && quizParams?.name && quizParams?.code) {
    return (
      <QuizScreen
        countryName={quizParams.name}
        countryCode={quizParams.code}
        onComplete={(passed) => {
          if (passed) {
            const normalizedCode = quizParams.code.toUpperCase();
            if (normalizedCode) {
              setCompletedCodes((prev) =>
                prev.includes(normalizedCode) ? prev : [...prev, normalizedCode]
              );
            }
          }
          window.location.hash = "";
        }}
      />
    );
  }

  return (
    <MapScreen
      user={user}
      completedCodes={completedCodes}
      onSignIn={() => {
        window.location.hash = "auth";
      }}
      onSignOut={handleLogout}
    />
  );
}
