export type Friend = {
  id: string;
  name: string;
  home: string;
  countries: number;
  streak: number;
  lastQuiz: string;
  isOnline: boolean;
};

export type FriendRequest = {
  id: string;
  name: string;
  mutuals: number;
  favorite: string;
};

export type LeaderboardEntry = {
  id: string;
  name: string;
  countries: number;
};

export type SocialSnapshot = {
  friends: Friend[];
  requests: FriendRequest[];
  leaderboard: LeaderboardEntry[];
};

const demoSnapshot: SocialSnapshot = {
  friends: [
    {
      id: "friend-1",
      name: "Lina Park",
      home: "Seoul",
      countries: 14,
      streak: 6,
      lastQuiz: "Italy",
      isOnline: true,
    },
    {
      id: "friend-2",
      name: "Noah Klein",
      home: "Berlin",
      countries: 21,
      streak: 3,
      lastQuiz: "France",
      isOnline: true,
    },
    {
      id: "friend-3",
      name: "Amina Hassan",
      home: "Cairo",
      countries: 17,
      streak: 9,
      lastQuiz: "Greece",
      isOnline: false,
    },
  ],
  requests: [
    {
      id: "request-1",
      name: "Miguel Santos",
      mutuals: 3,
      favorite: "Portugal",
    },
    {
      id: "request-2",
      name: "Sofia Costa",
      mutuals: 1,
      favorite: "Morocco",
    },
  ],
  leaderboard: [
    { id: "rank-1", name: "Yuki Tan", countries: 38 },
    { id: "rank-2", name: "Oliver Smith", countries: 35 },
    { id: "rank-3", name: "Priya Singh", countries: 32 },
  ],
};

export async function fetchSocialSnapshot(): Promise<SocialSnapshot> {
  return Promise.resolve(demoSnapshot);
}
