'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Download,
  ExternalLink,
  Eye,
  FileSpreadsheet,
  FileText,
  Heart,
  HeartPulse,
  Info,
  Layers,
  Loader2,
  MapPin,
  Microscope,
  Printer,
  Share2,
  Shield,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';
import { formatPercent, getRiskColor } from '@/lib/utils';

const CATEGORY_MAP: Record<string, string> = {
  DIABETES: 'Endocrine & Metabolic',
  HEART_DISEASE: 'Cardiovascular',
  STROKE: 'Cerebrovascular',
  ASTHMA: 'Respiratory',
  CHRONIC_KIDNEY_DISEASE: 'Renal Function',
  LIVER_DISEASE: 'Hepatic & Metabolic',
  PARKINSONS: 'Neurological & Motor',
  BREAST_CANCER: 'Oncology',
  LUNG_CANCER: 'Pulmonary Oncology',
  HYPERTENSION: 'Cardiovascular & Vascular',
};

export default function CombinedResultPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const assessmentId = resolvedParams.id;

  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeModalDisease, setActiveModalDisease] = useState<any | null>(null);

  useEffect(() => {
    async function fetchAssessment() {
      try {
        const res = await apiRequest(`/api/v1/assessments/complete/${assessmentId}`);
        setData(res);
      } catch (err: any) {
        console.error('Failed to retrieve combined assessment', err);
        setError(err.message || 'Combined assessment record not found.');
      } finally {
        setLoading(false);
      }
    }
    fetchAssessment();
  }, [assessmentId]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-16 space-y-4">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin" />
        <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
          Compiling multi-disease assessment profile across all 10 foundation models...
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-xl mx-auto my-16 p-8 rounded-2xl bg-rose-50 border border-rose-200 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-600 mx-auto" />
        <h2 className="text-xl font-bold text-rose-900">Assessment Record Not Found</h2>
        <p className="text-sm text-rose-700">{error || 'ID not recognized in database history.'}</p>
        <Link
          href="/assess"
          className="inline-block px-5 py-2.5 bg-rose-600 text-white rounded-xl text-xs font-bold"
        >
          Return to Assessment Center
        </Link>
      </div>
    );
  }

  const results = data.results || [];
  const summary = data.summary || {
    high_risk_count: 0,
    moderate_risk_count: 0,
    low_risk_count: 0,
    highest_risk_disease: 'None',
    highest_risk_percentage: 0,
  };

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-10">
      {/* Top Action Bar (Hidden during PDF print) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800 print:hidden">
        <Link
          href="/assess"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-teal-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Start Another Assessment</span>
        </Link>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePrint}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2 shadow-sm transition-all"
          >
            <Printer className="w-4 h-4 text-teal-600" />
            <span>Download PDF / Print Report</span>
          </button>
          <Link
            href="/hospitals"
            className="px-4 py-2 rounded-xl text-xs font-bold text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 hover:bg-teal-100 flex items-center gap-2 shadow-sm transition-all"
          >
            <Building2 className="w-4 h-4" />
            <span>Find Verified Hospitals</span>
          </Link>
        </div>
      </div>

      {/* Printable Clinical Header */}
      <div className="rounded-3xl bg-gradient-to-tr from-slate-900 via-slate-900 to-teal-950 p-6 sm:p-10 text-white border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold border border-teal-500/30">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
            <span>Multi-Disease Clinical Intelligence Report</span>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            ID: {data.assessment_id.slice(0, 18)}... · Mode: {data.assessment_mode.toUpperCase()}
          </span>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl sm:text-4xl font-black tracking-tight">
            Comprehensive 10-Disease Risk Profile
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
            Evaluated using stratified Tabular Foundation Models (TabICLv2 2.2.0 / TabPFN 9.0.0). Results represent non-diagnostic prototype risk probabilities derived from synthetic benchmarking distributions.
          </p>
        </div>

        <div className="pt-2 flex flex-wrap items-center gap-6 text-xs text-slate-400 border-t border-slate-800/80">
          <div>
            Evaluated:{' '}
            <strong className="text-white">
              {new Date(data.created_at).toLocaleDateString()} at{' '}
              {new Date(data.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </strong>
          </div>
          <div>
            Total Diseases Evaluated: <strong className="text-white">{data.diseases_evaluated}</strong>
          </div>
          <div>
            Protocol:{' '}
            <strong className="text-teal-300">Phase 7B Independent Foundation Pipeline</strong>
          </div>
        </div>
      </div>

      {/* Summary KPI Tier Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">High Risk Diseases</p>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-black text-rose-600 dark:text-rose-400">
              {summary.high_risk_count}
            </h3>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-rose-50 dark:bg-rose-950 text-rose-700 dark:text-rose-300">
              &gt; 70% Risk
            </span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Moderate Risk Diseases</p>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-black text-amber-600 dark:text-amber-400">
              {summary.moderate_risk_count}
            </h3>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
              30% – 70%
            </span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Low Risk Diseases</p>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-black text-emerald-600 dark:text-emerald-400">
              {summary.low_risk_count}
            </h3>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
              &lt; 30% Risk
            </span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Highest Flagged Risk</p>
          <div className="flex items-baseline justify-between">
            <h3 className="text-lg font-black text-slate-900 dark:text-white truncate">
              {summary.highest_risk_disease || 'None'}
            </h3>
            <span className="text-xs font-bold text-teal-600">
              {summary.highest_risk_percentage}%
            </span>
          </div>
        </div>
      </div>

      {/* Clinical Disclaimer Notice */}
      <div className="p-4 rounded-2xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 flex items-start gap-3 text-xs leading-relaxed">
        <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <strong>Notice on Independent Multi-Disease Risk Metrics:</strong> MediRisk 2.0 treats each of the 10 disease risks as scientifically independent assessments. Individual probabilities are never averaged together into a single global score, as clinical diseases have distinct etiologies and risk factor interactions.
        </div>
      </div>

      {/* Comparison Chart: Horizontal Probability Overview */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div>
            <h2 className="text-xl font-black text-slate-900 dark:text-white tracking-tight">
              Cross-Disease Probability Comparison
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Model-calibrated risk probability across all 10 evaluated diseases.
            </p>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 text-xs font-semibold">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-emerald-500" />
              <span>Low (&lt; 30%)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-amber-500" />
              <span>Moderate (30-70%)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500" />
              <span>High (&gt; 70%)</span>
            </div>
          </div>
        </div>

        {/* Horizontal Bars */}
        <div className="space-y-4">
          {results.map((r: any) => {
            const prob = r.risk_percentage || 0;
            const colors = getRiskColor(r.risk_level);
            return (
              <div key={r.disease_code} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-slate-800 dark:text-slate-200">
                    {r.disease_name}{' '}
                    <span className="font-normal text-slate-400">
                      ({CATEGORY_MAP[r.disease_code] || 'General'})
                    </span>
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold ${colors.badge}`}>
                      {r.risk_level}
                    </span>
                    <span className="font-mono text-slate-900 dark:text-white w-12 text-right">
                      {prob.toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Bar */}
                <div className="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden relative">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      r.risk_level === 'HIGH'
                        ? 'bg-rose-500'
                        : r.risk_level === 'MODERATE'
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(100, Math.max(5, prob))}%` }}
                  />
                  {/* Guideline thresholds */}
                  <div className="absolute top-0 bottom-0 left-[30%] w-px bg-slate-300 dark:bg-slate-600" />
                  <div className="absolute top-0 bottom-0 left-[70%] w-px bg-slate-300 dark:bg-slate-600" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 10 Disease Detailed Cards Grid */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
          <div>
            <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Individual Disease Findings & Recommendations
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Detailed breakdown of risk attributions, key contributing factors, and clinical guidance for each disease.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {results.map((r: any) => {
            const colors = getRiskColor(r.risk_level);
            const attributions = r.attributions || [];
            const recommendations = r.recommendations || [];
            const topRiskFactors = attributions.filter((a: any) => a.impact === 'INCREASES_RISK').slice(0, 3);
            const topProtective = attributions.filter((a: any) => a.impact === 'PROTECTIVE').slice(0, 2);

            return (
              <div
                key={r.disease_code}
                className="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow space-y-5"
              >
                <div className="space-y-4">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        {CATEGORY_MAP[r.disease_code] || 'Condition'}
                      </span>
                      <h3 className="text-xl font-black text-slate-900 dark:text-white">
                        {r.disease_name}
                      </h3>
                      <span className="text-[11px] text-slate-400 font-mono">
                        Model: {r.model_name} {r.model_version}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-black inline-block ${colors.badge}`}>
                        {r.risk_level} RISK
                      </span>
                      <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                        {(r.risk_percentage || 0).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Factor Attributions */}
                  <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      Key Influencing Factors:
                    </p>

                    {topRiskFactors.length > 0 ? (
                      <div className="space-y-1.5">
                        {topRiskFactors.map((rf: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between text-xs p-2 rounded-xl bg-rose-50/60 dark:bg-rose-950/30 border border-rose-100 dark:border-rose-900/40 text-rose-900 dark:text-rose-200"
                          >
                            <span className="font-semibold">{rf.feature_label}</span>
                            <span className="font-mono text-[11px] text-rose-700 dark:text-rose-300">
                              {rf.feature_value} (Elevated)
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No critical risk factors flagged.</p>
                    )}

                    {topProtective.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        {topProtective.map((pf: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between text-xs p-2 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/40 text-emerald-900 dark:text-emerald-200"
                          >
                            <span className="font-semibold">{pf.feature_label}</span>
                            <span className="font-mono text-[11px] text-emerald-700 dark:text-emerald-300">
                              {pf.feature_value} (Protective)
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Primary Recommendation */}
                  {recommendations.length > 0 && (
                    <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs space-y-1">
                      <p className="font-bold text-slate-800 dark:text-slate-200">
                        {recommendations[0].title}
                      </p>
                      <p className="text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                        {recommendations[0].description}
                      </p>
                    </div>
                  )}
                </div>

                {/* Footer Action: Open Details Modal */}
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <button
                    onClick={() => setActiveModalDisease(r)}
                    className="text-xs font-bold text-teal-600 dark:text-teal-400 hover:text-teal-700 flex items-center gap-1.5 transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Full Analysis & Guidance</span>
                  </button>

                  <Link
                    href={`/assess/${r.disease_code.toLowerCase()}`}
                    className="text-xs font-medium text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    Assess Separately →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed Analysis Modal */}
      {activeModalDisease && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8 max-h-[90vh] overflow-y-auto space-y-6">
            <div className="flex items-start justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
              <div>
                <span className="text-[10px] font-bold text-teal-600 uppercase tracking-wider">
                  Condition Specific Report
                </span>
                <h3 className="text-2xl font-black text-slate-900 dark:text-white">
                  {activeModalDisease.disease_name}
                </h3>
                <p className="text-xs text-slate-500">
                  {CATEGORY_MAP[activeModalDisease.disease_code]} · Model:{' '}
                  {activeModalDisease.model_name} {activeModalDisease.model_version}
                </p>
              </div>
              <button
                onClick={() => setActiveModalDisease(null)}
                className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 hover:text-slate-900"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Probability Callout */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase">Assessment Outcome</p>
                <p className="text-xl font-black text-slate-900 dark:text-white">
                  {(activeModalDisease.risk_percentage || 0).toFixed(1)}% Risk Probability
                </p>
              </div>
              <span
                className={`px-3 py-1 rounded-full text-xs font-black ${
                  getRiskColor(activeModalDisease.risk_level).badge
                }`}
              >
                {activeModalDisease.risk_level} RISK
              </span>
            </div>

            {/* Full Attributions Table */}
            <div className="space-y-3">
              <h4 className="text-xs font-black text-slate-900 dark:text-white uppercase tracking-wider">
                Feature Attributions (Patient Values vs Baseline)
              </h4>
              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-slate-800/70 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-bold">
                    <tr>
                      <th className="p-3">Feature Name</th>
                      <th className="p-3">Patient Value</th>
                      <th className="p-3">Clinical Impact</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {(activeModalDisease.attributions || []).map((a: any, i: number) => (
                      <tr key={i} className="hover:bg-slate-50/50">
                        <td className="p-3 font-semibold text-slate-800 dark:text-slate-200">
                          {a.feature_label}
                        </td>
                        <td className="p-3 font-mono text-slate-600 dark:text-slate-400">
                          {a.feature_value}
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              a.impact === 'INCREASES_RISK'
                                ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                                : a.impact === 'PROTECTIVE'
                                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                                : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                            }`}
                          >
                            {a.impact.replace('_', ' ')}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recommendations List */}
            <div className="space-y-3">
              <h4 className="text-xs font-black text-slate-900 dark:text-white uppercase tracking-wider">
                Actionable Clinical Recommendations
              </h4>
              <div className="space-y-2">
                {(activeModalDisease.recommendations || []).map((rec: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {rec.title}
                      </span>
                      <span className="text-[10px] font-semibold text-teal-600 bg-teal-50 dark:bg-teal-950/60 px-2 py-0.5 rounded-full">
                        Priority {rec.priority}
                      </span>
                    </div>
                    <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                      {rec.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Modal Close CTA */}
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setActiveModalDisease(null)}
                className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-950 text-xs font-bold"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
