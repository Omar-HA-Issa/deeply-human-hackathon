import { useMemo, useState } from "react";
import "./QuizScreen.css";

export type QuizQuestion = {
  id: string;
  prompt: string;
  options: string[];
  correctIndex: number;
};

type QuizScreenProps = {
  countryName: string;
  onComplete: (passed: boolean) => void;
};

const mockQuestions: QuizQuestion[] = [
  {
    id: "q1",
    prompt: "What is the capital city?",
    options: ["Madrid", "Lisbon", "Rome", "Athens"],
    correctIndex: 0,
  },
  {
    id: "q2",
    prompt: "Which continent is this country in?",
    options: ["Europe", "Asia", "South America", "Africa"],
    correctIndex: 0,
  },
  {
    id: "q3",
    prompt: "Which language is widely spoken here?",
    options: ["Spanish", "Arabic", "German", "Japanese"],
    correctIndex: 0,
  },
  {
    id: "q4",
    prompt: "Which flag colors are correct?",
    options: ["Red & Yellow", "Green & White", "Blue & Black", "Orange & Purple"],
    correctIndex: 0,
  },
  {
    id: "q5",
    prompt: "Pick the correct currency.",
    options: ["Euro", "Peso", "Yen", "Dinar"],
    correctIndex: 0,
  },
];

export function QuizScreen({ countryName, onComplete }: QuizScreenProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [showResult, setShowResult] = useState(false);

  const questions = useMemo(() => mockQuestions, []);
  const currentQuestion = questions[currentIndex];

  const handleSubmit = () => {
    if (selectedIndex === null) {
      return;
    }

    const isCorrect = selectedIndex === currentQuestion.correctIndex;
    const nextCorrectCount = isCorrect ? correctCount + 1 : correctCount;
    const isLast = currentIndex === questions.length - 1;

    if (isLast) {
      setCorrectCount(nextCorrectCount);
      setShowResult(true);
      return;
    }

    setCorrectCount(nextCorrectCount);
    setSelectedIndex(null);
    setCurrentIndex((prev) => prev + 1);
  };

  const handleFinish = () => {
    const passed = correctCount >= 3;
    onComplete(passed);
  };

  if (showResult) {
    const passed = correctCount >= 3;
    return (
      <div className="quiz-screen">
        <div className="quiz-card">
          <h2>{passed ? "Great job!" : "Almost there"}</h2>
          <p>
            You scored {correctCount} out of {questions.length}.
          </p>
          <button className="quiz-primary" onClick={handleFinish}>
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
            {currentQuestion.options.map((option, index) => (
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
