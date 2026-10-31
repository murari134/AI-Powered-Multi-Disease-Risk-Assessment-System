'use client';

import Link from 'next/link';
import {
  Activity,
  ArrowRight,
  Brain,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Compass,
  Cpu,
  FileSpreadsheet,
  FileText,
  Heart,
  HeartPulse,
  Layers,
  Microscope,
  Shield,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  TrendingUp,
} from 'lucide-react';

const INDIVIDUAL_DISEASES = [
  {
    id: 'diabetes',
    name: 'Diabetes Risk',
    category: 'Endocrine & Metabolic',
    description: 'Fasting glucose, insulin kinetics, BMI, blood pressure, and hereditary pedigree markers.',
    featuresCount: 14,
    benchmarkMetric: 'AUC 0.88 · Accuracy 82.5%',
    icon: Activity,
    color: 'from-blue-500/10 to-teal-500/10 border-teal-500/30 text-teal-600 dark:text-teal-400',
  },
  {
    id: 'heart_disease',
    name: 'Heart Disease',
    category: 'Cardiovascular',
    description: 'Angina profile, exercise stress testing, resting ECG, ST depression, and serum cholesterol.',
    featuresCount: 16,
    benchmarkMetric: 'AUC 0.91 · Accuracy 85.0%',
    icon: HeartPulse,
    color: 'from-rose-500/10 to-red-500/10 border-rose-500/30 text-rose-600 dark:text-rose-400',
  },
  {
    id: 'stroke',
    name: 'Stroke Risk',
    category: 'Cerebrovascular',
    description: 'Hypertension status, atrial fibrillation history, glucose dynamics, and lifestyle factors.',
    featuresCount: 13,
    benchmarkMetric: 'AUC 0.87 · Accuracy 83.2%',
    icon: Activity,
    color: 'from-purple-500/10 to-indigo-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400',
  },
  {
    id: 'hypertension',
    name: 'Hypertension',
    category: 'Cardiovascular & Vascular',
    description: 'Resting systolic/diastolic blood pressure, sodium intake, heart rate, and metabolic flags.',
    featuresCount: 15,
    benchmarkMetric: 'AUC 0.89 · Accuracy 84.1%',
    icon: Heart,
    color: 'from-amber-500/10 to-orange-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400',
  },
  {
    id: 'chronic_kidney_disease',
    name: 'Chronic Kidney Disease',
    category: 'Renal Function',
    description: 'Serum creatinine, blood urea nitrogen, urinalysis markers (albumin, sugar, pus cells), and electrolytes.',
    featuresCount: 19,
    benchmarkMetric: 'AUC 0.96 · Accuracy 92.4%',
    icon: Layers,
    color: 'from-cyan-500/10 to-blue-500/10 border-cyan-500/30 text-cyan-600 dark:text-cyan-400',
  },
  {
    id: 'liver_disease',
    name: 'Liver Disease',
    category: 'Hepatic & Metabolic',
    description: 'Total/direct bilirubin, alkaline phosphatase, ALT, AST enzymes, and total proteins ratio.',
    featuresCount: 15,
    benchmarkMetric: 'AUC 0.86 · Accuracy 81.8%',
    icon: Microscope,
    color: 'from-emerald-500/10 to-teal-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400',
  },
  {
    id: 'parkinsons',
    name: "Parkinson's Disease",
    category: 'Neurological & Motor',
    description: 'Vocal acoustic measures (jitter, shimmer, NHR/HNR), tremor ratings, and motor rigidity scores.',
    featuresCount: 14,
    benchmarkMetric: 'AUC 0.93 · Accuracy 88.6%',
    icon: Brain,
    color: 'from-violet-500/10 to-purple-500/10 border-violet-500/30 text-violet-600 dark:text-violet-400',
  },
  {
    id: 'breast_cancer',
    name: 'Breast Cancer Risk',
    category: 'Oncology & Tissue Imaging',
    description: 'Fine-needle aspirate cell morphology (radius, texture, perimeter, concavity) and genetics.',
    featuresCount: 16,
    benchmarkMetric: 'AUC 0.97 · Accuracy 94.2%',
    icon: Shield,
    color: 'from-pink-500/10 to-rose-500/10 border-pink-500/30 text-pink-600 dark:text-pink-400',
  },
  {
    id: 'lung_cancer',
    name: 'Lung Cancer Risk',
    category: 'Pulmonary Oncology',
    description: 'Smoking pack-years, radon/occupational exposure, hemoptysis, and chronic respiratory symptoms.',
    featuresCount: 18,
    benchmarkMetric: 'AUC 0.90 · Accuracy 86.7%',
    icon: Stethoscope,
    color: 'from-slate-500/10 to-zinc-500/10 border-slate-500/30 text-slate-600 dark:text-slate-400',
  },
  {
    id: 'asthma',
    name: 'Asthma Risk',
    category: 'Respiratory Health',
    description: 'Spirometry (FEV1/FVC ratio), air quality index, allergic triggers, and respiratory infections.',
    featuresCount: 14,
    benchmarkMetric: 'AUC 0.88 · Accuracy 83.9%',
    icon: Stethoscope,
    color: 'from-teal-500/10 to-emerald-500/10 border-teal-500/30 text-teal-600 dark:text-teal-400',
  },
];

