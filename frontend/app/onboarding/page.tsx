"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type Step = 1 | 2 | 3 | 4;

interface FormData {
  nom: string;
  serie_bac: string;
  ville: string;
  langue: string;
  budget: string;
  notes: Record<string, number>;
  interets: string[];
}

const SERIES_BAC = ["Sciences", "Lettres", "Economie", "Technique"];
const VILLES = [
  "Casablanca",
  "Rabat",
  "Fès",
  "Marrakech",
  "Tanger",
  "Agadir",
  "Meknès",
  "Oujda",
  "Kenitra",
  "Tétouan",
  "Settat",
  "El Jadida",
];
const LANGUES = [
  { value: "fr", label: "Français" },
  { value: "ar", label: "Arabe" },
  { value: "en", label: "Anglais" },
];
const BUDGETS = [
  { value: "public", label: "Public uniquement (gratuit)" },
  { value: "prive_abordable", label: "Privé abordable (< 50 000 MAD/an)" },
  { value: "prive_premium", label: "Privé premium (pas de limite)" },
];
const INTERETS = [
  "Informatique",
  "Robotique",
  "Intelligence Artificielle",
  "Mathématiques",
  "Physique",
  "Chimie",
  "Biologie",
  "Médecine",
  "Commerce",
  "Finance",
  "Marketing",
  "Droit",
  "Langues",
  "Littérature",
  "Histoire",
  "Génie Civil",
  "Architecture",
  "Entrepreneuriat",
];

