import Link from 'next/link';
import { Activity, AlertTriangle, ShieldCheck, Cpu, Database, Award } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="w-full border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 mt-auto">
      {/* Disclaimer Banner */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 py-4 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <p className="text-xs sm:text-sm text-amber-900 dark:text-amber-200/90 leading-relaxed">
            <strong className="font-semibold text-amber-950 dark:text-amber-100">
              Crucial Clinical Safety Disclaimer:
            </strong>{' '}
            MediRisk 2.0 is an academic research and technical benchmarking platform powered by Tabular Foundation Models
            (TabPFN 9.0.0 & TabICLv2 2.2.0) trained on synthetic cohorts. It{' '}
            <strong className="font-semibold underline">does NOT provide medical diagnoses</strong>, clinical treatment advice,
            or prescription recommendations. All risk indices (&lt;30% Low, 30–70% Moderate, &gt;70% High) are illustrative
            computational estimates. In medical emergencies, immediately contact licensed healthcare practitioners or emergency services.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Col 1 */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold text-sm">
                MR
              </div>
              <span className="font-extrabold text-lg tracking-tight text-slate-900 dark:text-white">
                Medi<span className="text-teal-600">Risk</span> 2.0
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Multi-disease risk assessment benchmark utilizing state-of-the-art in-context tabular foundation models across 10 distinct pathologies.
            </p>
            <div className="flex items-center gap-2 text-xs font-semibold text-teal-700 dark:text-teal-300">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              FastAPI ML Inference Active
            </div>
          </div>

          {/* Col 2 */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white mb-3">
              10 Disease Modules
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
              <li><Link href="/assess/diabetes" className="hover:text-teal-600">Type 2 Diabetes Risk</Link></li>
              <li><Link href="/assess/heart_disease" className="hover:text-teal-600">Heart Disease Evaluation</Link></li>
              <li><Link href="/assess/stroke" className="hover:text-teal-600">Stroke Vulnerability Index</Link></li>
              <li><Link href="/assess/hypertension" className="hover:text-teal-600">Hypertension Screening</Link></li>
              <li><Link href="/assess/chronic_kidney_disease" className="hover:text-teal-600">Chronic Kidney Disease</Link></li>
            </ul>
          </div>

          {/* Col 3 */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white mb-3">
              Advanced Modules
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
              <li><Link href="/assess/liver_disease" className="hover:text-teal-600">Liver Pathology Assessment</Link></li>
              <li><Link href="/assess/parkinsons" className="hover:text-teal-600">Parkinson&apos;s Disease Screening</Link></li>
              <li><Link href="/assess/breast_cancer" className="hover:text-teal-600">Breast Cancer Risk Profiler</Link></li>
              <li><Link href="/assess/lung_cancer" className="hover:text-teal-600">Lung Cancer Early Indicator</Link></li>
              <li><Link href="/assess/asthma" className="hover:text-teal-600">Asthma Severity Probability</Link></li>
            </ul>
          </div>

          {/* Col 4 */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white mb-3">
              Platform Architecture
            </h4>
            <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <div className="flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5 text-teal-600" />
                <span>TabICLv2 2.2.0 & TabPFN 9.0.0</span>
              </div>
              <div className="flex items-center gap-2">
                <Database className="w-3.5 h-3.5 text-teal-600" />
                <span>PostgreSQL 16 Relational Store</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                <span>Argon2id & JWT Authentication</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="w-3.5 h-3.5 text-teal-600" />
                <span>Phase 7B Benchmarking Protocol</span>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 dark:text-slate-500 gap-4">
          <p>© 2026 MediRisk 2.0 Academic Research Project. Synthetic Prototype.</p>
          <div className="flex items-center gap-4">
            <Link href="/analytics" className="hover:underline">Phase 7B Benchmarks</Link>
            <Link href="/hospitals" className="hover:underline">Verified Hospital Search</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
