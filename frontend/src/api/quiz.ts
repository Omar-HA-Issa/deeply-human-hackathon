import { getJson, postJson } from "./client";

export type QuizApiQuestion = {
  id: number;
  prompt: string;
  choices: string[];
  correct_index: number;
  did_you_know?: string;
  surprising_fact?: string;
  insight?: string;
};

export type QuizApiResponse = {
  questions: QuizApiQuestion[];
  fun_fact?: string;
};

export type QuizSubmitAnswer = {
  question_id: number;
  selected_index: number;
};

export type QuizSubmitResponse = {
  score: number;
  total: number;
  correct_count: number;
  results: Array<{
    question_id: number;
    correct: boolean;
    correct_index?: number;
    explanation?: string;
    error?: string;
  }>;
};

export function fetchQuiz(countryCode: string) {
  return getJson<QuizApiResponse>(`/api/quiz/${countryCode}/`);
}

export function submitQuiz(
  countryCode: string,
  answers: QuizSubmitAnswer[],
  options?: { skipProgress?: boolean }
) {
  return postJson<QuizSubmitResponse>(`/api/quiz/${countryCode}/submit/`, {
    answers,
    skip_progress: options?.skipProgress ?? false,
  });
}
