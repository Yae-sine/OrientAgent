import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OrientAgent - Orientation Scolaire Marocaine",
  description:
    "Système IA multi-agents pour guider les lycéens marocains dans leur orientation post-bac",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-gray-50 antialiased">{children}</body>
    </html>
  );
}
