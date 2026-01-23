import { getJson } from "./client";

type ProgressResponse = {
  xp: number;
  quiz_points: number;
  match_points: number;
  xp_per_unlock: number;
  next_unlock_xp: number;
  unlocked_countries: string[];
  completed_countries: string[];
};

export type ProgressSnapshot = {
  xp: number;
  quizPoints: number;
  matchPoints: number;
  xpPerUnlock: number;
  nextUnlockXp: number;
  unlockedCountries: string[];
  completedCountries: string[];
};

export async function fetchProgressSnapshot(): Promise<ProgressSnapshot> {
  const response = await getJson<ProgressResponse>("/api/progress/");
  return {
    xp: response.xp,
    quizPoints: response.quiz_points,
    matchPoints: response.match_points,
    xpPerUnlock: response.xp_per_unlock,
    nextUnlockXp: response.next_unlock_xp,
    unlockedCountries: response.unlocked_countries,
    completedCountries: response.completed_countries,
  };
}
