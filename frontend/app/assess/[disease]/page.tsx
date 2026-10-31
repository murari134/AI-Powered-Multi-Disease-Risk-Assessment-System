'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronRight,
  Cpu,
  FileText,
  HelpCircle,
  Info,
  Loader2,
  Sparkles,
  Stethoscope,
  TrendingUp,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';
import { getRiskColor } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

interface FeatureSpec {
  name: string;
  type: 'numerical' | 'categorical' | 'binary';
  unit?: string;
  domain?: any[];
  description?: string;
  missing_allowed?: boolean;
}

interface DiseaseSpec {
  disease_id: string;
  name: string;
  target: {
    column: string;
    positive_class?: { meaning: string };
    negative_class?: { meaning: string };
  };
  features: FeatureSpec[];
  disclaimer: string;
}

const SAMPLE_PROFILES: Record<string, { low: Record<string, any>; high: Record<string, any> }> = {
  diabetes: {
    low: {
      age: 28,
      bmi: 22.4,
      glucose_level: 88,
      blood_pressure_systolic: 115,
      blood_pressure_diastolic: 75,
      insulin_level: 60,
      skin_thickness: 18,
      diabetes_pedigree: 0.15,
      num_pregnancies: 0,
      sex: 'female',
      smoking_status: 'never',
      physical_activity: 'active',
      family_history_diabetes: 0,
      hypertension_flag: 0,
    },
    high: {
      age: 58,
      bmi: 34.8,
      glucose_level: 195,
      blood_pressure_systolic: 155,
      blood_pressure_diastolic: 95,
      insulin_level: 210,
      skin_thickness: 35,
      diabetes_pedigree: 0.85,
      num_pregnancies: 3,
      sex: 'female',
      smoking_status: 'current',
      physical_activity: 'sedentary',
      family_history_diabetes: 1,
      hypertension_flag: 1,
    },
  },
  heart_disease: {
    low: {
      age: 32,
      sex: 'female',
      chest_pain_type: 'typical_angina',
      resting_blood_pressure: 118,
      cholesterol: 180,
      fasting_blood_sugar: 0,
      resting_ecg: 'normal',
      max_heart_rate: 165,
      exercise_angina: 0,
      st_depression: 0.2,
      st_slope: 'upsloping',
      num_major_vessels: 0,
      thalassemia: 'normal',
      bmi: 23.1,
      smoking_status: 'never',
      family_history_heart_disease: 0,
    },
    high: {
      age: 64,
      sex: 'male',
      chest_pain_type: 'asymptomatic',
      resting_blood_pressure: 160,
      cholesterol: 290,
      fasting_blood_sugar: 1,
      resting_ecg: 'st_t_wave_abnormality',
      max_heart_rate: 115,
      exercise_angina: 1,
      st_depression: 2.8,
      st_slope: 'flat',
      num_major_vessels: 2,
      thalassemia: 'reversible_defect',
      bmi: 32.6,
      smoking_status: 'current',
      family_history_heart_disease: 1,
    },
  },
  stroke: {
    low: {
      age: 30,
      sex: 'male',
      hypertension: 0,
      heart_disease: 0,
      ever_married: 'yes',
      work_type: 'private',
      residence_type: 'urban',
      avg_glucose_level: 85.0,
      bmi: 23.5,
      smoking_status: 'never',
      physical_activity: 'moderate',
      family_history_stroke: 0,
      alcohol_intake: 'never',
    },
    high: {
      age: 72,
      sex: 'male',
      hypertension: 1,
      heart_disease: 1,
      ever_married: 'yes',
      work_type: 'self_employed',
      residence_type: 'urban',
      avg_glucose_level: 215.0,
      bmi: 33.2,
      smoking_status: 'current',
      physical_activity: 'sedentary',
      family_history_stroke: 1,
      alcohol_intake: 'frequent',
    },
  },
  hypertension: {
    low: {
      age: 26,
      sex: 'female',
      systolic_bp: 112,
      diastolic_bp: 74,
      bmi: 21.8,
      resting_heart_rate: 68,
      cholesterol_total: 175,
      sodium_intake_estimate: 1800,
      physical_activity_hours: 4.5,
      smoking_status: 'never',
      alcohol_consumption: 'none',
      family_history_hypertension: 0,
      diabetes_diagnosed: 0,
      sleep_hours_per_night: 8,
      stress_level_reported: 'low',
    },
    high: {
      age: 59,
      sex: 'male',
      systolic_bp: 162,
      diastolic_bp: 102,
      bmi: 33.5,
      resting_heart_rate: 88,
      cholesterol_total: 265,
      sodium_intake_estimate: 4200,
      physical_activity_hours: 0.5,
      smoking_status: 'current',
      alcohol_consumption: 'heavy',
      family_history_hypertension: 1,
      diabetes_diagnosed: 1,
      sleep_hours_per_night: 5,
      stress_level_reported: 'high',
    },
  },
};

