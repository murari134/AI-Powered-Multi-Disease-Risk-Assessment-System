import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import AuthModal from '@/components/AuthModal';

export const metadata: Metadata = {
  title: 'MediRisk 2.0 — AI-Powered Multi-Disease Risk Assessment',
  description:
    'Research-oriented multi-disease tabular risk assessment platform leveraging Tabular Foundation Models (TabPFN 9.0.0 & TabICLv2 2.2.0).',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="antialiased min-h-screen flex flex-col bg-slate-50/50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-teal-500 selection:text-white">
        <Navbar />
        <main className="flex-1 flex flex-col">{children}</main>
        <Footer />
        <AuthModal />
      </body>
    </html>
  );
}
