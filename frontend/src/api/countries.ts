import { getJson } from "./client";

type AvailableCountriesResponse = {
  countries: string[];
};

export async function fetchAvailableCountryCodes(): Promise<string[]> {
  const response = await getJson<AvailableCountriesResponse>(
    "/api/countries/available/"
  );
  return response.countries;
}
