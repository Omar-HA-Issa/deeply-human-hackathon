import countries from "world-countries";

export type CountryStatus = "locked" | "available" | "completed";

export type CountryPin = {
  code: string;
  name: string;
  lat: number;
  lng: number;
  status: CountryStatus;
};

export function buildAllCountryPins(
  statusByCode: Record<string, CountryStatus> = {}
): CountryPin[] {
  return (countries as Array<Record<string, unknown>>)
    .map((country) => {
      const latlng = country.latlng as number[] | undefined;
      const code = country.cca2 as string | undefined;
      const name = (country.name as { common?: string } | undefined)?.common;

      if (!latlng || latlng.length < 2 || !code || !name) {
        return null;
      }

      const normalizedCode = code.toUpperCase();
      return {
        code: normalizedCode,
        name,
        lat: latlng[0],
        lng: latlng[1],
        status: statusByCode[normalizedCode] ?? "locked",
      } satisfies CountryPin;
    })
    .filter(Boolean) as CountryPin[];
}
