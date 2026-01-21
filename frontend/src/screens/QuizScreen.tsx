import { useEffect, useMemo, useState } from "react";
import { fetchQuiz, QuizApiQuestion, QuizSubmitResponse, submitQuiz } from "../api/quiz";
import "./QuizScreen.css";

type QuizScreenProps = {
  countryName: string;
  countryCode: string;
  onComplete: (passed: boolean) => void;
};
export function QuizScreen({ countryName, countryCode, onComplete }: QuizScreenProps) {
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
    if (selectedIndex === null || !currentQuestion) {
      return;
    }

    setAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: selectedIndex,
    }));

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

    submitQuiz(countryCode, payload)
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
  }, [answers, countryCode, showResult, submitError, submitLoading, submitted]);

  const handleFinish = () => {
    onComplete(correctCount >= 3);
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
          <h2>Loading quiz...</h2>
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
          <h2>{passed ? "Great job!" : "Almost there"}</h2>
          <p>
            {submitted
              ? `You scored ${correctCount} out of ${totalQuestions}.`
              : "Calculating your score..."}
          </p>
          {funFact && <p className="quiz-fun-fact">Fun fact: {funFact}</p>}
          {submitLoading && <p className="quiz-muted">Submitting your answers...</p>}
          {submitError && <p className="quiz-error">{submitError}</p>}
          {submitError && (
            <button
              className="quiz-secondary"
              onClick={() => setSubmitError(null)}
            >
              Retry submission
            </button>
          )}
          {scoreSummary && scoreSummary.length > 0 && (
            <div className="quiz-explanations">
              <h4>Explanations</h4>
              <ul>
                {scoreSummary.map((item) => (
                  <li key={item.id}>
                    {item.explanation}
                    {!item.correct && " (Incorrect)"}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <button
            className="quiz-primary"
            onClick={handleFinish}
            disabled={submitLoading || !submitted}
          >
            {passed ? "Unlock next country" : "Try again"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="quiz-screen">
      <div className="quiz-card">
        <div className="quiz-header">
          <div>
            <h1>{countryName} Quiz</h1>
            <p>Question {currentIndex + 1} of {questions.length}</p>
          </div>
          <div className="quiz-score">Score: {correctCount}</div>
        </div>

        <div className="quiz-question">
          <h3>{currentQuestion.prompt}</h3>
          <div className="quiz-options">
            {currentQuestion.choices.map((option, index) => (
              <button
                key={option}
                className={
                  selectedIndex === index
                    ? "quiz-option selected"
                    : "quiz-option"
                }
                onClick={() => setSelectedIndex(index)}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <button
          className="quiz-primary"
          onClick={handleSubmit}
          disabled={selectedIndex === null}
        >
          {currentIndex === questions.length - 1 ? "Finish" : "Next"}
        </button>
      </div>
    </div>
  );
}
