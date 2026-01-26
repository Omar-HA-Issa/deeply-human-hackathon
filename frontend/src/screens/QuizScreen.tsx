import { useEffect, useMemo, useState } from "react";
import { submitMatchResult } from "../api/matches";
import { fetchQuiz, QuizApiQuestion, QuizSubmitResponse, submitQuiz } from "../api/quiz";
import "./QuizScreen.css";

type QuizScreenProps = {
  countryName: string;
  countryCode: string;
  matchId?: number;
  onComplete: (passed: boolean) => void;
};
export function QuizScreen({ countryName, countryCode, matchId, onComplete }: QuizScreenProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const [questions, setQuestions] = useState<QuizApiQuestion[]>([]);
  const [funFact, setFunFact] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<QuizSubmitResponse["results"]>([]);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [matchSubmitted, setMatchSubmitted] = useState(false);
  const [matchSubmitError, setMatchSubmitError] = useState<string | null>(null);
  const [matchSubmitLoading, setMatchSubmitLoading] = useState(false);
  const [answerStates, setAnswerStates] = useState<
    Record<number, { selectedIndex: number; isCorrect: boolean }>
  >({});
  const [revealedQuestions, setRevealedQuestions] = useState<Set<number>>(
    () => new Set()
  );

  useEffect(() => {
    setLoading(true);
    setError(null);
    setQuestions([]);
    setFunFact(null);
    setAnswers({});
    setCurrentIndex(0);
    setSelectedIndex(null);
    setCorrectCount(0);
    setShowResult(false);
    setResults([]);
    setSubmitted(false);
    setSubmitError(null);
    setAnswerStates({});
    setRevealedQuestions(new Set());
    setMatchSubmitted(false);
    setMatchSubmitError(null);
    setMatchSubmitLoading(false);

    fetchQuiz(countryCode)
      .then((response) => {
        setQuestions(response.questions ?? []);
        setFunFact(response.fun_fact ?? null);
        setTotalQuestions(response.questions?.length ?? 0);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load quiz");
      })
      .finally(() => setLoading(false));
  }, [countryCode]);

  const currentQuestion = questions[currentIndex];

  const handleSubmit = () => {
    if (!currentQuestion || selectedIndex === null) {
      return;
    }

    const isAlreadyRevealed = revealedQuestions.has(currentQuestion.id);
    if (!isAlreadyRevealed) {
      const isCorrect = selectedIndex === currentQuestion.correct_index;
      setAnswerStates((prev) => ({
        ...prev,
        [currentQuestion.id]: { selectedIndex, isCorrect },
      }));
      setAnswers((prev) => ({
        ...prev,
        [currentQuestion.id]: selectedIndex,
      }));
      setRevealedQuestions((prev) => new Set(prev).add(currentQuestion.id));
      return;
    }

    const isLast = currentIndex === questions.length - 1;
    if (isLast) {
      setShowResult(true);
      return;
    }

    setSelectedIndex(null);
    setCurrentIndex((prev) => prev + 1);
  };

  useEffect(() => {
    if (!showResult || submitLoading || submitted || submitError) {
      return;
    }

    const payload = Object.entries(answers).map(([id, answerIndex]) => ({
      question_id: Number(id),
      selected_index: answerIndex,
    }));

    setSubmitLoading(true);
    setSubmitError(null);

    submitQuiz(countryCode, payload, { skipProgress: Boolean(matchId) })
      .then((result) => {
        setCorrectCount(result.correct_count);
        setTotalQuestions(result.total);
        setResults(result.results ?? []);
        setSubmitted(true);
      })
      .catch((err) => {
        setSubmitError(err instanceof Error ? err.message : "Failed to submit quiz");
      })
      .finally(() => setSubmitLoading(false));
  }, [
    answers,
    countryCode,
    matchId,
    showResult,
    submitError,
    submitLoading,
    submitted,
  ]);

  useEffect(() => {
    if (!matchId || !submitted || matchSubmitted || matchSubmitLoading || matchSubmitError) {
      return;
    }
    if (!totalQuestions) {
      return;
    }
    setMatchSubmitLoading(true);
    submitMatchResult(matchId, correctCount, totalQuestions)
      .then(() => setMatchSubmitted(true))
      .catch((err) => {
        setMatchSubmitError(err instanceof Error ? err.message : "Failed to submit match");
      })
      .finally(() => setMatchSubmitLoading(false));
  }, [
    correctCount,
    matchId,
    matchSubmitted,
    matchSubmitError,
    matchSubmitLoading,
    submitted,
    totalQuestions,
  ]);

  const handleFinish = () => {
    onComplete(correctCount >= 3);
  };


  const optionVariants = useMemo(
    () => ["blue", "yellow", "mint", "lavender"],
    []
  );

  const displayScore = useMemo(() => {
    return Object.values(answerStates).filter((item) => item.isCorrect).length;
  }, [answerStates]);

  const handleOptionSelect = (index: number) => {
    if (!currentQuestion) {
      return;
    }

    if (revealedQuestions.has(currentQuestion.id)) {
      return;
    }

    setSelectedIndex(index);
  };

  const scoreSummary = useMemo(() => {
    if (!showResult) {
      return null;
    }
    return results
      .filter((item) => item.explanation)
      .map((item) => ({
        id: String(item.question_id),
        explanation: item.explanation as string,
        correct: item.correct,
      }));
  }, [results, showResult]);

  if (loading) {
    return (
      <div className="quiz-screen">
        <div className="quiz-card">
          <div className="quiz-loading">
            <div className="quiz-spinner"></div>
            <span className="quiz-loading-text">Loading quiz...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="quiz-screen">
        <div className="quiz-card">
          <h2>Quiz unavailable</h2>
          <p>{error}</p>
          <button className="quiz-primary" onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="quiz-screen">
        <div className="quiz-card">
          <h2>No questions found</h2>
          <button className="quiz-primary" onClick={() => onComplete(false)}>
            Back to roadmap
          </button>
        </div>
      </div>
    );
  }

  if (showResult) {
    const passed = correctCount >= 3;
    return (
      <div className="quiz-screen">
        <div className="quiz-card">
          <div className="quiz-meta">
            <div className="quiz-country">
              <span className="quiz-code">{countryCode}</span>
              <div>
                <h1>{countryName}</h1>
                <p>Quiz complete</p>
              </div>
            </div>
          </div>

          <h2>{passed ? "Great job!" : "Almost there"}</h2>
          <p>
            {submitted
              ? `You scored ${correctCount} out of ${totalQuestions}.`
              : "Calculating your score..."}
          </p>
          {funFact && (
            <div className="quiz-fun-card">
              <div className="quiz-fun-title">Did you know?</div>
              <p>{funFact}</p>
            </div>
          )}
          {submitLoading && <p className="quiz-muted">Submitting your answers...</p>}
          {submitError && <p className="quiz-error">{submitError}</p>}
          {matchId && matchSubmitLoading && (
            <p className="quiz-muted">Submitting match result...</p>
          )}
          {matchId && matchSubmitted && !matchSubmitError && (
            <p className="quiz-success">Match result submitted!</p>
          )}
          {matchId && matchSubmitError && <p className="quiz-error">{matchSubmitError}</p>}
          {matchId && matchSubmitError && (
            <button
              className="quiz-secondary"
              onClick={() => setMatchSubmitError(null)}
            >
              Retry match submission
            </button>
          )}
          {submitError && (
            <button
              className="quiz-secondary"
              onClick={() => setSubmitError(null)}
            >
              Retry submission
            </button>
          )}
          <button
            className="quiz-primary"
            onClick={handleFinish}
            disabled={
              submitLoading ||
              !submitted ||
              (matchId ? matchSubmitLoading || !!matchSubmitError : false)
            }
          >
            {passed ? "Unlock next country" : "Try again"}
          </button>
        </div>
      </div>
    );
  }

  // Helper to strip "Surprising, right?" prefix from text
  const stripSurprisingPrefix = (text: string | undefined) => {
    if (!text) return "";
    return text.replace(/^Surprising,?\s*right\??\s*/i, "").trim();
  };

  return (
    <div className="quiz-screen">
      <button
        className="quiz-exit"
        onClick={() => onComplete(false)}
        title="Exit quiz"
      >
        ✕
      </button>
      <div className="quiz-card">
        <div className="quiz-meta">
          <div className="quiz-country">
            <span className="quiz-code">{countryCode}</span>
            <div>
              <h1>{countryName}</h1>
              <p>Question {currentIndex + 1} of {questions.length}</p>
            </div>
          </div>
          <div className="quiz-meta-actions">
            <div className="quiz-score">Score: {displayScore}</div>
          </div>
        </div>

        <div className="quiz-question">
          <h3>{currentQuestion.prompt}</h3>
          <div className="quiz-options">
            {currentQuestion.choices.map((option, index) => {
              const answerState = answerStates[currentQuestion.id];
              const isAnswered = Boolean(answerState);
              const isSelected = answerState?.selectedIndex === index;
              const isCorrect = currentQuestion.correct_index === index;
              const isWrong = isSelected && !answerState?.isCorrect;
              const isRevealed = revealedQuestions.has(currentQuestion.id);

              let stateClass = "";
              if (isAnswered && isCorrect) {
                stateClass = "correct";
              } else if (isAnswered && isWrong) {
                stateClass = "wrong";
              }

              return (
                <button
                  key={option}
                  data-variant={optionVariants[index % optionVariants.length]}
                  className={`quiz-option ${selectedIndex === index ? "selected" : ""} ${stateClass}`}
                  onClick={() => handleOptionSelect(index)}
                  disabled={isRevealed}
                >
                  <span className="quiz-option-letter">
                    {String.fromCharCode(65 + index)}
                  </span>
                  <span className="quiz-option-text">{option}</span>
                </button>
              );
            })}
          </div>
        </div>

        {revealedQuestions.has(currentQuestion.id) && (
          <div className={`quiz-fun-card ${answerStates[currentQuestion.id]?.isCorrect ? 'correct' : 'wrong'}`}>
            <div className="quiz-fun-title">
              {answerStates[currentQuestion.id]?.isCorrect ? "Did you know?" : "Surprising, right?"}
            </div>
            <p>
              {answerStates[currentQuestion.id]?.isCorrect
                ? (currentQuestion.did_you_know || stripSurprisingPrefix(currentQuestion.surprising_fact) || funFact)
                : (stripSurprisingPrefix(currentQuestion.surprising_fact) || currentQuestion.did_you_know || funFact)}
            </p>
          </div>
        )}

        <button
          className="quiz-primary"
          onClick={handleSubmit}
          disabled={selectedIndex === null}
        >
          {revealedQuestions.has(currentQuestion.id)
            ? currentIndex === questions.length - 1
              ? "Finish"
              : "Continue"
            : "Check answer"}
        </button>
      </div>
    </div>
  );
}
