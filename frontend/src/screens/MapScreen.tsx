import { useMemo, useRef, useState } from "react";
import Globe, { GlobeMethods } from "react-globe.gl";
import "./MapScreen.css";

type CountryPin = {
  name: string;
  lat: number;
  lng: number;
  size: number;
  color: string;
};

export function MapScreen() {
  const globeRef = useRef<GlobeMethods | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  const countryPins = useMemo<CountryPin[]>(
    () => [
      { name: "Mexico", lat: 23.6345, lng: -102.5528, size: 0.32, color: "#6EE7B7" },
      { name: "Japan", lat: 36.2048, lng: 138.2529, size: 0.3, color: "#93C5FD" },
      { name: "Kenya", lat: -0.0236, lng: 37.9062, size: 0.28, color: "#FCA5A5" },
      { name: "Norway", lat: 60.472, lng: 8.4689, size: 0.28, color: "#FDE68A" },
      { name: "Brazil", lat: -14.235, lng: -51.9253, size: 0.34, color: "#A7F3D0" },
      { name: "India", lat: 20.5937, lng: 78.9629, size: 0.33, color: "#C4B5FD" },
      { name: "Canada", lat: 56.1304, lng: -106.3468, size: 0.3, color: "#FDBA74" }
    ],
    []
  );

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
              pointAltitude={(point) => (point as CountryPin).size}
              pointRadius={0.12}
              pointColor={(point) => (point as CountryPin).color}
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