export default function AssessPage({ params }: { params: Promise<{ disease: string }> }) {
  const resolvedParams = use(params);
  const diseaseId = resolvedParams.disease;
  const router = useRouter();

  const [spec, setSpec] = useState<DiseaseSpec | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [modelChoice, setModelChoice] = useState<'tabicl' | 'tabpfn'>('tabicl');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);

  useEffect(() => {
    async function fetchSpec() {
      try {
        const data = await apiRequest<DiseaseSpec>(`/api/v1/diseases/${diseaseId}`);
        setSpec(data);

        // Initialize default form fields
        const initial: Record<string, any> = {};
        for (const feat of data.features) {
          if (feat.type === 'binary') {
            initial[feat.name] = 0;
          } else if (feat.type === 'categorical') {
            initial[feat.name] = feat.domain && feat.domain[0] ? feat.domain[0] : '';
          } else {
            // Pick midpoint or domain default
            if (feat.domain && Array.isArray(feat.domain) && feat.domain.length === 2) {
              const [min, max] = feat.domain;
              initial[feat.name] = Math.round((min + max) / 2);
            } else {
              initial[feat.name] = 0;
            }
          }
        }
        setFormData(initial);
      } catch (err: any) {
        setError(err.message || 'Failed to load disease specification.');
      } finally {
        setIsLoading(false);
      }
    }
    fetchSpec();
  }, [diseaseId]);

  const handleChange = (name: string, value: any, type: string) => {
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'numerical' ? (value === '' ? '' : Number(value)) : value,
    }));
  };

  const loadSample = (type: 'low' | 'high') => {
    if (SAMPLE_PROFILES[diseaseId] && SAMPLE_PROFILES[diseaseId][type]) {
      setFormData((prev) => ({ ...prev, ...SAMPLE_PROFILES[diseaseId][type] }));
    } else {
      // General heuristic sample
      if (!spec) return;
      const sample: Record<string, any> = {};
      spec.features.forEach((f) => {
        if (f.type === 'numerical' && f.domain) {
          const [min, max] = f.domain;
          sample[f.name] = type === 'low' ? min + (max - min) * 0.25 : min + (max - min) * 0.75;
        } else if (f.type === 'binary') {
          sample[f.name] = type === 'low' ? 0 : 1;
        } else if (f.type === 'categorical' && f.domain) {
          sample[f.name] = type === 'low' ? f.domain[0] : f.domain[f.domain.length - 1];
        }
      });
      setFormData((prev) => ({ ...prev, ...sample }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        disease_id: diseaseId,
        input_data: formData,
        model_name: modelChoice,
      };

      const res = await apiRequest('/api/v1/predictions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setResult(res);
      // Scroll to result
      window.scrollTo({ top: 400, behavior: 'smooth' });
    } catch (err: any) {
      setError(err.message || 'Prediction execution failed. Check inputs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin" />
        <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
          Loading clinical feature schema for {diseaseId}...
        </p>
      </div>
    );
  }

  if (error && !spec) {
    return (
      <div className="max-w-xl mx-auto my-16 p-8 rounded-2xl bg-rose-50 border border-rose-200 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-600 mx-auto" />
        <h2 className="text-xl font-bold text-rose-900">Module Load Error</h2>
        <p className="text-sm text-rose-700">{error}</p>
        <Link href="/" className="inline-block px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-semibold">
          Return to Overview
        </Link>
      </div>
    );
  }

  const riskColors = result ? getRiskColor(result.risk_level) : null;

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto w-full">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-teal-600 dark:text-slate-400 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Disease Portfolio
      </Link>

      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-6 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300">
              Module: {spec?.disease_id.toUpperCase()}
            </span>
            <span className="text-xs text-slate-500">Schema v1.0.0</span>
          </div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white mt-1">
            {spec?.name} Risk Assessment
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
            Fill in the patient clinical and lifestyle parameters. Fields adhere to verified YAML data-quality bounds.
          </p>
        </div>

        {/* Sample Profile Loaders */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => loadSample('low')}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100 transition-colors"
          >
            Sample: Low Risk
          </button>
          <button
            type="button"
            onClick={() => loadSample('high')}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-rose-700 bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 hover:bg-rose-100 transition-colors"
          >
            Sample: Elevated Risk
          </button>
        </div>
      </div>

      {/* Result Card if available */}
      {result && riskColors && (
        <div className={`mb-10 rounded-2xl border ${riskColors.border} ${riskColors.bg} p-6 sm:p-8 shadow-xl animate-in zoom-in-95 duration-200`}>
          <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-200/60 dark:border-slate-800/60 gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-extrabold px-3 py-1 rounded-full uppercase tracking-wider ${riskColors.badge}`}>
                  {result.risk_level} RISK CATEGORY
                </span>
                <span className="text-xs text-slate-500">
                  Model: {result.model_name} {result.model_version} • Latency {result.inference_latency_ms}ms
                </span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white">
                Calculated Risk Score: {result.risk_percentage}%
              </h2>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                Raw model probability: {result.raw_probability} (Calibrated: {result.calibrated_probability})
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href={`/results/${result.prediction_id}`}
                className="px-5 py-2.5 rounded-xl font-bold text-xs bg-slate-900 text-white dark:bg-white dark:text-slate-950 shadow-md flex items-center gap-1.5 hover:scale-105 transition-all"
              >
                <span>Full Clinical PDF & Analysis</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
              <Link
                href={`/hospitals?specialty=${diseaseId}`}
                className="px-4 py-2.5 rounded-xl font-semibold text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 hover:bg-slate-50 transition-colors"
              >
                Find Specialist
              </Link>
            </div>
          </div>

          {/* Attributions & Recommendations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {/* Top Contributing Features */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 mb-3 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-teal-600" />
                Key Contributing Factors (Feature Attributions)
              </h4>
              <div className="space-y-2">
                {result.attributions?.slice(0, 4).map((a: any, i: number) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-white/80 dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-bold text-slate-800 dark:text-slate-200">{a.feature_label}</span>
                      <span className="text-slate-500 ml-2">({a.feature_value})</span>
                    </div>
                    <span
                      className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                        a.impact === 'INCREASES_RISK'
                          ? 'bg-rose-100 text-rose-800'
                          : a.impact === 'PROTECTIVE'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {a.impact === 'INCREASES_RISK' ? '+ Risk Factor' : a.impact === 'PROTECTIVE' ? '- Protective' : 'Baseline'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendations */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 mb-3 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-teal-600" />
                Actionable Clinical Prototype Guidance
              </h4>
              <div className="space-y-2">
                {result.recommendations?.slice(0, 3).map((r: any, i: number) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-white/80 dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800 space-y-1 text-xs"
                  >
                    <p className="font-bold text-slate-800 dark:text-slate-200">{r.title}</p>
                    <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">{r.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Model Architecture Selection */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-teal-600" />
              Tabular Foundation Model Engine
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Select which verified foundation architecture executes in-context inference
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 max-w-xs">
            <button
              type="button"
              onClick={() => setModelChoice('tabicl')}
              className={`px-3 py-2 rounded-xl text-xs font-bold transition-all border ${
                modelChoice === 'tabicl'
                  ? 'bg-teal-50 dark:bg-teal-950 border-teal-500 text-teal-700 dark:text-teal-300 shadow-sm'
                  : 'border-slate-200 dark:border-slate-800 text-slate-600 hover:bg-slate-50'
              }`}
            >
              TabICLv2 2.2.0 (Fast)
            </button>
            <button
              type="button"
              onClick={() => setModelChoice('tabpfn')}
              className={`px-3 py-2 rounded-xl text-xs font-bold transition-all border ${
                modelChoice === 'tabpfn'
                  ? 'bg-cyan-50 dark:bg-cyan-950 border-cyan-500 text-cyan-700 dark:text-cyan-300 shadow-sm'
                  : 'border-slate-200 dark:border-slate-800 text-slate-600 hover:bg-slate-50'
              }`}
            >
              TabPFN 9.0.0
            </button>
          </div>
        </div>

        {/* Feature Input Fields Grid */}
        <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Clinical & Demographic Variables ({spec?.features.length} Parameters)
            </h3>
            <span className="text-xs text-slate-400">All inputs validated against specification bounds</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {spec?.features.map((feat) => {
              const val = formData[feat.name];
              const isNum = feat.type === 'numerical';
              const isBin = feat.type === 'binary';
              const isCat = feat.type === 'categorical';

              return (
                <div key={feat.name} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                      <span>{feat.name.replace(/_/g, ' ').toUpperCase()}</span>
                      {feat.unit && (
                        <span className="text-[10px] text-teal-600 dark:text-teal-400 font-semibold lowercase">
                          ({feat.unit})
                        </span>
                      )}
                    </label>
                    {feat.domain && Array.isArray(feat.domain) && (
                      <span className="text-[10px] text-slate-400">
                        {isNum ? `${feat.domain[0]}–${feat.domain[1]}` : ''}
                      </span>
                    )}
                  </div>

                  {/* Input Element based on type */}
                  {isNum ? (
                    <input
                      type="number"
                      step="any"
                      min={feat.domain ? feat.domain[0] : undefined}
                      max={feat.domain ? feat.domain[1] : undefined}
                      required={!feat.missing_allowed}
                      value={val !== undefined ? val : ''}
                      onChange={(e) => handleChange(feat.name, e.target.value, 'numerical')}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40"
                    />
                  ) : isBin ? (
                    <select
                      value={val !== undefined ? val : 0}
                      onChange={(e) => handleChange(feat.name, Number(e.target.value), 'binary')}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40"
                    >
                      <option value={0}>0 — Absent / Normal / No</option>
                      <option value={1}>1 — Present / Diagnosed / Yes</option>
                    </select>
                  ) : isCat && feat.domain ? (
                    <select
                      value={val || ''}
                      onChange={(e) => handleChange(feat.name, e.target.value, 'categorical')}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40"
                    >
                      {feat.domain.map((opt: string) => (
                        <option key={opt} value={opt}>
                          {opt.replace(/_/g, ' ').toUpperCase()}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={val || ''}
                      onChange={(e) => handleChange(feat.name, e.target.value, 'text')}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/40"
                    />
                  )}

                  {feat.description && (
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 line-clamp-1">
                      {feat.description}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Disclaimer & Submit */}
        <div className="p-5 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-900 dark:text-amber-300 leading-relaxed">
            By clicking &quot;Compute Risk Assessment&quot;, you acknowledge this computational execution is an educational research
            prototype utilizing tabular foundation models. The outputs do not replace clinical physician consultation.
          </p>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-4 px-6 rounded-2xl font-bold text-base text-white bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 shadow-xl shadow-teal-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Executing {modelChoice.toUpperCase()} In-Context Inference...</span>
            </>
          ) : (
            <>
              <Stethoscope className="w-5 h-5" />
              <span>Compute {spec?.name} Risk Assessment</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
