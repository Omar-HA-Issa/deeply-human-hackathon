import { getJson, postJson } from "./client";

export type Friend = {
  id: number;
  username: string;
  xp: number;
  quizPoints: number;
  accuracy: number;
  streakDays: number;
};

export type FriendRequest = {
  id: number;
  username: string;
  direction: "incoming" | "outgoing";
  createdAt: string;
};

export type LeaderboardEntry = {
  rank: number;
  userId: number;
  username: string;
  xp: number;
  quizPoints: number;
  accuracy: number;
  streakDays: number;
  isMe: boolean;
};

export type SocialSnapshot = {
  friends: Friend[];
  requests: FriendRequest[];
  leaderboard: LeaderboardEntry[];
};

type FriendsResponse = {
  friends: Array<{
    id: number;
    username: string;
    xp: number;
    quiz_points: number;
    accuracy: number;
    streak_days: number;
  }>;
};

type FriendRequestsResponse = {
  incoming: Array<{
    id: number;
    from_user: { id: number; username: string };
    created_at: string;
  }>;
  outgoing: Array<{
    id: number;
    to_user: { id: number; username: string };
    created_at: string;
  }>;
};

type LeaderboardResponse = {
  leaderboard: Array<{
    rank: number;
    user: { id: number; username: string };
    xp: number;
    quiz_points: number;
    accuracy: number;
    streak_days: number;
    is_me: boolean;
  }>;
};

export async function fetchSocialSnapshot(): Promise<SocialSnapshot> {
  const [friendsResponse, requestsResponse, leaderboardResponse] = await Promise.all([
    getJson<FriendsResponse>("/api/friends/"),
    getJson<FriendRequestsResponse>("/api/friends/requests/"),
    getJson<LeaderboardResponse>("/api/leaderboard/"),
  ]);

  const friends = friendsResponse.friends.map((friend) => ({
    id: friend.id,
    username: friend.username,
    xp: friend.xp,
    quizPoints: friend.quiz_points,
    accuracy: friend.accuracy,
    streakDays: friend.streak_days,
  }));

  const requests: FriendRequest[] = [
    ...requestsResponse.incoming.map((request) => ({
      id: request.id,
      username: request.from_user.username,
      direction: "incoming" as const,
      createdAt: request.created_at,
    })),
    ...requestsResponse.outgoing.map((request) => ({
      id: request.id,
      username: request.to_user.username,
      direction: "outgoing" as const,
      createdAt: request.created_at,
    })),
  ];

  const leaderboard = leaderboardResponse.leaderboard.map((entry) => ({
    rank: entry.rank,
    userId: entry.user.id,
    username: entry.user.username,
    xp: entry.xp,
    quizPoints: entry.quiz_points,
    accuracy: entry.accuracy,
    streakDays: entry.streak_days,
    isMe: entry.is_me,
  }));

  return { friends, requests, leaderboard };
}

export async function acceptFriendRequest(requestId: number) {
  return postJson<Record<string, never>>(
    `/api/friends/requests/${requestId}/accept/`
  );
}

export async function declineFriendRequest(requestId: number) {
  return postJson<Record<string, never>>(
    `/api/friends/requests/${requestId}/decline/`
  );
}

export async function sendFriendRequest(username: string) {
  return postJson<Record<string, never>>("/api/friends/requests/send/", {
    username,
  });
}

export async function cancelFriendRequest(requestId: number) {
  return postJson<Record<string, never>>(
    `/api/friends/requests/${requestId}/cancel/`
  );
}

export async function removeFriend(userId: number) {
  return postJson<Record<string, never>>(`/api/friends/${userId}/remove/`);
}

export async function fetchLeaderboard(limit = 50): Promise<LeaderboardEntry[]> {
  const response = await getJson<LeaderboardResponse>(`/api/leaderboard/?limit=${limit}`);
  return response.leaderboard.map((entry) => ({
    rank: entry.rank,
    userId: entry.user.id,
    username: entry.user.username,
    xp: entry.xp,
    quizPoints: entry.quiz_points,
    accuracy: entry.accuracy,
    streakDays: entry.streak_days,
    isMe: entry.is_me,
  }));
}

export async function fetchFriends(): Promise<Friend[]> {
  const friendsResponse = await getJson<FriendsResponse>("/api/friends/");
  return friendsResponse.friends.map((friend) => ({
    id: friend.id,
    username: friend.username,
    xp: friend.xp,
    quizPoints: friend.quiz_points,
    accuracy: friend.accuracy,
    streakDays: friend.streak_days,
  }));
}
