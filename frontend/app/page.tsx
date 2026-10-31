'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Building2,
  CheckCircle2,
  ChevronRight,
  Cpu,
  Database,
  HeartPulse,
  History,
  Layers,
  Microscope,
  Shield,
  ShieldAlert,
  Sparkles,
  Stethoscope,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';

interface DiseaseMeta {
  id: string;
  name: string;
  target_column: string;
  positive_meaning: string;
  negative_meaning: string;
  features_count: number;
  features_preview: string[];
  benchmarks: Array<{
    model: string;
    model_version: string;
    roc_auc: number;
    accuracy: number;
    inference_latency_ms: number;
  }>;
  disclaimer: string;
}

const DISEASE_ICONS: Record<string, any> = {
  diabetes: Activity,
  heart_disease: HeartPulse,
  stroke: Activity,
  asthma: Stethoscope,
  chronic_kidney_disease: Layers,
  liver_disease: Microscope,
  parkinsons: Activity,
  breast_cancer: Shield,
  lung_cancer: Stethoscope,
  hypertension: HeartPulse,
};

export default function HomePage() {
  const [diseases, setDiseases] = useState<DiseaseMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const { setAuthModalOpen } = useAuthStore();

  useEffect(() => {
    async function loadDiseases() {
      try {
        const data = await apiRequest<{ count: number; diseases: DiseaseMeta[] }>('/api/v1/diseases');
        setDiseases(data.diseases || []);
      } catch (err) {
        console.error('Failed to load diseases', err);
      } finally {
        setLoading(false);
      }
    }
    loadDiseases();
  }, []);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 text-white pt-16 pb-24 px-4 sm:px-6 lg:px-8 border-b border-slate-800">
        {/* Glow Effects */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[350px] bg-gradient-to-tr from-teal-500/20 to-cyan-500/10 blur-[120px] pointer-events-none rounded-full" />
        <div className="absolute -top-24 right-10 w-96 h-96 bg-cyan-600/10 blur-[100px] pointer-events-none rounded-full" />

        <div className="relative max-w-5xl mx-auto text-center space-y-6">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-950/80 border border-teal-500/30 text-teal-300 text-xs font-semibold backdrop-blur-md shadow-inner shadow-teal-500/20">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
            <span>Phase 7B Clinical Benchmark Verified • Tabular Foundation Models</span>
          </div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white leading-tight sm:leading-none">
            Multi-Disease Risk Assessment{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 via-cyan-300 to-sky-400">
              Powered by TabPFN & TabICLv2
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-lg text-slate-300 max-w-3xl mx-auto leading-relaxed">
            MediRisk 2.0 evaluates non-diagnostic clinical and lifestyle profiles across{' '}
            <strong className="text-white font-semibold">10 major diseases</strong> using in-context tabular foundation models,
            leakage-safe preprocessing pipelines, and explainable feature attributions.
          </p>

          {/* CTAs */}
          <div className="pt-2 flex flex-wrap items-center justify-center gap-3 sm:gap-4">
            <Link
              href="/assess"
              className="px-6 py-3.5 rounded-xl font-bold text-sm sm:text-base text-white bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 shadow-lg shadow-teal-500/25 flex items-center gap-2 hover:scale-[1.02] transition-all"
            >
              <Stethoscope className="w-5 h-5" />
              <span>Start Risk Assessment</span>
              <ArrowRight className="w-4 h-4 ml-0.5" />
            </Link>

            <Link
              href="#diseases"
              className="px-6 py-3.5 rounded-xl font-semibold text-sm sm:text-base text-slate-200 bg-slate-800/80 hover:bg-slate-800 border border-slate-700 backdrop-blur-sm hover:text-white transition-all flex items-center gap-2"
            >
              <Layers className="w-5 h-5 text-teal-400" />
              <span>Explore 10 Diseases</span>
            </Link>

            <Link
              href="/hospitals"
              className="px-5 py-3.5 rounded-xl font-semibold text-sm sm:text-base text-slate-300 hover:text-white border border-slate-800 hover:bg-slate-800/50 transition-all flex items-center gap-2"
            >
              <Building2 className="w-4 h-4 text-cyan-400" />
              <span>Find Hospitals</span>
            </Link>
          </div>

          {/* Stat Pillars */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 pt-10 text-left">
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800/80 backdrop-blur-md">
              <p className="text-2xl font-black text-white">10</p>
              <p className="text-xs text-slate-400 font-medium">Pathologies Analyzed</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800/80 backdrop-blur-md">
              <p className="text-2xl font-black text-teal-400">0.863</p>
              <p className="text-xs text-slate-400 font-medium">Peak Benchmark ROC-AUC</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800/80 backdrop-blur-md">
              <p className="text-2xl font-black text-cyan-400">2 Models</p>
              <p className="text-xs text-slate-400 font-medium">TabPFN 9.0 & TabICLv2 2.2</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800/80 backdrop-blur-md">
              <p className="text-2xl font-black text-emerald-400">&lt; 1 sec</p>
              <p className="text-xs text-slate-400 font-medium">In-Context Inference Latency</p>
            </div>
          </div>
        </div>
      </section>

      {/* Safety Notice Banner */}
      <section className="bg-amber-500/10 border-b border-amber-500/20 py-3.5 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5 text-xs text-amber-900 dark:text-amber-200">
            <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <span>
              <strong>Academic & Research Disclaimer:</strong> MediRisk 2.0 assessments do not provide medical diagnoses or clinical care plans.
            </span>
          </div>
          <Link
            href="/analytics"
            className="text-xs font-semibold text-amber-900 dark:text-amber-300 hover:underline shrink-0"
          >
            Review Benchmark Protocols →
          </Link>
        </div>
      </section>

      {/* 10 Disease Modules Grid */}
      <section id="diseases" className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300 text-xs font-bold uppercase tracking-wider mb-2">
              Disease Modules
            </div>
            <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
              10 Comprehensive Risk Assessment Panels
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 max-w-2xl">
              Each clinical module utilizes the exact YAML feature schema, data-quality bounds, and trained Tabular Foundation Models.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-500">Categorization:</span>
            <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">Low (&lt;30%)</span>
            <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800">Mod (30-70%)</span>
            <span className="text-xs font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800">High (&gt;70%)</span>
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-64 rounded-2xl bg-slate-200 dark:bg-slate-800" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {diseases.map((d) => {
              const Icon = DISEASE_ICONS[d.id] || Activity;
              const tabicl = d.benchmarks.find((b) => b.model.toLowerCase().includes('tabicl'));
              const tabpfn = d.benchmarks.find((b) => b.model.toLowerCase().includes('tabpfn'));

              return (
                <div
                  key={d.id}
                  className="group relative rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-6 shadow-sm hover:shadow-xl hover:border-teal-400 dark:hover:border-teal-500 transition-all flex flex-col justify-between"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="w-12 h-12 rounded-xl bg-teal-50 dark:bg-teal-950/80 text-teal-600 dark:text-teal-400 flex items-center justify-center group-hover:scale-110 transition-transform shadow-inner">
                        <Icon className="w-6 h-6 stroke-[2.2]" />
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                        {d.features_count} Features
                      </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-1.5 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
                      {d.name}
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-4">
                      Assesses individual risk of {d.positive_meaning.toLowerCase()} vs {d.negative_meaning.toLowerCase()}.
                    </p>

                    {/* Benchmarks preview */}
                    <div className="bg-slate-50 dark:bg-slate-950 rounded-xl p-3 mb-5 space-y-1.5 border border-slate-100 dark:border-slate-800/80">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">TabICLv2 2.2:</span>
                        <span className="font-bold text-teal-600 dark:text-teal-400">
                          {tabicl?.roc_auc ? `ROC-AUC ${tabicl.roc_auc.toFixed(4)}` : 'Verified'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">TabPFN 9.0:</span>
                        <span className="font-bold text-cyan-600 dark:text-cyan-400">
                          {tabpfn?.roc_auc ? `ROC-AUC ${tabpfn.roc_auc.toFixed(4)}` : 'Verified'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Action Link */}
                  <Link
                    href={`/assess/${d.id}`}
                    className="w-full py-2.5 px-4 rounded-xl font-bold text-sm text-center text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/60 hover:bg-teal-600 hover:text-white dark:hover:bg-teal-600 transition-all flex items-center justify-center gap-1.5 group/btn"
                  >
                    <span>Launch Assessment</span>
                    <ChevronRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
                  </Link>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Architecture & Verification Section */}
      <section className="bg-slate-100 dark:bg-slate-900/60 border-y border-slate-200 dark:border-slate-800 py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
              State-of-the-Art Healthcare ML Foundation
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
              Engineered with strict zero-leakage protocols and in-context tabular foundation models.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 flex items-center justify-center mb-4">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">
                In-Context Tabular Learners
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                TabPFN 9.0.0 and TabICLv2 2.2.0 utilize prior-data fitted transformer weights to perform instantaneous Bayesian-style in-context inference without overfitting.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="w-10 h-10 rounded-xl bg-cyan-100 dark:bg-cyan-950 text-cyan-600 flex items-center justify-center mb-4">
                <Shield className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">
                Zero-Leakage Preprocessing
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                MediRiskPreprocessor guarantees strict feature boundary compliance: scalers and imputers are fitted on training splits only, avoiding distribution contamination.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center mb-4">
                <BarChart3 className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">
                Explainable Attributions
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Every predicted probability is matched with individual feature attributions comparing patient values to baseline cohorts, highlighting risk and protective factors.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Hospital Locator Quick Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="rounded-3xl bg-gradient-to-tr from-slate-900 via-teal-950 to-slate-900 p-8 sm:p-12 text-white relative overflow-hidden shadow-2xl border border-teal-800/40">
          <div className="relative max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold border border-teal-500/30">
              <Building2 className="w-3.5 h-3.5" />
              <span>Real Hospital Locator</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Locate Verified Medical Facilities & Centers
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Search real-world healthcare centers, tertiary referral hospitals, and emergency departments with verified addresses, phone numbers, and emergency availability.
            </p>
            <div className="pt-2 flex flex-wrap gap-3">
              <Link
                href="/hospitals"
                className="px-6 py-3 rounded-xl font-bold text-sm bg-teal-500 hover:bg-teal-400 text-slate-950 shadow-lg shadow-teal-500/30 flex items-center gap-2 transition-all"
              >
                <span>Launch Hospital Search</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/dashboard"
                className="px-5 py-3 rounded-xl font-semibold text-sm bg-slate-800/80 hover:bg-slate-800 text-white border border-slate-700 transition-all flex items-center gap-2"
              >
                <span>Go to User Dashboard</span>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
