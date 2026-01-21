import { useMemo, useRef, useState } from "react";
import Globe, { GlobeMethods } from "react-globe.gl";
import { buildAllCountryPins, CountryPin, CountryStatus } from "../data/countries";
import "./MapScreen.css";

const statusByCode: Record<string, CountryStatus> = {
  MX: "available",
  US: "completed",
  JP: "available",
  BR: "locked",
  CA: "completed",
};

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

export function MapScreen() {
  const globeRef = useRef<GlobeMethods | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  const countryPins = useMemo(() => buildAllCountryPins(statusByCode), []);

  const handleStartQuiz = (countryName: string) => {
    setSelectedCountry(countryName);
    window.location.hash = `quiz?country=${encodeURIComponent(countryName)}`;
  };

  const handleRandomQuiz = () => {
    const randomIndex = Math.floor(Math.random() * countryPins.length);
    const randomCountry = countryPins[randomIndex];
    handleStartQuiz(randomCountry.name);
  };

  return (
    <div className="map-screen">
      <header className="top-header">
        <div className="logo">WorldQuest</div>
        <div className="tagline">Explore the world. Learn fast.</div>
        <button className="button ghost">Sign in</button>
      </header>

      <nav className="tabs">
        <button className="tab active">Explore</button>
        <button className="tab">Roadmap</button>
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

          <button className="button primary" onClick={handleRandomQuiz}>
            Random Country Quiz
          </button>
        </section>

        <section className="card globe-card">
          <div className="globe-header">
            <div>
              <h2>Explore the globe</h2>
              <p>Hover for country names. Click to start a quiz.</p>
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
              onPointClick={(point) => handleStartQuiz((point as CountryPin).name)}
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
