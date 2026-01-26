import countries from "world-countries";

export type CountryStatus = "locked" | "available" | "completed";

export type CountryPin = {
  code: string;
  name: string;
  lat: number;
  lng: number;
  status: CountryStatus;
};

type CountryRecord = {
  cca2?: string;
  cca3?: string;
  ccn3?: string;
  latlng?: number[];
  name?: { common?: string };
  borders?: string[];
};

type CountryData = {
  code: string;
  numericCode?: string;
  name: string;
  lat: number;
  lng: number;
  borders: string[];
};

const EARTH_RADIUS_KM = 6371;

const toRadians = (value: number) => (value * Math.PI) / 180;

const distanceKm = (a: CountryData, b: CountryData) => {
  const latDelta = toRadians(b.lat - a.lat);
  const lngDelta = toRadians(b.lng - a.lng);
  const lat1 = toRadians(a.lat);
  const lat2 = toRadians(b.lat);

  const sinLat = Math.sin(latDelta / 2);
  const sinLng = Math.sin(lngDelta / 2);
  const haversine =
    sinLat * sinLat + Math.cos(lat1) * Math.cos(lat2) * sinLng * sinLng;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(haversine));
};

const buildSeaNeighborMap = (
  countries: CountryData[],
  maxDistanceKm: number,
  maxNeighbors: number
) => {
  const map = new Map<string, string[]>();

  countries.forEach((country) => {
    const distances = countries
      .filter((other) => other.code !== country.code)
      .map((other) => ({
        code: other.code,
        distance: distanceKm(country, other),
      }))
      .filter((entry) => entry.distance <= maxDistanceKm)
      .sort((a, b) => a.distance - b.distance)
      .slice(0, maxNeighbors)
      .map((entry) => entry.code);

    map.set(country.code, distances);
  });

  return map;
};

const countryData: CountryData[] = (() => {
  const records = countries as CountryRecord[];
  const cca3ToCca2: Record<string, string> = {};

  records.forEach((record) => {
    if (record.cca2 && record.cca3) {
      cca3ToCca2[record.cca3.toUpperCase()] = record.cca2.toUpperCase();
    }
  });

  return records
    .map((record) => {
      const latlng = record.latlng;
      const code = record.cca2;
      const name = record.name?.common;
      const numericCode = record.ccn3?.padStart(3, "0");

      if (!latlng || latlng.length < 2 || !code || !name) {
        return null;
      }

      const borders = (record.borders ?? [])
        .map((border) => cca3ToCca2[border.toUpperCase()])
        .filter(Boolean) as string[];

      return {
        code: code.toUpperCase(),
        numericCode,
        name,
        lat: latlng[0],
        lng: latlng[1],
        borders,
      } satisfies CountryData;
    })
    .filter(Boolean) as CountryData[];
})();

const numericCodeToCountry = new Map<string, CountryData>();

countryData.forEach((country) => {
  if (country.numericCode) {
    numericCodeToCountry.set(country.numericCode, country);
  }
});


export function buildAllCountryPins(
  statusByCode: Record<string, CountryStatus> = {}
): CountryPin[] {
  return countryData.map((country) => ({
    code: country.code,
    name: country.name,
    lat: country.lat,
    lng: country.lng,
    status: statusByCode[country.code] ?? "locked",
  }));
}

export function getCountryByNumericCode(numericCode: string | number) {
  const key = String(numericCode).padStart(3, "0");
  return numericCodeToCountry.get(key) ?? null;
}

export function buildRoadmapPins(options: {
  startCode?: string;
  startCodes?: string[];
  completedCodes?: string[];
  singleAvailable?: boolean;
  allowedCodes?: string[];
  includeSeaNeighbors?: boolean;
  seaNeighborKm?: number;
  maxSeaNeighbors?: number;
}): CountryPin[] {
  const allowedSet = options.allowedCodes
    ? new Set(options.allowedCodes.map((code) => code.toUpperCase()))
    : null;
  const filteredCountries = allowedSet
    ? countryData.filter((country) => allowedSet.has(country.code))
    : countryData;
  const seaNeighborMap = options.includeSeaNeighbors
    ? buildSeaNeighborMap(
        filteredCountries,
        options.seaNeighborKm ?? 600,
        options.maxSeaNeighbors ?? 3
      )
    : null;
  const normalizedStarts = (
    options.startCodes && options.startCodes.length > 0
      ? options.startCodes
      : options.startCode
        ? [options.startCode]
        : []
  ).map((code) => code.toUpperCase());
  const completedSet = new Set(
    (options.completedCodes ?? []).map((code) => code.toUpperCase())
  );

  const availableSet = new Set<string>();

  normalizedStarts.forEach((start) => {
    if (!completedSet.has(start)) {
      if (!allowedSet || allowedSet.has(start)) {
        availableSet.add(start);
      }
    }
  });

  filteredCountries.forEach((country) => {
    if (!completedSet.has(country.code)) {
      return;
    }

    country.borders.forEach((neighbor) => {
      if (!completedSet.has(neighbor) && (!allowedSet || allowedSet.has(neighbor))) {
        availableSet.add(neighbor);
      }
    });

    if (seaNeighborMap) {
      const seaNeighbors = seaNeighborMap.get(country.code) ?? [];
      seaNeighbors.forEach((neighbor) => {
        if (!completedSet.has(neighbor) && (!allowedSet || allowedSet.has(neighbor))) {
          availableSet.add(neighbor);
        }
      });
    }

  });

  if (options.singleAvailable && availableSet.size > 1) {
    const sorted = Array.from(availableSet).sort();
    availableSet.clear();
    availableSet.add(sorted[0]);
  }

  const baseCountries = allowedSet ? filteredCountries : countryData;

  return baseCountries.map((country) => {
    let status: CountryStatus = "locked";
    if (completedSet.has(country.code)) {
      status = "completed";
    } else if (availableSet.has(country.code)) {
      status = "available";
    }

    return {
      code: country.code,
      name: country.name,
      lat: country.lat,
      lng: country.lng,
      status,
    } satisfies CountryPin;
  });
}
