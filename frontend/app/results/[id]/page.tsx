'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Building2,
  CheckCircle2,
  Cpu,
  Download,
  FileText,
  HeartPulse,
  Info,
  Loader2,
  Printer,
  Share2,
  ShieldAlert,
  Stethoscope,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';
import { getRiskColor } from '@/lib/utils';

export default function ResultPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const predictionId = resolvedParams.id;

  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadResult() {
      try {
        const res = await apiRequest(`/api/v1/predictions/${predictionId}`);
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve assessment results.');
      } finally {
        setLoading(false);
      }
    }
    loadResult();
  }, [predictionId]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-16 space-y-4">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin" />
        <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
          Loading clinical risk assessment evaluation...
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-xl mx-auto my-16 p-8 rounded-2xl bg-rose-50 border border-rose-200 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-600 mx-auto" />
        <h2 className="text-xl font-bold text-rose-900">Assessment Record Not Found</h2>
        <p className="text-sm text-rose-700">{error || 'Record ID not recognized.'}</p>
        <Link href="/" className="inline-block px-5 py-2.5 bg-rose-600 text-white rounded-xl text-xs font-bold">
          Return to Disease Panels
        </Link>
      </div>
    );
  }

  const riskColors = getRiskColor(data.risk_level);

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto w-full">
      {/* Top action bar (hidden during print) */}
      <div className="flex flex-wrap items-center justify-between pb-6 mb-6 border-b border-slate-200 dark:border-slate-800 print:hidden gap-3">
        <div className="flex items-center gap-4">
          <Link
            href={`/assess/${data.disease_code.toLowerCase()}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-teal-600"
          >
            <ArrowLeft className="w-4 h-4" />
            Re-run {data.disease_name} Assessment
          </Link>
          {data.assessment_mode === 'combined' && data.assessment_id && (
            <Link
              href={`/results/combined/${data.assessment_id}`}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-teal-600 hover:text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-3 py-1 rounded-lg border border-teal-200 dark:border-teal-800"
            >
              ← Back to Complete 10-Disease Dashboard
            </Link>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePrint}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 flex items-center gap-1.5 shadow-sm"
          >
            <Printer className="w-4 h-4" />
            <span>Download PDF / Print</span>
          </button>
          <Link
            href={`/hospitals?specialty=${data.disease_code.toLowerCase()}`}
            className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 flex items-center gap-1.5 shadow-sm"
          >
            <Building2 className="w-4 h-4" />
            <span>Find Specialist</span>
          </Link>
        </div>
      </div>

      {/* Printable Clinical Report Container */}
      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl p-6 sm:p-10 space-y-8 print:border-none print:shadow-none print:p-0">
        {/* Report Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-6 gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-teal-600 text-white flex items-center justify-center font-bold text-lg">
              MR
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-black text-slate-900 dark:text-white">
                  MediRisk 2.0 Clinical Risk Report
                </h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-100 text-teal-800">
                  RESEARCH PROTOTYPE
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Pathology Evaluation: <strong className="text-slate-800 dark:text-slate-200">{data.disease_name}</strong> • Record ID: {data.prediction_id.slice(0, 8)}
              </p>
            </div>
          </div>

          <div className="text-right sm:border-l sm:pl-6 border-slate-100 dark:border-slate-800">
            <p className="text-[11px] text-slate-400">Date Generated</p>
            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              {new Date(data.created_at).toLocaleDateString()} {new Date(data.created_at).toLocaleTimeString()}
            </p>
          </div>
        </div>

        {/* Risk Score Highlight Card */}
        <div className={`rounded-2xl p-6 sm:p-8 border ${riskColors.border} ${riskColors.bg} flex flex-col md:flex-row md:items-center justify-between gap-6`}>
          <div>
            <span className={`text-xs font-extrabold px-3 py-1 rounded-full uppercase tracking-wider ${riskColors.badge}`}>
              {data.risk_level} RISK CATEGORY
            </span>
            <h2 className="text-4xl sm:text-5xl font-black text-slate-900 dark:text-white mt-3">
              {data.risk_percentage}%
            </h2>
            <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 mt-2 max-w-xl">
              Model evaluated non-diagnostic probability: <strong>{data.raw_probability}</strong>.
              Categorization boundaries: &lt;30% Low Risk, 30–70% Moderate Risk, &gt;70% High Risk.
            </p>
          </div>

          {/* Model info badge */}
          <div className="bg-white/90 dark:bg-slate-950/90 rounded-2xl p-4 border border-slate-200 dark:border-slate-800 text-xs space-y-1.5 shrink-0">
            <div className="flex items-center gap-1.5 font-bold text-slate-800 dark:text-slate-200">
              <Cpu className="w-4 h-4 text-teal-600" />
              <span>Inference Architecture</span>
            </div>
            <p className="text-slate-500">Model: <strong className="text-slate-700 dark:text-slate-300">{data.model_name} {data.model_version}</strong></p>
            <p className="text-slate-500">Type: <span className="text-slate-700 dark:text-slate-300">In-Context Transformer</span></p>
            <p className="text-slate-500">Execution Time: <span className="text-slate-700 dark:text-slate-300">{data.inference_latency_ms} ms</span></p>
          </div>
        </div>

        {/* Contributing Features (Attributions) */}
        <div className="space-y-4">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-2">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-teal-600" />
              <span>Explainable Contributing Factors & Feature Attributions</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Quantifies relative risk acceleration or protective mitigation compared to baseline demographic cohorts.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {data.attributions?.map((attr: any, i: number) => {
              const isPositive = attr.impact === 'INCREASES_RISK';
              const isProtective = attr.impact === 'PROTECTIVE';

              return (
                <div
                  key={i}
                  className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200">{attr.feature_label}</p>
                    <p className="text-xs text-slate-500">Recorded: <strong className="text-slate-700 dark:text-slate-300">{attr.feature_value}</strong></p>
                  </div>

                  <div className="text-right">
                    <span
                      className={`inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full ${
                        isPositive
                          ? 'bg-rose-100 text-rose-800'
                          : isProtective
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {isPositive ? <TrendingUp className="w-3 h-3" /> : isProtective ? <TrendingDown className="w-3 h-3" /> : null}
                      {isPositive ? 'Elevates Risk' : isProtective ? 'Protective' : 'Neutral'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Personalized Clinical Prototype Recommendations */}
        <div className="space-y-4">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-2">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-600" />
              <span>Prioritized Clinical Prototype Recommendations</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Algorithmic guidance tailored to the patient profile and identified risk factors.
            </p>
          </div>

          <div className="space-y-3">
            {data.recommendations?.map((rec: any, i: number) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-950 flex items-start gap-3.5 shadow-sm"
              >
                <div className="w-6 h-6 rounded-full bg-teal-50 dark:bg-teal-950 text-teal-700 font-black text-xs flex items-center justify-center shrink-0 mt-0.5">
                  {rec.priority}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white">{rec.title}</h4>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">{rec.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Submitted Features Table */}
        {data.input_data && Object.keys(data.input_data).length > 0 && (
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Submitted Input Parameters
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              {Object.entries(data.input_data).map(([k, v]) => (
                <div key={k} className="p-2 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800">
                  <p className="text-[10px] text-slate-400 font-medium truncate uppercase">{k.replace(/_/g, ' ')}</p>
                  <p className="font-bold text-slate-800 dark:text-slate-200 truncate">{String(v)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Safety Disclaimer */}
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-900 dark:text-amber-300 leading-relaxed">
          <p>
            <strong>IMPORTANT CLINICAL SAFETY NOTICE:</strong> {data.disclaimer}
          </p>
        </div>
      </div>
    </div>
  );
}
