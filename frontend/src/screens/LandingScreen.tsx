import { useEffect, useRef, useState } from "react";
import Globe, { GlobeMethods } from "react-globe.gl";
import { feature } from "topojson-client";
import "./LandingScreen.css";

type LandingScreenProps = {
  onSignIn: () => void;
  onSignUp: () => void;
};

export function LandingScreen({ onSignIn, onSignUp }: LandingScreenProps) {
  const globeRef = useRef<GlobeMethods | null>(null);
  const [countryBorders, setCountryBorders] = useState<Array<unknown>>([]);

  useEffect(() => {
    let isMounted = true;
    fetch("https://unpkg.com/world-atlas@2/countries-110m.json")
      .then((response) => response.json())
      .then((worldData) => {
        const collection = feature(
          worldData,
          worldData.objects.countries
        ) as { features: Array<unknown> };
        if (isMounted) {
          setCountryBorders(collection.features);
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

  return (
    <div className="landing-screen">
      <div className="landing-globe">
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
          onGlobeReady={() => {
            const controls = globeRef.current?.controls();
            if (controls) {
              controls.autoRotate = true;
              controls.autoRotateSpeed = 0.4;
              controls.enableZoom = false;
              controls.enablePan = false;
            }
          }}
        />
      </div>

      <div className="landing-content">
        <div className="landing-brand">WorldQuest</div>
        <h1>Explore the world. Learn fast.</h1>
        <p>Start your journey across the globe, one country at a time.</p>
        <div className="landing-actions">
          <button className="landing-primary" onClick={onSignIn}>
            Sign in
          </button>
          <button className="landing-secondary" onClick={onSignUp}>
            Sign up
          </button>
        </div>
      </div>
    </div>
  );
}
