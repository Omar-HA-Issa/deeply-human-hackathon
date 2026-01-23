import { getJson } from "./client";

export type UserStats = {
  xp: number;
  total_correct: number;
  total_answered: number;
  accuracy: number;
  streak_days: number;
  countries_completed: number;
  total_attempts: number;
};

export type StatsResponse = {
  stats: UserStats;
};

export function fetchUserStats() {
  return getJson<StatsResponse>("/api/stats/");
}
