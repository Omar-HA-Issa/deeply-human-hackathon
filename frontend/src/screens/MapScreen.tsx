import { useMemo, useRef, useState } from "react";
import Globe, { GlobeMethods } from "react-globe.gl";
import { buildRoadmapPins, CountryPin, CountryStatus } from "../data/countries";
import "./MapScreen.css";

const startCode = "ES";

const statusColor: Record<CountryStatus, string> = {
  locked: "rgba(148, 163, 184, 0.5)",
  available: "#93C5FD",
  completed: "#6EE7B7",
};

const statusAltitude: Record<CountryStatus, number> = {
  locked: 0.15,
  available: 0.25,
  completed: 0.3,
};

type MapScreenProps = {
  user: { username: string } | null;
  completedCodes: string[];
  onSignIn: () => void;
  onSignOut: () => void;
};

export function MapScreen({ user, completedCodes, onSignIn, onSignOut }: MapScreenProps) {
  const globeRef = useRef<GlobeMethods | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  const countryPins = useMemo(
    () => buildRoadmapPins({ startCode, completedCodes, singleAvailable: true }),
    [completedCodes]
  );

  const handleStartQuiz = (country: CountryPin) => {
    setSelectedCountry(country.name);
    const query = new URLSearchParams({
      code: country.code,
      name: country.name,
    });
    window.location.hash = `quiz?${query.toString()}`;
  };

  return (
    <div className="map-screen">
      <header className="top-header">
        <div className="logo">WorldQuest</div>
        <div className="tagline">Explore the world. Learn fast.</div>
        {user ? (
          <div className="auth-actions">
            <span className="auth-user">Hi, {user.username}</span>
            <button className="button ghost" onClick={onSignOut}>
              Sign out
            </button>
          </div>
        ) : (
          <button className="button ghost" onClick={onSignIn}>
            Sign in
          </button>
        )}
      </header>

      <nav className="tabs">
        <button className="tab active">Roadmap</button>
        <button className="tab">Social</button>
      </nav>

      <main className="main-grid">
        <section className="card stats-card">
          <h3>Your stats</h3>
          <div className="stats-grid">
            <div className="stat">
              <span className="stat-label">Countries explored</span>
              <span className="stat-value">12</span>
            </div>
            <div className="stat">
              <span className="stat-label">Accuracy</span>
              <span className="stat-value">78%</span>
            </div>
            <div className="stat">
              <span className="stat-label">Streak</span>
              <span className="stat-value">5 days</span>
            </div>
          </div>

          <div className="selected-country">
            <span>Selected</span>
            <strong>{selectedCountry ?? "Pick a pin"}</strong>
          </div>

        </section>

        <section className="card globe-card">
          <div className="globe-header">
            <div>
              <h2>Roadmap from Spain</h2>
              <p>Connected countries unlock next steps.</p>
            </div>
            <div className="chip">Live pins</div>
          </div>

          <div className="globe-wrapper">
            <Globe
              ref={globeRef}
              globeImageUrl="https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
              bumpImageUrl="https://unpkg.com/three-globe/example/img/earth-topology.png"
              backgroundColor="rgba(0,0,0,0)"
              pointsData={countryPins}
              pointLat={(point) => (point as CountryPin).lat}
              pointLng={(point) => (point as CountryPin).lng}
              pointAltitude={(point) => statusAltitude[(point as CountryPin).status]}
              pointRadius={0.12}
              pointColor={(point) => statusColor[(point as CountryPin).status]}
              pointLabel={(point) => (point as CountryPin).name}
              onPointClick={(point) => handleStartQuiz(point as CountryPin)}
              onGlobeReady={() => {
                const controls = globeRef.current?.controls();
                if (controls) {
                  controls.autoRotate = true;
                  controls.autoRotateSpeed = 0.4;
                }
              }}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
