import { useEffect, useMemo, useState } from "react";
import {
  acceptFriendRequest,
  cancelFriendRequest,
  declineFriendRequest,
  fetchSocialSnapshot,
  Friend,
  FriendRequest,
  LeaderboardEntry,
  removeFriend,
  sendFriendRequest,
} from "../api/social";
import {
  acceptMatch,
  cancelMatch,
  createMatch,
  declineMatch,
  fetchMatches,
  FriendMatch,
} from "../api/matches";
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
  const [matches, setMatches] = useState<FriendMatch[]>([]);
  const [cheeredIds, setCheeredIds] = useState<Set<number>>(new Set());
  const [inviteStatus, setInviteStatus] = useState<string | null>(null);
  const [requestStatus, setRequestStatus] = useState<string | null>(null);
  const [matchStatus, setMatchStatus] = useState<string | null>(null);
  const [requestName, setRequestName] = useState("");
  const [isSendingRequest, setIsSendingRequest] = useState(false);
  const [isSendingMatch, setIsSendingMatch] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadSnapshot = async () => {
    try {
      setIsLoading(true);
      setLoadError(null);
      const [snapshot, matchList] = await Promise.all([
        fetchSocialSnapshot(),
        fetchMatches(),
      ]);
      setFriends(snapshot.friends);
      setRequests(snapshot.requests);
      setLeaderboard(snapshot.leaderboard);
      setMatches(matchList);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to load");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!user) {
      setIsLoading(false);
      return;
    }
    loadSnapshot();
  }, [user]);

  const incomingRequests = useMemo(
    () => requests.filter((request) => request.direction === "incoming"),
    [requests]
  );

  const outgoingRequests = useMemo(
    () => requests.filter((request) => request.direction === "outgoing"),
    [requests]
  );

  const handleCheer = (friendId: number) => {
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

  const handleAccept = async (requestId: number) => {
    await acceptFriendRequest(requestId);
    await loadSnapshot();
  };

  const handleIgnore = async (requestId: number) => {
    await declineFriendRequest(requestId);
    await loadSnapshot();
  };

  const handleSendRequest = async () => {
    const trimmed = requestName.trim();
    if (!trimmed) {
      setRequestStatus("Enter a username to send a request.");
      return;
    }
    try {
      setIsSendingRequest(true);
      await sendFriendRequest(trimmed);
      setRequestName("");
      setRequestStatus("Friend request sent!");
      await loadSnapshot();
    } catch (error) {
      setRequestStatus(error instanceof Error ? error.message : "Request failed");
    } finally {
      setIsSendingRequest(false);
      window.setTimeout(() => setRequestStatus(null), 2200);
    }
  };

  const handleCancelRequest = async (requestId: number) => {
    await cancelFriendRequest(requestId);
    await loadSnapshot();
  };

  const handleRemoveFriend = async (friendId: number) => {
    await removeFriend(friendId);
    await loadSnapshot();
  };

  const handleChallengeFriend = async (friendId: number, friendName: string) => {
    const countryCode = window
      .prompt(`Challenge ${friendName} with a country code (e.g., ES):`)
      ?.trim()
      .toUpperCase();
    if (!countryCode) {
      return;
    }
    try {
      setIsSendingMatch(true);
      await createMatch(friendId, countryCode);
      setMatchStatus(`Challenge sent to ${friendName}!`);
      await loadSnapshot();
    } catch (error) {
      setMatchStatus(error instanceof Error ? error.message : "Challenge failed");
    } finally {
      setIsSendingMatch(false);
      window.setTimeout(() => setMatchStatus(null), 2400);
    }
  };

  const handleAcceptMatch = async (matchId: number) => {
    await acceptMatch(matchId);
    await loadSnapshot();
  };

  const handleDeclineMatch = async (matchId: number) => {
    await declineMatch(matchId);
    await loadSnapshot();
  };

  const handleCancelMatch = async (matchId: number) => {
    await cancelMatch(matchId);
    await loadSnapshot();
  };

  const handlePlayMatch = (match: FriendMatch) => {
    const query = new URLSearchParams({
      code: match.country.code,
      name: match.country.name,
      match: String(match.id),
    });
    window.location.hash = `quiz?${query.toString()}`;
  };

  const handleInvite = async () => {
    const inviteLink = `${window.location.origin}/#auth?mode=register&invite=${encodeURIComponent(
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
            <span className="pill">{friends.length} total</span>
          </header>
          {matchStatus ? (
            <div className="match-status-banner">{matchStatus}</div>
          ) : null}
          {isLoading ? (
            <div className="empty-state">Loading friends…</div>
          ) : loadError ? (
            <div className="empty-state">{loadError}</div>
          ) : (
            <div className="friend-list">
              {friends.map((friend) => (
                <div className="friend-row" key={friend.id}>
                <div className="friend-main">
                  <div className="avatar">{friend.username[0]}</div>
                  <div>
                    <div className="friend-name">{friend.username}</div>
                    <div className="friend-meta">
                      {Math.round(friend.accuracy * 100)}% accuracy
                    </div>
                    <div className="friend-status">
                      <span className="status-dot online" />
        						{friend.quizPoints} pts
                    </div>
                  </div>
                </div>
                <div className="friend-details">
                  <span>{friend.streakDays} day streak</span>
                  <span>{Math.round(friend.accuracy * 100)}% accuracy</span>
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
                  <button
                    className="button ghost"
                    onClick={() => handleChallengeFriend(friend.id, friend.username)}
                    disabled={isSendingMatch}
                  >
                    Challenge
                  </button>
                  <button
                    className="button ghost"
                    onClick={() => handleRemoveFriend(friend.id)}
                  >
                    Remove
                  </button>
                </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="card social-panel match-panel">
          <header className="panel-header">
            <h3>Friend matches</h3>
            <span className="pill muted">{matches.length} total</span>
          </header>
          {isLoading ? (
            <div className="empty-state">Loading matches…</div>
          ) : loadError ? (
            <div className="empty-state">{loadError}</div>
          ) : matches.length ? (
            <div className="match-list">
              {matches.map((match) => {
                const opponent = match.isChallenger
                  ? match.opponent.username
                  : match.challenger.username;
                const awaitingResponse =
                  match.status === "pending" && match.isChallenger;
                const needsResponse =
                  match.status === "pending" && !match.isChallenger;
                const awaitingFriend =
                  match.status === "accepted" && match.myResult && !match.opponentResult;
                const needsPlay = match.status === "accepted" && !match.myResult;
                const winnerText =
                  match.status === "completed"
                    ? match.winnerId
                      ? match.winnerId === match.challenger.id
                        ? `${match.challenger.username} wins`
                        : `${match.opponent.username} wins`
                      : "Tie game"
                    : null;

                return (
                  <div className="match-row" key={match.id}>
                    <div className="match-main">
                      <div className="match-title">
                        {match.country.name} ({match.country.code})
                      </div>
                      <div className="match-meta">
                        vs {opponent} · {match.status}
                      </div>
                      {winnerText ? (
                        <div className="match-winner">{winnerText}</div>
                      ) : null}
                      {match.myResult ? (
                        <div className="match-score">
                          You: {match.myResult.correctCount}/
                          {match.myResult.totalQuestions} ({match.myResult.score} pts)
                        </div>
                      ) : null}
                      {match.opponentResult ? (
                        <div className="match-score muted">
                          Friend: {match.opponentResult.correctCount}/
                          {match.opponentResult.totalQuestions} (
                          {match.opponentResult.score} pts)
                        </div>
                      ) : null}
                    </div>
                    <div className="match-actions">
                      {needsResponse ? (
                        <>
                          <button
                            className="button primary small"
                            onClick={() => handleAcceptMatch(match.id)}
                          >
                            Accept
                          </button>
                          <button
                            className="button ghost small"
                            onClick={() => handleDeclineMatch(match.id)}
                          >
                            Decline
                          </button>
                        </>
                      ) : null}
                      {awaitingResponse ? (
                        <button
                          className="button ghost small"
                          onClick={() => handleCancelMatch(match.id)}
                        >
                          Cancel
                        </button>
                      ) : null}
                      {needsPlay ? (
                        <button
                          className="button primary small"
                          onClick={() => handlePlayMatch(match)}
                        >
                          Play match
                        </button>
                      ) : null}
                      {awaitingFriend ? (
                        <span className="match-wait">Waiting on friend…</span>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              Challenge a friend to kick off your first match.
            </div>
          )}
        </section>

        <section className="card social-panel">
          <header className="panel-header">
            <h3>Friend requests</h3>
            <span className="pill muted">{incomingRequests.length} new</span>
          </header>
          <div className="add-friend-form">
            <div className="add-friend-fields">
              <input
                className="add-friend-input"
                placeholder="Add by username"
                value={requestName}
                onChange={(event) => setRequestName(event.target.value)}
              />
              <button
                className="button primary small add-friend-button"
                onClick={handleSendRequest}
                disabled={isSendingRequest}
              >
                {isSendingRequest ? "Sending..." : "Send"}
              </button>
            </div>
            {requestStatus ? (
              <div className="add-friend-status">{requestStatus}</div>
            ) : null}
          </div>
          {isLoading ? (
            <div className="empty-state">Loading requests…</div>
          ) : loadError ? (
            <div className="empty-state">{loadError}</div>
          ) : incomingRequests.length ? (
            <div className="request-list">
              {incomingRequests.map((request) => (
                <div className="request-row" key={request.id}>
                  <div>
                    <div className="friend-name">{request.username}</div>
                    <div className="friend-meta">
                      Incoming request
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
            <div className="empty-state">
              {outgoingRequests.length
                ? `No incoming requests. ${outgoingRequests.length} outgoing pending.`
                : "No requests right now."}
            </div>
          )}
          {outgoingRequests.length ? (
            <div className="request-list">
              {outgoingRequests.map((request) => (
                <div className="request-row" key={request.id}>
                  <div>
                    <div className="friend-name">{request.username}</div>
                    <div className="friend-meta">Outgoing request</div>
                  </div>
                  <div className="request-actions">
                    <button
                      className="button ghost small"
                      onClick={() => handleCancelRequest(request.id)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
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
          {isLoading ? (
            <div className="empty-state">Loading leaderboard…</div>
          ) : loadError ? (
            <div className="empty-state">{loadError}</div>
          ) : (
            <div className="leaderboard-list">
              {leaderboard.map((entry, index) => (
                <div className="leaderboard-row" key={entry.userId}>
                  <span className="rank">#{index + 1}</span>
                  <span className="leader-name">
                    {entry.username}
                    {entry.isMe ? " (you)" : ""}
                  </span>
                  <span className="leader-score">{entry.quizPoints} pts</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