export default function AssessmentSelectionPage() {
  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-12">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-700 dark:text-teal-300 text-xs font-bold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Clinical Assessment Center</span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-slate-900 dark:text-white tracking-tight">
          Select Your Assessment Mode
        </h1>
        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300">
          MediRisk 2.0 provides two clinical evaluation pathways powered by verified Tabular Foundation Models (TabICLv2 and TabPFN). Choose between an all-in-one comprehensive screening or a targeted disease assessment.
        </p>
      </div>

      {/* Pathway Selection Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        {/* Option 1: Complete Health Assessment (Prominent Card) */}
        <div className="lg:col-span-7 rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900 to-teal-950 p-8 sm:p-10 text-white flex flex-col justify-between shadow-2xl border border-teal-500/30 relative overflow-hidden group">
          {/* Decorative glow */}
          <div className="absolute top-0 right-0 w-80 h-80 bg-teal-500/15 rounded-full blur-3xl pointer-events-none group-hover:bg-teal-500/25 transition-all" />

          <div className="space-y-6 relative z-10">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-500 text-slate-950 font-extrabold text-xs tracking-wide uppercase shadow-sm">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Mode A · Complete Panel
              </span>
              <span className="text-xs text-teal-300 font-semibold bg-teal-950/60 px-2.5 py-1 rounded-lg border border-teal-500/30">
                10 Diseases Evaluated
              </span>
            </div>

            <div className="space-y-3">
              <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
                Complete Health Assessment
              </h2>
              <p className="text-sm text-slate-300 leading-relaxed">
                Evaluate your non-diagnostic health risk across all 10 chronic disease categories in a single unified submission. Enter your clinical, lifestyle, and lab parameters once; our intelligent mapping engine prepares and runs each dedicated foundation model in parallel.
              </p>
            </div>

            {/* Feature Highlights */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-2">
              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <div className="w-5 h-5 rounded-md bg-teal-500/20 text-teal-400 flex items-center justify-center shrink-0 mt-0.5">
                  ✓
                </div>
                <div>
                  <strong className="block text-white font-semibold">One Unified Form</strong>
                  Common health information asked only once
                </div>
              </div>

              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <div className="w-5 h-5 rounded-md bg-teal-500/20 text-teal-400 flex items-center justify-center shrink-0 mt-0.5">
                  ✓
                </div>
                <div>
                  <strong className="block text-white font-semibold">Accurate Feature Mapping</strong>
                  Each model receives its exact YAML-specified inputs
                </div>
              </div>

              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <div className="w-5 h-5 rounded-md bg-teal-500/20 text-teal-400 flex items-center justify-center shrink-0 mt-0.5">
                  ✓
                </div>
                <div>
                  <strong className="block text-white font-semibold">Combined Results Dashboard</strong>
                  Side-by-side risk comparison charts & breakdown
                </div>
              </div>

              <div className="flex items-start gap-2.5 text-xs text-slate-200">
                <div className="w-5 h-5 rounded-md bg-teal-500/20 text-teal-400 flex items-center justify-center shrink-0 mt-0.5">
                  ✓
                </div>
                <div>
                  <strong className="block text-white font-semibold">Comprehensive PDF Export</strong>
                  Single-click clinical report generation
                </div>
              </div>
            </div>

            {/* Disease tags */}
            <div className="pt-2">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Simultaneously Evaluates:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {[
                  'Diabetes',
                  'Heart Disease',
                  'Stroke',
                  'Asthma',
                  'Chronic Kidney Disease',
                  'Liver Disease',
                  "Parkinson's",
                  'Breast Cancer',
                  'Lung Cancer',
                  'Hypertension',
                ].map((d) => (
                  <span
                    key={d}
                    className="text-[11px] px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700/60"
                  >
                    {d}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-8 relative z-10">
            <Link
              href="/assess/complete"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-2xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-black text-sm tracking-wide shadow-lg shadow-teal-500/25 transition-all hover:scale-[1.02]"
            >
              <span>Begin Complete Health Assessment</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Option 2: Individual Disease Pathway Overview Card */}
        <div className="lg:col-span-5 rounded-3xl bg-white dark:bg-slate-900 p-8 sm:p-10 border border-slate-200 dark:border-slate-800 shadow-xl flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold text-xs uppercase tracking-wide border border-slate-200 dark:border-slate-700">
              <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
              Mode B · Targeted Evaluation
            </span>

            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900 dark:text-white">
              Individual Disease Assessment
            </h2>

            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              Focus specifically on a single disease condition. The individual form collects only the precise diagnostic parameters required for that illness, eliminating unrelated questions and delivering a rapid, condition-specific risk analysis.
            </p>

            <ul className="space-y-3 pt-2 text-xs text-slate-600 dark:text-slate-400">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                <span>Collects only relevant disease-specific features</span>
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                <span>Condition-specific model explainability & SHAP attributions</span>
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                <span>Direct clinical prototype recommendations & facility locator</span>
              </li>
            </ul>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-3">
            <p className="text-xs font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider">
              Quick Individual Launch:
            </p>
            <div className="grid grid-cols-2 gap-2">
              <Link
                href="/assess/diabetes"
                className="px-3 py-2 rounded-xl text-xs font-semibold bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:border-teal-500 text-slate-800 dark:text-slate-200 text-center transition-colors"
              >
                Diabetes
              </Link>
              <Link
                href="/assess/heart_disease"
                className="px-3 py-2 rounded-xl text-xs font-semibold bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:border-teal-500 text-slate-800 dark:text-slate-200 text-center transition-colors"
              >
                Heart Disease
              </Link>
              <Link
                href="/assess/stroke"
                className="px-3 py-2 rounded-xl text-xs font-semibold bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:border-teal-500 text-slate-800 dark:text-slate-200 text-center transition-colors"
              >
                Stroke
              </Link>
              <Link
                href="/assess/hypertension"
                className="px-3 py-2 rounded-xl text-xs font-semibold bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:border-teal-500 text-slate-800 dark:text-slate-200 text-center transition-colors"
              >
                Hypertension
              </Link>
            </div>
            <p className="text-[11px] text-center text-slate-500 dark:text-slate-400">
              Scroll down to choose from all 10 diseases ↓
            </p>
          </div>
        </div>
      </div>

      {/* Individual Diseases Catalog Grid */}
      <div className="space-y-6 pt-4">
        <div className="border-b border-slate-200 dark:border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              All 10 Individual Disease Assessments
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Select any disease module to open its dedicated clinical assessment form.
            </p>
          </div>
          <span className="text-xs font-bold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/60 px-3 py-1 rounded-full border border-teal-200 dark:border-teal-800 self-start sm:self-auto">
            10 Foundation Models Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {INDIVIDUAL_DISEASES.map((dis) => {
            const Icon = dis.icon;
            return (
              <div
                key={dis.id}
                className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 flex flex-col justify-between hover:shadow-lg hover:border-teal-500/50 transition-all group"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div
                      className={`w-11 h-11 rounded-xl bg-gradient-to-tr ${dis.color} flex items-center justify-center border`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                      {dis.category}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-black text-slate-900 dark:text-white group-hover:text-teal-600 transition-colors">
                      {dis.name}
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {dis.description}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                    <span>{dis.featuresCount} Clinical Features</span>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">{dis.benchmarkMetric}</span>
                  </div>
                </div>

                <div className="pt-5 mt-4 border-t border-slate-100 dark:border-slate-800">
                  <Link
                    href={`/assess/${dis.id}`}
                    className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-slate-100 hover:bg-teal-500 hover:text-slate-950 dark:bg-slate-800 dark:hover:bg-teal-500 text-slate-800 dark:text-slate-200 flex items-center justify-center gap-1.5 transition-all shadow-sm"
                  >
                    <span>Assess {dis.name.replace(' Risk', '')}</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
