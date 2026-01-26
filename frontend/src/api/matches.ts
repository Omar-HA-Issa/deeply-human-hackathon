import { getJson, postJson } from "./client";

export type MatchResult = {
  correctCount: number;
  totalQuestions: number;
  score: number;
  submittedAt: string | null;
};

export type FriendMatch = {
  id: number;
  status: "pending" | "accepted" | "declined" | "canceled" | "completed";
  country: { code: string; name: string };
  challenger: { id: number; username: string };
  opponent: { id: number; username: string };
  isChallenger: boolean;
  createdAt: string;
  acceptedAt: string | null;
  completedAt: string | null;
  winnerId: number | null;
  myResult: MatchResult | null;
  opponentResult: MatchResult | null;
};

type MatchesResponse = {
  matches: Array<{
    id: number;
    status: FriendMatch["status"];
    country: { code: string; name: string };
    challenger: { id: number; username: string };
    opponent: { id: number; username: string };
    is_challenger: boolean;
    created_at: string;
    accepted_at: string | null;
    completed_at: string | null;
    winner_id: number | null;
    my_result: {
      correct_count: number;
      total_questions: number;
      score: number;
      submitted_at: string | null;
    } | null;
    opponent_result: {
      correct_count: number;
      total_questions: number;
      score: number;
      submitted_at: string | null;
    } | null;
  }>;
};

type MatchChallengePayload = {
  friend_id: number;
  country_code: string;
};

export async function fetchMatches(): Promise<FriendMatch[]> {
  const response = await getJson<MatchesResponse>("/api/matches/");
  return response.matches.map((match) => ({
    id: match.id,
    status: match.status,
    country: match.country,
    challenger: match.challenger,
    opponent: match.opponent,
    isChallenger: match.is_challenger,
    createdAt: match.created_at,
    acceptedAt: match.accepted_at,
    completedAt: match.completed_at,
    winnerId: match.winner_id,
    myResult: match.my_result
      ? {
          correctCount: match.my_result.correct_count,
          totalQuestions: match.my_result.total_questions,
          score: match.my_result.score,
          submittedAt: match.my_result.submitted_at,
        }
      : null,
    opponentResult: match.opponent_result
      ? {
          correctCount: match.opponent_result.correct_count,
          totalQuestions: match.opponent_result.total_questions,
          score: match.opponent_result.score,
          submittedAt: match.opponent_result.submitted_at,
        }
      : null,
  }));
}

export async function createMatch(friendId: number, countryCode: string) {
  const payload: MatchChallengePayload = {
    friend_id: friendId,
    country_code: countryCode,
  };
  return postJson<{ match: { id: number } }>("/api/matches/challenge/", payload);
}

export async function acceptMatch(matchId: number) {
  return postJson<Record<string, never>>(`/api/matches/${matchId}/accept/`);
}

export async function declineMatch(matchId: number) {
  return postJson<Record<string, never>>(`/api/matches/${matchId}/decline/`);
}

export async function cancelMatch(matchId: number) {
  return postJson<Record<string, never>>(`/api/matches/${matchId}/cancel/`);
}

export async function submitMatchResult(
  matchId: number,
  correctCount: number,
  totalQuestions: number
) {
  return postJson<Record<string, never>>(`/api/matches/${matchId}/submit/`, {
    correct_count: correctCount,
    total_questions: totalQuestions,
  });
}
