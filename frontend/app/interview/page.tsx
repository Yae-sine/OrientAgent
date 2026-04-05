"use client";

import Link from "next/link";

export default function InterviewPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 bg-gray-50">
      <div className="max-w-md text-center">
        <div className="text-6xl mb-4">🔄</div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Feature Deprecated</h1>
        <p className="text-lg text-gray-600 mb-8">
          La simulation d&apos;entretien a été supprimée. 
          <br />
          <br />
          Consultez vos recommandations personnalisées et préparez-vous directement avec les
          ressources des établissements.
        </p>
        
        <Link
          href="/"
          className="inline-block px-6 py-3 bg-orient-blue text-white rounded-lg font-semibold hover:bg-blue-800 transition-colors"
        >
          ← Retour à l'accueil
        </Link>
      </div>
    </main>
  );
}
