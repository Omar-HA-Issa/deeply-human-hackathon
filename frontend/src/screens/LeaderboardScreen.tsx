import { useEffect, useMemo, useState } from "react";
import { fetchFriends, fetchLeaderboard, Friend, LeaderboardEntry } from "../api/social";
import "./LeaderboardScreen.css";

type LeaderboardScreenProps = {
  user: { username: string } | null;
};

type View = "global" | "friends";

export function LeaderboardScreen({ user }: LeaderboardScreenProps) {
  const [activeView, setActiveView] = useState<View>("global");
  const [globalEntries, setGlobalEntries] = useState<LeaderboardEntry[]>([]);
  const [friendEntries, setFriendEntries] = useState<Friend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const [globalData, friendsData] = await Promise.all([
          fetchLeaderboard(),
          user ? fetchFriends() : Promise.resolve([]),
        ]);
        if (!mounted) return;
        setGlobalEntries(globalData);
        setFriendEntries(friendsData);
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "Failed to load leaderboard");
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [user]);

  const meFromGlobal = useMemo(
    () => globalEntries.find((entry) => entry.isMe),
    [globalEntries]
  );

  const friendsOnlyLeaderboard = useMemo(() => {
    const withMe =
      user && meFromGlobal
        ? [
            ...friendEntries,
            {
              id: -1,
              username: user.username,
              xp: meFromGlobal.xp,
              quizPoints: meFromGlobal.quizPoints,
              accuracy: meFromGlobal.accuracy,
              streakDays: meFromGlobal.streakDays,
            },
          ]
        : friendEntries;
    return [...withMe].sort((a, b) => b.quizPoints - a.quizPoints);
  }, [friendEntries, meFromGlobal, user]);

  const renderRow = (index: number, name: string, score: number, extra?: string) => (
    <div className="leader-row" key={`${name}-${index}`}>
      <span className="leader-rank">#{index + 1}</span>
      <span className="leader-username">{name}</span>
      <span className="leader-score">{score} pts</span>
      {extra ? <span className="leader-meta">{extra}</span> : null}
    </div>
  );

  return (
    <div className="leaderboard-screen">
      <section className="card leaderboard-hero">
        <div className="leader-toggle">
          <button
            className={`tab ${activeView === "global" ? "active" : ""}`}
            onClick={() => setActiveView("global")}
          >
            Global
          </button>
          <button
            className={`tab ${activeView === "friends" ? "active" : ""}`}
            onClick={() => setActiveView("friends")}
            disabled={!user}
          >
            Friends only
          </button>
          {!user ? <span className="leader-note">Sign in to see friends</span> : null}
        </div>
      </section>

      <section className="card leaderboard-panel">
        {isLoading ? (
          <div className="empty-state">Loading leaderboard…</div>
        ) : error ? (
          <div className="empty-state">{error}</div>
        ) : activeView === "global" ? (
          <div className="leader-list">
            {globalEntries.map((entry, index) =>
              renderRow(index, entry.username + (entry.isMe ? " (you)" : ""), entry.quizPoints)
            )}
          </div>
        ) : friendsOnlyLeaderboard.length ? (
          <div className="leader-list">
            {friendsOnlyLeaderboard.map((friend, index) =>
              renderRow(
                index,
                friend.username === user?.username ? `${friend.username} (you)` : friend.username,
                friend.quizPoints,
                `${Math.round(friend.accuracy * 100)}% accuracy`
              )
            )}
          </div>
        ) : (
          <div className="empty-state">Add friends to see your private leaderboard.</div>
        )}
      </section>
    </div>
  );
}