const SUBJECTS_BY_SERIE: Record<string, string[]> = {
  Sciences: ["maths", "physique", "svt", "francais", "arabe", "anglais"],
  Lettres: ["arabe", "francais", "histoire_geo", "philo", "anglais"],
  Economie: ["maths", "economie", "compta", "francais", "arabe", "anglais"],
  Technique: ["maths", "physique", "techno", "francais", "arabe"],
};

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<FormData>({
    nom: "",
    serie_bac: "",
    ville: "",
    langue: "fr",
    budget: "public",
    notes: {},
    interets: [],
  });

  const updateField = <K extends keyof FormData>(
    field: K,
    value: FormData[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleInteret = (interet: string) => {
    setFormData((prev) => ({
      ...prev,
      interets: prev.interets.includes(interet)
        ? prev.interets.filter((i) => i !== interet)
        : [...prev.interets, interet],
    }));
  };

  const updateNote = (subject: string, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0 && numValue <= 20) {
      setFormData((prev) => ({
        ...prev,
        notes: { ...prev.notes, [subject]: numValue },
      }));
    }
  };

  const canProceed = (): boolean => {
    switch (step) {
      case 1:
        return formData.nom.length >= 2 && formData.serie_bac !== "";
      case 2:
        const subjects = SUBJECTS_BY_SERIE[formData.serie_bac] || [];
        return subjects.every((s) => formData.notes[s] !== undefined);
      case 3:
        return formData.interets.length >= 1;
      case 4:
        return formData.ville !== "";
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (step < 4) {
      setStep((step + 1) as Step);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep((step - 1) as Step);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch("/api/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Erreur lors de la création de la session");
      }

      const data = await response.json();
      router.push(`/results?session_id=${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur est survenue");
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-orient-blue mb-2">
            🎓 OrientAgent
          </h1>
          <p className="text-gray-600">Étape {step} sur 4</p>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-orient-blue transition-all duration-300"
              style={{ width: `${(step / 4) * 100}%` }}
            />
          </div>
        </div>

        {/* Form card */}
        <div className="bg-white rounded-xl shadow-lg p-6 md:p-8">
          {step === 1 && (
            <Step1
              formData={formData}
              updateField={updateField}
            />
          )}

          {step === 2 && (
            <Step2
              formData={formData}
              updateNote={updateNote}
            />
          )}

          {step === 3 && (
            <Step3
              formData={formData}
              toggleInteret={toggleInteret}
            />
          )}

          {step === 4 && (
            <Step4
              formData={formData}
              updateField={updateField}
            />
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t">
            {step > 1 ? (
              <button
                onClick={handleBack}
                className="px-6 py-2 text-gray-600 hover:text-gray-900"
              >
                ← Retour
              </button>
            ) : (
              <div />
            )}

            {step < 4 ? (
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className="px-6 py-2 bg-orient-blue text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-800"
              >
                Continuer →
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!canProceed() || isSubmitting}
                className="px-8 py-3 bg-orient-green text-white rounded-lg font-semibold disabled:opacity-50 hover:bg-green-700"
              >
                {isSubmitting ? "Analyse en cours..." : "🚀 Lancer l'analyse"}
              </button>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

// Step 1: Basic Info
function Step1({
  formData,
  updateField,
}: {
  formData: FormData;
  updateField: <K extends keyof FormData>(field: K, value: FormData[K]) => void;
}) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Informations générales
      </h2>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Ton prénom ou nom
          </label>
          <input
            type="text"
            value={formData.nom}
            onChange={(e) => updateField("nom", e.target.value)}
            placeholder="Ex: Ahmed, Fatima..."
            className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-orient-blue focus:border-orient-blue"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Série du Baccalauréat
          </label>
          <div className="grid grid-cols-2 gap-3">
            {SERIES_BAC.map((serie) => (
              <button
                key={serie}
                onClick={() => updateField("serie_bac", serie)}
                className={`p-4 border-2 rounded-lg text-left transition-colors ${
                  formData.serie_bac === serie
                    ? "border-orient-blue bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <span className="font-medium">{serie}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Step 2: Notes
function Step2({
  formData,
  updateNote,
}: {
  formData: FormData;
  updateNote: (subject: string, value: string) => void;
}) {
  const subjects = SUBJECTS_BY_SERIE[formData.serie_bac] || [];

  const subjectLabels: Record<string, string> = {
    maths: "Mathématiques",
    physique: "Physique",
    svt: "SVT",
    francais: "Français",
    arabe: "Arabe",
    anglais: "Anglais",
    histoire_geo: "Histoire-Géographie",
    philo: "Philosophie",
    economie: "Économie",
    compta: "Comptabilité",
    techno: "Technologie",
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Tes notes moyennes
      </h2>
      <p className="text-gray-600 mb-6">
        Indique tes moyennes pour chaque matière (sur 20)
      </p>

      <div className="space-y-4">
        {subjects.map((subject) => (
          <div key={subject} className="flex items-center gap-4">
            <label className="w-40 text-sm font-medium text-gray-700">
              {subjectLabels[subject] || subject}
            </label>
            <input
              type="number"
              min="0"
              max="20"
              step="0.5"
              value={formData.notes[subject] ?? ""}
              onChange={(e) => updateNote(subject, e.target.value)}
              placeholder="0 - 20"
              className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orient-blue"
            />
            <span className="text-gray-400">/20</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Step 3: Interests
function Step3({
  formData,
  toggleInteret,
}: {
  formData: FormData;
  toggleInteret: (interet: string) => void;
}) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Tes centres d&apos;intérêt
      </h2>
      <p className="text-gray-600 mb-6">
        Sélectionne au moins 1 domaine qui t&apos;intéresse
      </p>

      <div className="flex flex-wrap gap-2">
        {INTERETS.map((interet) => (
          <button
            key={interet}
            onClick={() => toggleInteret(interet)}
            className={`px-4 py-2 rounded-full border-2 transition-colors ${
              formData.interets.includes(interet)
                ? "border-orient-blue bg-orient-blue text-white"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            {interet}
          </button>
        ))}
      </div>

      {formData.interets.length > 0 && (
        <p className="mt-4 text-sm text-orient-green">
          ✓ {formData.interets.length} intérêt(s) sélectionné(s)
        </p>
      )}
    </div>
  );
}

// Step 4: Constraints
function Step4({
  formData,
  updateField,
}: {
  formData: FormData;
  updateField: <K extends keyof FormData>(field: K, value: FormData[K]) => void;
}) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Tes contraintes
      </h2>
      <p className="text-gray-600 mb-6">
        Ces informations nous aident à affiner les recommandations
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Ville préférée pour les études
          </label>
          <select
            value={formData.ville}
            onChange={(e) => updateField("ville", e.target.value)}
            className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-orient-blue"
          >
            <option value="">Sélectionne une ville</option>
            {VILLES.map((ville) => (
              <option key={ville} value={ville}>
                {ville}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Langue préférée
          </label>
          <div className="flex gap-3">
            {LANGUES.map((langue) => (
              <button
                key={langue.value}
                onClick={() => updateField("langue", langue.value)}
                className={`flex-1 p-3 border-2 rounded-lg transition-colors ${
                  formData.langue === langue.value
                    ? "border-orient-blue bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                {langue.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Budget
          </label>
          <div className="space-y-2">
            {BUDGETS.map((budget) => (
              <button
                key={budget.value}
                onClick={() => updateField("budget", budget.value)}
                className={`w-full p-3 border-2 rounded-lg text-left transition-colors ${
                  formData.budget === budget.value
                    ? "border-orient-blue bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                {budget.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
