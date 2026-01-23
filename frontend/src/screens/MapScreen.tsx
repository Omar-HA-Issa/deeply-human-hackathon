import { useEffect, useMemo, useRef, useState } from "react";
import Globe, { GlobeMethods } from "react-globe.gl";
import { feature } from "topojson-client";
import { fetchAvailableCountryCodes } from "../api/countries";
import { UserStats } from "../api/stats";
import {
  buildRoadmapPins,
  CountryPin,
  CountryStatus,
  getCountryByNumericCode,
} from "../data/countries";
import { SocialScreen } from "./SocialScreen";
import "./MapScreen.css";

const startCode = "ES";

const statusColor: Record<CountryStatus, string> = {
  locked: "#F87171",
  available: "#60A5FA",
  completed: "#34D399",
};

const statusAltitude: Record<CountryStatus, number> = {
  locked: 0.08,
  available: 0.12,
  completed: 0.16,
};

type MapScreenProps = {
  user: { username: string } | null;
  completedCodes: string[];
  stats: UserStats | null;
  onSignIn: () => void;
  onSignOut: () => void;
};

export function MapScreen({ user, completedCodes, stats, onSignIn, onSignOut }: MapScreenProps) {
  const globeRef = useRef<GlobeMethods | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"roadmap" | "social">("roadmap");
  const [countryBorders, setCountryBorders] = useState<Array<unknown>>([]);
  const [availableCodes, setAvailableCodes] = useState<string[] | null>(null);

  const countriesExplored = stats?.countries_completed ?? completedCodes.length;
  const accuracyPercent = stats ? Math.round((stats.accuracy || 0) * 100) : 0;
  const streakDays = stats?.streak_days ?? 0;

  const countryPins = useMemo(
    () =>
      buildRoadmapPins({
        startCode,
        completedCodes,
        allowedCodes: user ? undefined : (availableCodes ?? undefined),
        includeSeaNeighbors: true,
        seaNeighborKm: 600,
        maxSeaNeighbors: 3,
      }),
    [completedCodes, availableCodes, user]
  );

  useEffect(() => {
    let isMounted = true;
    fetchAvailableCountryCodes()
      .then((codes) => {
        if (isMounted) {
          setAvailableCodes(codes);
        }
      })
      .catch(() => {
        if (isMounted) {
          setAvailableCodes(null);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    fetch("https://unpkg.com/world-atlas@2/countries-110m.json")
      .then((response) => response.json())
      .then((worldData) => {
        const collection = feature(
          worldData,
          worldData.objects.countries
        ) as { features: Array<unknown> };
        const mapped = collection.features.map((polygon) => {
          const polygonData = polygon as {
            id?: number | string;
            properties?: Record<string, unknown>;
          };
          const numericId = polygonData.id ?? "";
          const country = getCountryByNumericCode(numericId);
          return {
            ...polygonData,
            properties: {
              ...polygonData.properties,
              code: country?.code,
              name: country?.name,
            },
          };
        });
        if (isMounted) {
          setCountryBorders(mapped);
        }
      })
      .catch(() => {
        if (isMounted) {
          setCountryBorders([]);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleStartQuiz = (country: CountryPin) => {
    if (country.status === "locked") {
      return;
    }
    setSelectedCountry(country.name);
    const query = new URLSearchParams({
      code: country.code,
      name: country.name,
    });
    window.location.hash = `quiz?${query.toString()}`;
  };

  const handleCountryClick = (polygon: unknown) => {
    const props = (polygon as { properties?: { code?: string; name?: string } })
      .properties;
    const code = props?.code;
    if (!code) {
      return;
    }
    const pin = countryPins.find((item) => item.code === code);
    if (!pin) {
      return;
    }
    handleStartQuiz(pin);
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
        <button
          className={`tab ${activeTab === "roadmap" ? "active" : ""}`}
          onClick={() => setActiveTab("roadmap")}
        >
          Roadmap
        </button>
        <button
          className={`tab ${activeTab === "social" ? "active" : ""}`}
          onClick={() => setActiveTab("social")}
        >
          Social
        </button>
      </nav>

      {activeTab === "roadmap" ? (
        <main className="main-grid">
          <section className="card stats-card">
            <h3>Your stats</h3>
            <div className="stats-grid">
              <div className="stat">
                <span className="stat-label">Countries explored</span>
                <span className="stat-value">{countriesExplored}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Accuracy</span>
                <span className="stat-value">{accuracyPercent}%</span>
              </div>
              <div className="stat">
                <span className="stat-label">Streak</span>
                <span className="stat-value">{streakDays} days</span>
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
                polygonsData={countryBorders}
                polygonAltitude={0.01}
                polygonCapColor={() => "rgba(12, 18, 38, 0.35)"}
                polygonSideColor={() => "rgba(12, 18, 38, 0.15)"}
                polygonStrokeColor={() => "rgba(148, 163, 184, 0.5)"}
                pointsData={countryPins}
                pointLat={(point) => (point as CountryPin).lat}
                pointLng={(point) => (point as CountryPin).lng}
                pointAltitude={(point) =>
                  statusAltitude[(point as CountryPin).status]
                }
                pointRadius={0.24}
                pointColor={(point) => statusColor[(point as CountryPin).status]}
                pointLabel={(point) => (point as CountryPin).name}
                onPointClick={(point) => handleStartQuiz(point as CountryPin)}
                onPolygonClick={(polygon) => handleCountryClick(polygon)}
                onGlobeReady={() => {
                  const controls = globeRef.current?.controls();
                  if (controls) {
                    controls.autoRotate = false;
                  }
                }}
              />
            </div>
          </section>
        </main>
      ) : (
        <SocialScreen user={user} onSignIn={onSignIn} />
      )}
    </div>
  );
}
