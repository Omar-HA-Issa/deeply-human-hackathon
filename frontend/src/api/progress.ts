import { getJson } from "./client";

export type ProgressEntry = {
  code: string;
  status: "locked" | "available" | "completed";
  unlocked_at: string | null;
  completed_at: string | null;
};

export type ProgressResponse = {
  progress: ProgressEntry[];
  completed_codes: string[];
  count: number;
};

export function fetchProgress() {
  return getJson<ProgressResponse>("/api/progress/");
}
