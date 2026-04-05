"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

interface Question {
  index: number;
  text: string;
  answered: boolean;
  evaluation?: {
    clarte: number;
    motivation: number;
    connaissance: number;
    feedback: string;
  };
}

interface InterviewState {
  filiere: string;
  questions: string[];
  currentIndex: number;
  answers: string[];
  evaluations: Array<{
    clarte: number;
    motivation: number;
    connaissance: number;
    feedback: string;
  }>;
  isComplete: boolean;
  finalScore?: number;
  finalFeedback?: {
    score: number;
    points_forts: string[];
    axes_amelioration: string[];
  };
}

function InterviewContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const filiereId = searchParams.get("filiere_id");

  const [state, setState] = useState<InterviewState>({
    filiere: "",
    questions: [],
    currentIndex: 0,
    answers: [],
    evaluations: [],
    isComplete: false,
  });
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch questions on mount
  useEffect(() => {
    if (!sessionId || !filiereId) {
      setError("Paramètres manquants");
      setIsLoading(false);
      return;
    }

    const initInterview = async () => {
      try {
        // Select the filière
        await fetch(`/api/session/${sessionId}/select-filiere`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filiere_id: filiereId }),
        });

        // Get questions
        const res = await fetch(`/api/session/${sessionId}/interview/questions`);
        const data = await res.json();

        setState((prev) => ({
          ...prev,
          filiere: data.filiere,
          questions: data.questions,
          currentIndex: data.answered_count,
        }));
        setIsLoading(false);
      } catch {
        setError("Erreur lors du chargement des questions");
        setIsLoading(false);
      }
    };

    initInterview();
  }, [sessionId, filiereId]);

  const handleSubmitAnswer = async () => {
    if (!currentAnswer.trim() || currentAnswer.length < 10) {
      setError("Ta réponse doit faire au moins 10 caractères");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`/api/session/${sessionId}/interview/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_index: state.currentIndex,
          answer: currentAnswer,
        }),
      });

      const evaluation = await res.json();

      setState((prev) => {
        const newAnswers = [...prev.answers, currentAnswer];
        const newEvaluations = [...prev.evaluations, evaluation];
        const isComplete = evaluation.is_complete;

        return {
          ...prev,
          answers: newAnswers,
          evaluations: newEvaluations,
          currentIndex: prev.currentIndex + 1,
          isComplete,
        };
      });

      setCurrentAnswer("");

      // If complete, fetch final results
      if (evaluation.is_complete) {
        const resultRes = await fetch(`/api/session/${sessionId}/result`);
        const result = await resultRes.json();
        setState((prev) => ({
          ...prev,
          finalScore: result.interview_score,
          finalFeedback: result.interview_feedback,
        }));
      }
    } catch {
      setError("Erreur lors de l'envoi de la réponse");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-orient-blue border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-600">Préparation de l&apos;entretien...</p>
        </div>
      </div>
    );
  }

  if (error && !state.questions.length) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Erreur</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            href="/onboarding"
            className="px-6 py-3 bg-orient-blue text-white rounded-lg"
          >
            Recommencer
          </Link>
        </div>
      </div>
    );
  }

  if (state.isComplete) {
    return <InterviewComplete state={state} sessionId={sessionId!} />;
  }

  const currentQuestion = state.questions[state.currentIndex];
  const lastEvaluation = state.evaluations[state.evaluations.length - 1];

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-orient-blue mb-2">
            🎤 Simulation d&apos;entretien
          </h1>
          <p className="text-gray-600">{state.filiere}</p>
        </div>

        {/* Progress */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>Question {state.currentIndex + 1} sur {state.questions.length}</span>
            <span>{Math.round(((state.currentIndex) / state.questions.length) * 100)}% complété</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-orient-blue transition-all duration-300"
              style={{ width: `${((state.currentIndex) / state.questions.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Previous evaluation */}
        {lastEvaluation && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-green-600">✓</span>
              <span className="font-medium text-green-800">Réponse précédente évaluée</span>
            </div>
            <div className="flex gap-4 mb-2 text-sm">
              <span>Clarté: {lastEvaluation.clarte}/10</span>
              <span>Motivation: {lastEvaluation.motivation}/10</span>
              <span>Connaissance: {lastEvaluation.connaissance}/10</span>
            </div>
            <p className="text-sm text-green-700">{lastEvaluation.feedback}</p>
          </div>
        )}

        {/* Question card */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-start gap-4 mb-6">
            <div className="w-12 h-12 bg-orient-blue rounded-full flex items-center justify-center text-white text-xl">
              🎓
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">Question {state.currentIndex + 1}</p>
              <p className="text-lg text-gray-900">{currentQuestion}</p>
            </div>
          </div>

          <textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            placeholder="Tape ta réponse ici... Sois précis et authentique !"
            rows={6}
            className="w-full px-4 py-3 border rounded-lg resize-none focus:ring-2 focus:ring-orient-blue focus:border-orient-blue"
          />

          <div className="flex justify-between items-center mt-4">
            <span className="text-sm text-gray-500">
              {currentAnswer.length} caractères (min. 10)
            </span>
            <button
              onClick={handleSubmitAnswer}
              disabled={isSubmitting || currentAnswer.length < 10}
              className="px-6 py-3 bg-orient-blue text-white rounded-lg font-medium disabled:opacity-50 hover:bg-blue-800"
            >
              {isSubmitting ? "Évaluation..." : "Envoyer ma réponse →"}
            </button>
          </div>

          {error && (
            <p className="mt-2 text-red-600 text-sm">{error}</p>
          )}
        </div>

        {/* Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 mb-2">💡 Conseils</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Structure ta réponse: introduction, développement, conclusion</li>
            <li>• Donne des exemples concrets de ton parcours</li>
            <li>• Montre ta connaissance de la filière</li>
            <li>• Sois authentique et positif</li>
          </ul>
        </div>
      </div>
    </main>
  );
}

function InterviewComplete({
  state,
  sessionId,
}: {
  state: InterviewState;
  sessionId: string;
}) {
  const feedback = state.finalFeedback;
  const score = state.finalScore ?? 0;

  const getScoreColor = (score: number) => {
    if (score >= 70) return "text-orient-green";
    if (score >= 50) return "text-orient-orange";
    return "text-red-600";
  };

  const getScoreEmoji = (score: number) => {
    if (score >= 80) return "🌟";
    if (score >= 70) return "✨";
    if (score >= 50) return "👍";
    return "💪";
  };

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        {/* Celebration */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">{getScoreEmoji(score)}</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Entretien terminé !
          </h1>
          <p className="text-gray-600">
            Voici ton évaluation pour {state.filiere}
          </p>
        </div>

        {/* Score card */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-6 text-center">
          <p className="text-gray-600 mb-2">Score global</p>
          <div className={`text-6xl font-bold ${getScoreColor(score)} mb-4`}>
            {score}/100
          </div>

          {feedback?.details && (
            <div className="flex justify-center gap-6 text-sm">
              <div>
                <div className="font-medium">Clarté</div>
                <div className="text-gray-600">{feedback.details.clarte_moyenne}/10</div>
              </div>
              <div>
                <div className="font-medium">Motivation</div>
                <div className="text-gray-600">{feedback.details.motivation_moyenne}/10</div>
              </div>
              <div>
                <div className="font-medium">Connaissance</div>
                <div className="text-gray-600">{feedback.details.connaissance_moyenne}/10</div>
              </div>
            </div>
          )}
        </div>

        {/* Feedback */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Strengths */}
          <div className="bg-green-50 rounded-xl p-6">
            <h3 className="font-bold text-green-900 mb-4">✓ Points forts</h3>
            <ul className="space-y-2">
              {feedback?.points_forts.map((point, i) => (
                <li key={i} className="text-green-800 text-sm flex gap-2">
                  <span>•</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Areas to improve */}
          <div className="bg-orange-50 rounded-xl p-6">
            <h3 className="font-bold text-orange-900 mb-4">→ Axes d&apos;amélioration</h3>
            <ul className="space-y-2">
              {feedback?.axes_amelioration.map((axe, i) => (
                <li key={i} className="text-orange-800 text-sm flex gap-2">
                  <span>•</span>
                  <span>{axe}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4">
          <a
            href={`/api/session/${sessionId}/pdf`}
            className="flex-1 py-3 bg-orient-green text-white text-center rounded-lg font-medium hover:bg-green-700"
          >
            📄 Télécharger le rapport complet
          </a>
          <Link
            href={`/results?session_id=${sessionId}`}
            className="flex-1 py-3 bg-gray-200 text-gray-700 text-center rounded-lg font-medium hover:bg-gray-300"
          >
            ← Retour aux résultats
          </Link>
        </div>
      </div>
    </main>
  );
}

export default function InterviewPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-orient-blue border-t-transparent rounded-full" />
      </div>
    }>
      <InterviewContent />
    </Suspense>
  );
}
