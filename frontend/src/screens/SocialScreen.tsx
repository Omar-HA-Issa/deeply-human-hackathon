import { useEffect, useMemo, useState } from "react";
import {
  fetchSocialSnapshot,
  Friend,
  FriendRequest,
  LeaderboardEntry,
} from "../api/social";
import "./SocialScreen.css";

type SocialUser = {
  username: string;
};

type SocialScreenProps = {
  user: SocialUser | null;
  onSignIn: () => void;
};

export function SocialScreen({ user, onSignIn }: SocialScreenProps) {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [requests, setRequests] = useState<FriendRequest[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [cheeredIds, setCheeredIds] = useState<Set<string>>(new Set());
  const [inviteStatus, setInviteStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchSocialSnapshot().then((snapshot) => {
      setFriends(snapshot.friends);
      setRequests(snapshot.requests);
      setLeaderboard(snapshot.leaderboard);
    });
  }, []);

  const onlineCount = useMemo(
    () => friends.filter((friend) => friend.isOnline).length,
    [friends]
  );

  const handleCheer = (friendId: string) => {
    setCheeredIds((prev) => {
      const next = new Set(prev);
      if (next.has(friendId)) {
        next.delete(friendId);
      } else {
        next.add(friendId);
      }
      return next;
    });
  };

  const handleAccept = (requestId: string) => {
    const request = requests.find((item) => item.id === requestId);
    if (!request) {
      return;
    }
    setRequests((prev) => prev.filter((item) => item.id !== requestId));
    setFriends((prev) => [
      {
        id: request.id,
        name: request.name,
        home: "New explorer",
        countries: 1,
        streak: 1,
        lastQuiz: request.favorite,
        isOnline: true,
      },
      ...prev,
    ]);
  };

  const handleIgnore = (requestId: string) => {
    setRequests((prev) => prev.filter((item) => item.id !== requestId));
  };

  const handleInvite = async () => {
    const inviteLink = `${window.location.origin}/#auth?invite=${encodeURIComponent(
      user?.username ?? "explorer"
    )}`;
    try {
      await navigator.clipboard.writeText(inviteLink);
      setInviteStatus("Invite link copied!");
    } catch (error) {
      setInviteStatus("Couldn’t copy link. Try again.");
    }
    window.setTimeout(() => setInviteStatus(null), 2200);
  };

  if (!user) {
    return (
      <div className="social-screen">
        <section className="card social-hero">
          <div>
            <h2>Social</h2>
            <p>Connect with friends, share streaks, and explore together.</p>
          </div>
          <button className="button primary" onClick={onSignIn}>
            Sign in to connect
          </button>
        </section>
        <section className="card social-locked">
          <h3>Unlock your social crew</h3>
          <p>
            Sign in to add friends, see live progress, and celebrate each quiz
            victory together.
          </p>
          <div className="social-preview">
            <div>
              <strong>Live friend status</strong>
              <span>See who is exploring right now.</span>
            </div>
            <div>
              <strong>Weekly challenges</strong>
              <span>Team up and unlock streak rewards.</span>
            </div>
            <div>
              <strong>Global leaderboard</strong>
              <span>Track the top explorers worldwide.</span>
            </div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="social-screen">
      <section className="card social-hero">
        <div>
          <h2>Social</h2>
          <p>Stay connected with your crew across every quiz.</p>
        </div>
        <div className="social-hero-actions">
          <button className="button primary" onClick={handleInvite}>
            Invite friends
          </button>
          {inviteStatus ? <span className="invite-status">{inviteStatus}</span> : null}
        </div>
      </section>

      <div className="social-grid">
        <section className="card social-panel">
          <header className="panel-header">
            <h3>Friends</h3>
            <span className="pill">{onlineCount} online</span>
          </header>
          <div className="friend-list">
            {friends.map((friend) => (
              <div className="friend-row" key={friend.id}>
                <div className="friend-main">
                  <div className="avatar">{friend.name[0]}</div>
                  <div>
                    <div className="friend-name">{friend.name}</div>
                    <div className="friend-meta">
                      {friend.home} · {friend.lastQuiz}
                    </div>
                    <div className="friend-status">
                      <span
                        className={
                          friend.isOnline ? "status-dot online" : "status-dot"
                        }
                      />
                      {friend.isOnline ? "Exploring now" : "Away"}
                    </div>
                  </div>
                </div>
                <div className="friend-details">
                  <span>{friend.countries} countries</span>
                  <span>{friend.streak} day streak</span>
                </div>
                <div className="friend-action">
                  <button
                    className={`button ghost ${
                      cheeredIds.has(friend.id) ? "cheered" : ""
                    }`}
                    onClick={() => handleCheer(friend.id)}
                  >
                    {cheeredIds.has(friend.id) ? "Cheered" : "Cheer"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card social-panel">
          <header className="panel-header">
            <h3>Friend requests</h3>
            <span className="pill muted">{requests.length} new</span>
          </header>
          {requests.length ? (
            <div className="request-list">
              {requests.map((request) => (
                <div className="request-row" key={request.id}>
                  <div>
                    <div className="friend-name">{request.name}</div>
                    <div className="friend-meta">
                      {request.mutuals} mutuals · Loves {request.favorite}
                    </div>
                  </div>
                  <div className="request-actions">
                    <button
                      className="button primary small"
                      onClick={() => handleAccept(request.id)}
                    >
                      Accept
                    </button>
                    <button
                      className="button ghost small"
                      onClick={() => handleIgnore(request.id)}
                    >
                      Ignore
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">No new requests right now.</div>
          )}
        </section>

        <section className="card social-panel challenge-panel">
          <header className="panel-header">
            <h3>Weekly challenge</h3>
            <span className="pill">2 days left</span>
          </header>
          <div className="challenge-body">
            <strong>Border hop streak</strong>
            <p>Complete 3 connected quizzes to keep your streak glowing.</p>
            <div className="challenge-progress">
              <div className="progress-track">
                <div className="progress-fill" style={{ width: "66%" }} />
              </div>
              <div className="challenge-foot">
                <span>2 / 3 complete</span>
                <button className="button ghost">Continue</button>
              </div>
            </div>
          </div>
        </section>

        <section className="card social-panel">
          <header className="panel-header">
            <h3>Top explorers</h3>
            <span className="pill muted">This week</span>
          </header>
          <div className="leaderboard-list">
            {leaderboard.map((entry, index) => (
              <div className="leaderboard-row" key={entry.id}>
                <span className="rank">#{index + 1}</span>
                <span className="leader-name">{entry.name}</span>
                <span className="leader-score">{entry.countries} countries</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
