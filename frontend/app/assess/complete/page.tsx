'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  Cpu,
  FileText,
  Heart,
  HeartPulse,
  HelpCircle,
  Info,
  Layers,
  Loader2,
  Microscope,
  Shield,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  TrendingUp,
  User,
  Zap,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';

// Realistic sample profiles for fast clinical demonstration
const SAMPLE_PRESETS: Record<string, { label: string; description: string; data: Record<string, any> }> = {
  healthy: {
    label: 'Healthy Reference Profile',
    description: 'Optimal vitals, active lifestyle, normal blood biomarkers',
    data: {
      age: 34,
      sex: 'female',
      bmi: 22.4,
      smoking_status: 'never',
      physical_activity: 'active',
      alcohol_consumption: 'none',
      work_type: 'private',
      residence_type: 'urban',
      ever_married: 1,
      // Vitals & History
      blood_pressure_systolic: 115,
      blood_pressure_diastolic: 75,
      heart_rate_resting: 68,
      max_heart_rate: 165,
      hypertension_flag: 0,
      diabetes_flag: 0,
      heart_disease_flag: 0,
      ckd_flag: 0,
      atrial_fibrillation_flag: 0,
      family_history_diabetes: 0,
      family_history_heart_disease: 0,
      family_history_hypertension: 0,
      family_history_asthma: 0,
      family_history_breast_cancer: 0,
      family_history_lung_cancer: 0,
      family_history_parkinsons: 0,
      // Labs
      glucose_level: 88,
      cholesterol_total: 175,
      blood_urea: 26,
      serum_creatinine: 0.9,
      sodium: 140,
      potassium: 4.2,
      hemoglobin: 14.2,
      packed_cell_volume: 42,
      white_blood_cell_count: 6800,
      red_blood_cell_count: 4.7,
      urine_albumin: 'normal',
      urine_sugar: 'normal',
      pus_cell: 'normal',
      bacteria_in_urine: 0,
      total_bilirubin: 0.7,
      direct_bilirubin: 0.18,
      alkaline_phosphatase: 165,
      alt: 22,
      ast: 24,
      total_proteins: 7.2,
      albumin: 4.4,
      albumin_globulin_ratio: 1.2,
      insulin_level: 65,
      skin_thickness: 18,
      diabetes_pedigree: 0.18,
      num_pregnancies: 0,
      // Signs & Symptoms
      chest_pain_type: 'typical_angina',
      resting_ecg: 'normal',
      exercise_induced_angina: 0,
      st_depression: 0.1,
      slope_peak_st: 'upsloping',
      num_major_vessels: 0,
      thalassemia_type: 'normal',
      fev1_fvc_ratio: 0.84,
      air_quality_index: 38,
      allergic_rhinitis_flag: 0,
      eczema_flag: 0,
      occupational_exposure: 'none',
      pet_exposure: 0,
      mold_exposure: 0,
      num_respiratory_infections_past_year: 0,
      pack_years: 0,
      years_since_quitting: 0,
      chronic_cough: 0,
      shortness_of_breath: 0,
      chest_pain: 0,
      hemoptysis: 0,
      weight_loss_unexplained: 0,
      fatigue: 0,
      wheezing: 0,
      radon_exposure: 'none',
      occupational_carcinogen_exposure: 0,
      copd_flag: 0,
      vocal_jitter_pct: 0.0035,
      vocal_shimmer_pct: 0.018,
      nhr: 0.015,
      hnr: 26.0,
      rpde: 0.38,
      dfa: 0.58,
      tremor_score: 0,
      rigidity_score: 0,
      bradykinesia_score: 0,
      pesticide_exposure: 0,
      head_injury_history: 0,
      radius_mean: 12.2,
      texture_mean: 16.5,
      perimeter_mean: 78.0,
      area_mean: 460.0,
      smoothness_mean: 0.088,
      compactness_mean: 0.075,
      concavity_mean: 0.045,
      symmetry_mean: 0.17,
      fractal_dimension_mean: 0.059,
      brca_mutation_known: 0,
      menopause_status: 'pre',
      hormone_therapy_history: 0,
      sodium_intake: 'moderate',
      stress_level: 'low',
      sleep_hours_per_night: 8,
      waist_circumference: 76,
    },
  },
  cardiometabolic: {
    label: 'Cardiometabolic Elevated Risk',
    description: 'Elevated blood pressure, fasting glucose, and lipid panel markers',
    data: {
      age: 58,
      sex: 'male',
      bmi: 32.4,
      smoking_status: 'former',
      physical_activity: 'sedentary',
      alcohol_consumption: 'moderate',
      work_type: 'private',
      residence_type: 'urban',
      ever_married: 1,
      // Vitals & History
      blood_pressure_systolic: 154,
      blood_pressure_diastolic: 96,
      heart_rate_resting: 84,
      max_heart_rate: 130,
      hypertension_flag: 1,
      diabetes_flag: 1,
      heart_disease_flag: 0,
      ckd_flag: 0,
      atrial_fibrillation_flag: 0,
      family_history_diabetes: 1,
      family_history_heart_disease: 1,
      family_history_hypertension: 1,
      family_history_asthma: 0,
      family_history_breast_cancer: 0,
      family_history_lung_cancer: 0,
      family_history_parkinsons: 0,
      // Labs
      glucose_level: 185,
      cholesterol_total: 265,
      blood_urea: 44,
      serum_creatinine: 1.35,
      sodium: 137,
      potassium: 4.6,
      hemoglobin: 13.8,
      packed_cell_volume: 40,
      white_blood_cell_count: 8200,
      red_blood_cell_count: 4.5,
      urine_albumin: 'abnormal',
      urine_sugar: 'abnormal',
      pus_cell: 'normal',
      bacteria_in_urine: 0,
      total_bilirubin: 0.9,
      direct_bilirubin: 0.22,
      alkaline_phosphatase: 195,
      alt: 38,
      ast: 35,
      total_proteins: 6.9,
      albumin: 4.0,
      albumin_globulin_ratio: 1.05,
      insulin_level: 195,
      skin_thickness: 32,
      diabetes_pedigree: 0.75,
      num_pregnancies: 0,
      // Signs & Symptoms
      chest_pain_type: 'asymptomatic',
      resting_ecg: 'st_t_abnormality',
      exercise_induced_angina: 1,
      st_depression: 1.8,
      slope_peak_st: 'flat',
      num_major_vessels: 1,
      thalassemia_type: 'reversible_defect',
      fev1_fvc_ratio: 0.79,
      air_quality_index: 65,
      allergic_rhinitis_flag: 0,
      eczema_flag: 0,
      occupational_exposure: 'none',
      pet_exposure: 0,
      mold_exposure: 0,
      num_respiratory_infections_past_year: 1,
      pack_years: 15,
      years_since_quitting: 6,
      chronic_cough: 0,
      shortness_of_breath: 1,
      chest_pain: 1,
      hemoptysis: 0,
      weight_loss_unexplained: 0,
      fatigue: 1,
      wheezing: 0,
      radon_exposure: 'low',
      occupational_carcinogen_exposure: 0,
      copd_flag: 0,
      vocal_jitter_pct: 0.0055,
      vocal_shimmer_pct: 0.024,
      nhr: 0.022,
      hnr: 22.0,
      rpde: 0.46,
      dfa: 0.65,
      tremor_score: 0,
      rigidity_score: 0,
      bradykinesia_score: 0,
      pesticide_exposure: 0,
      head_injury_history: 0,
      radius_mean: 13.5,
      texture_mean: 18.0,
      perimeter_mean: 87.0,
      area_mean: 550.0,
      smoothness_mean: 0.095,
      compactness_mean: 0.09,
      concavity_mean: 0.07,
      symmetry_mean: 0.18,
      fractal_dimension_mean: 0.062,
      brca_mutation_known: 0,
      menopause_status: 'post',
      hormone_therapy_history: 0,
      sodium_intake: 'high',
      stress_level: 'high',
      sleep_hours_per_night: 6,
      waist_circumference: 102,
    },
  },
};

export default function CompleteAssessmentPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [modelChoice, setModelChoice] = useState('tabicl');
  const [formData, setFormData] = useState<Record<string, any>>(SAMPLE_PRESETS.healthy.data);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalSteps = 5;

  const handleChange = (name: string, value: any, type: string) => {
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'numerical' ? (value === '' ? '' : Number(value)) : value,
    }));
  };

  const handleCheckbox = (name: string, checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      [name]: checked ? 1 : 0,
    }));
  };

  const loadPreset = (presetKey: string) => {
    if (SAMPLE_PRESETS[presetKey]) {
      setFormData(SAMPLE_PRESETS[presetKey].data);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        input_data: formData,
        model_name: modelChoice,
      };

      const res = await apiRequest('/api/v1/predictions/complete', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      // Redirect to combined results dashboard
      if (res.assessment_id) {
        router.push(`/results/combined/${res.assessment_id}`);
      } else {
        throw new Error('Assessment ID missing from response.');
      }
    } catch (err: any) {
      console.error('Failed complete assessment', err);
      setError(err.message || 'Complete assessment execution failed. Please verify your inputs.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto w-full space-y-8">
      {/* Top Breadcrumb & Presets Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <Link
          href="/assess"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-teal-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Assessment Center</span>
        </Link>

        {/* Quick presets */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-500 uppercase">Load Preset:</span>
          <button
            type="button"
            onClick={() => loadPreset('healthy')}
            className="px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100 transition-colors"
          >
            Healthy Reference
          </button>
          <button
            type="button"
            onClick={() => loadPreset('cardiometabolic')}
            className="px-3 py-1 rounded-lg text-xs font-semibold bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 hover:bg-rose-100 transition-colors"
          >
            Cardiometabolic Risk
          </button>
        </div>
      </div>

      {/* Main Title Banner */}
      <div className="rounded-3xl bg-gradient-to-tr from-slate-900 via-slate-900 to-teal-950 p-6 sm:p-8 text-white border border-slate-800 shadow-xl space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold border border-teal-500/30">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Mode A · Unified Multi-Disease Intake</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
          Complete Health Assessment (All 10 Diseases)
        </h1>
        <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
          Fill out this progressive intake form. Common physiological markers are entered only once; each disease model receives its own correctly mapped feature set via our clinical translation pipeline.
        </p>

        {/* Foundation Model Choice */}
        <div className="pt-3 flex flex-wrap items-center gap-3">
          <span className="text-xs font-semibold text-slate-300">Foundation Model Architecture:</span>
          <div className="inline-flex p-1 rounded-xl bg-slate-800/80 border border-slate-700">
            <button
              type="button"
              onClick={() => setModelChoice('tabicl')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                modelChoice === 'tabicl'
                  ? 'bg-teal-500 text-slate-950 shadow-sm'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              TabICLv2 2.2.0 (Recommended · Fast)
            </button>
            <button
              type="button"
              onClick={() => setModelChoice('tabpfn')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                modelChoice === 'tabpfn'
                  ? 'bg-teal-500 text-slate-950 shadow-sm'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              TabPFN 9.0.0 (In-Context Prior)
            </button>
          </div>
        </div>
      </div>

      {/* Step Progress Indicator */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="grid grid-cols-5 gap-2 text-center text-xs">
          {[
            { num: 1, label: 'Demographics & Lifestyle' },
            { num: 2, label: 'Vitals & History Flags' },
            { num: 3, label: 'Metabolic & Blood Labs' },
            { num: 4, label: 'Renal & Hepatic Panels' },
            { num: 5, label: 'Specialized Clinical Signs' },
          ].map((s) => (
            <button
              key={s.num}
              type="button"
              onClick={() => setCurrentStep(s.num)}
              className={`p-2 rounded-xl transition-all flex flex-col items-center gap-1 ${
                currentStep === s.num
                  ? 'bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 font-bold border border-teal-300 dark:border-teal-800'
                  : currentStep > s.num
                  ? 'text-emerald-600 dark:text-emerald-400 font-medium'
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                  currentStep === s.num
                    ? 'bg-teal-600 text-white font-bold'
                    : currentStep > s.num
                    ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                }`}
              >
                {currentStep > s.num ? '✓' : s.num}
              </div>
              <span className="hidden sm:inline text-[11px] truncate max-w-full">{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 flex items-start gap-3 text-xs sm:text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">Assessment Execution Notice</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Main Intake Form Form */}
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* STEP 1: Demographics & Lifestyle */}
        {currentStep === 1 && (
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
              <h2 className="text-xl font-black text-slate-900 dark:text-white">
                Step 1: Demographics & Lifestyle Parameters
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Foundational patient anthropometrics and lifestyle habits utilized across multiple models.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Age (Years) *
                </label>
                <input
                  type="number"
                  min="18"
                  max="100"
                  required
                  value={formData.age ?? 45}
                  onChange={(e) => handleChange('age', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Used in all 10 disease models</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Biological Sex *
                </label>
                <select
                  value={formData.sex ?? 'female'}
                  onChange={(e) => handleChange('sex', e.target.value, 'categorical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                >
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
                <span className="text-[11px] text-slate-400">Standard binary demographic mapping</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Body Mass Index (BMI, kg/m²) *
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="14"
                  max="60"
                  required
                  value={formData.bmi ?? 24.5}
                  onChange={(e) => handleChange('bmi', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Normal range: 18.5 – 24.9 kg/m²</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Smoking Status *
                </label>
                <select
                  value={formData.smoking_status ?? 'never'}
                  onChange={(e) => handleChange('smoking_status', e.target.value, 'categorical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                >
                  <option value="never">Never Smoked</option>
                  <option value="former">Former Smoker</option>
                  <option value="current">Current Smoker</option>
                  <option value="passive">Passive / Secondary Exposure</option>
                </select>
                <span className="text-[11px] text-slate-400">Mapped appropriately for Stroke, Heart, Lung, Asthma</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Physical Activity Level *
                </label>
                <select
                  value={formData.physical_activity ?? 'moderate'}
                  onChange={(e) => handleChange('physical_activity', e.target.value, 'categorical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                >
                  <option value="sedentary">Sedentary (Minimal activity)</option>
                  <option value="light">Light (1-2 days/week)</option>
                  <option value="moderate">Moderate (3-4 days/week)</option>
                  <option value="active">Active (5+ days/week)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Alcohol Consumption *
                </label>
                <select
                  value={formData.alcohol_consumption ?? 'none'}
                  onChange={(e) => handleChange('alcohol_consumption', e.target.value, 'categorical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                >
                  <option value="none">None (Non-drinker)</option>
                  <option value="light">Light (1-3 drinks/week)</option>
                  <option value="moderate">Moderate (4-7 drinks/week)</option>
                  <option value="heavy">Heavy (8+ drinks/week)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Work Type (Stroke feature)
                </label>
                <select
                  value={formData.work_type ?? 'private'}
                  onChange={(e) => handleChange('work_type', e.target.value, 'categorical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                >
                  <option value="private">Private Employment</option>
                  <option value="self_employed">Self Employed</option>
                  <option value="government">Government / Public</option>
                  <option value="never_worked">Never Worked</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Residence Type (Stroke feature)
                </label>
                <select
                  value={formData.residence_type ?? 'urban'}
                  onChange={(e) => handleChange('residence_type', e.target.value, 'categorical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                >
                  <option value="urban">Urban</option>
                  <option value="rural">Rural</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Waist Circumference (cm)
                </label>
                <input
                  type="number"
                  step="1"
                  min="50"
                  max="160"
                  value={formData.waist_circumference ?? 82}
                  onChange={(e) => handleChange('waist_circumference', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Hypertension metabolic risk factor</span>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: Vital Signs & Chronic History Flags */}
        {currentStep === 2 && (
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
              <h2 className="text-xl font-black text-slate-900 dark:text-white">
                Step 2: Vital Signs & Medical History
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Cardiovascular hemodynamics and known pre-existing clinical flags.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Systolic BP (mmHg) *
                </label>
                <input
                  type="number"
                  min="80"
                  max="240"
                  required
                  value={formData.blood_pressure_systolic ?? 120}
                  onChange={(e) => handleChange('blood_pressure_systolic', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Systolic reading</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Diastolic BP (mmHg) *
                </label>
                <input
                  type="number"
                  min="50"
                  max="140"
                  required
                  value={formData.blood_pressure_diastolic ?? 80}
                  onChange={(e) => handleChange('blood_pressure_diastolic', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Diastolic reading</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Resting Heart Rate (bpm)
                </label>
                <input
                  type="number"
                  min="40"
                  max="180"
                  value={formData.heart_rate_resting ?? 72}
                  onChange={(e) => handleChange('heart_rate_resting', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Max Heart Rate Achieved (bpm)
                </label>
                <input
                  type="number"
                  min="60"
                  max="220"
                  value={formData.max_heart_rate ?? 150}
                  onChange={(e) => handleChange('max_heart_rate', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Heart Disease model</span>
              </div>
            </div>

            {/* Pre-existing Diagnoses & Family History Flags */}
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-4">
              <h3 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wider">
                Personal Diagnoses & Family Medical History
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {[
                  { key: 'hypertension_flag', label: 'Diagnosed Hypertension' },
                  { key: 'diabetes_flag', label: 'Diagnosed Diabetes' },
                  { key: 'heart_disease_flag', label: 'Known Heart Disease' },
                  { key: 'atrial_fibrillation_flag', label: 'Atrial Fibrillation' },
                  { key: 'ckd_flag', label: 'Known Kidney Impairment' },
                  { key: 'family_history_diabetes', label: 'Family History: Diabetes' },
                  { key: 'family_history_heart_disease', label: 'Family History: Heart Disease' },
                  { key: 'family_history_hypertension', label: 'Family History: Hypertension' },
                  { key: 'family_history_asthma', label: 'Family History: Asthma' },
                  { key: 'family_history_breast_cancer', label: 'Family History: Breast Cancer' },
                  { key: 'family_history_lung_cancer', label: 'Family History: Lung Cancer' },
                  { key: 'family_history_parkinsons', label: 'Family History: Parkinson’s' },
                ].map((item) => (
                  <label
                    key={item.key}
                    className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={Boolean(formData[item.key])}
                      onChange={(e) => handleCheckbox(item.key, e.target.checked)}
                      className="w-4 h-4 rounded text-teal-600 focus:ring-teal-500"
                    />
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      {item.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Metabolic & Blood Biomarkers */}
        {currentStep === 3 && (
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
              <h2 className="text-xl font-black text-slate-900 dark:text-white">
                Step 3: Metabolic, Glycemic & Lipid Biomarkers
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Key laboratory blood test values for metabolic, endocrine, and lipid risk evaluation.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Fasting Glucose (mg/dL) *
                </label>
                <input
                  type="number"
                  min="40"
                  max="350"
                  required
                  value={formData.glucose_level ?? 95}
                  onChange={(e) => handleChange('glucose_level', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Normal fasting: 70–99 mg/dL</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Total Cholesterol (mg/dL) *
                </label>
                <input
                  type="number"
                  min="100"
                  max="450"
                  required
                  value={formData.cholesterol_total ?? 190}
                  onChange={(e) => handleChange('cholesterol_total', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Desirable: &lt; 200 mg/dL</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Fasting Serum Insulin (μU/mL)
                </label>
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={formData.insulin_level ?? 75}
                  onChange={(e) => handleChange('insulin_level', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400">Normal: 15–120 μU/mL</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Triceps Skin Thickness (mm)
                </label>
                <input
                  type="number"
                  min="5"
                  max="60"
                  value={formData.skin_thickness ?? 20}
                  onChange={(e) => handleChange('skin_thickness', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Diabetes Pedigree Score
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.05"
                  max="2.5"
                  value={formData.diabetes_pedigree ?? 0.35}
                  onChange={(e) => handleChange('diabetes_pedigree', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Number of Pregnancies
                </label>
                <input
                  type="number"
                  min="0"
                  max="15"
                  value={formData.num_pregnancies ?? 0}
                  onChange={(e) => handleChange('num_pregnancies', e.target.value, 'numerical')}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium focus:ring-2 focus:ring-teal-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: Renal & Hepatic Panels */}
        {currentStep === 4 && (
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
              <h2 className="text-xl font-black text-slate-900 dark:text-white">
                Step 4: Renal Function & Liver Enzyme Panels
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Biomarkers specific to Chronic Kidney Disease (CKD) and Hepatic assessments.
              </p>
            </div>

            <div className="space-y-4">
              <h3 className="text-xs font-black text-teal-600 dark:text-teal-400 uppercase tracking-wider">
                Renal Panel (Kidney Disease)
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Serum Creatinine (mg/dL) *
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.3"
                    max="15.0"
                    required
                    value={formData.serum_creatinine ?? 1.05}
                    onChange={(e) => handleChange('serum_creatinine', e.target.value, 'numerical')}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
                  />
                  <span className="text-[11px] text-slate-400">Normal: 0.7–1.3 mg/dL</span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Blood Urea (mg/dL) *
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="150"
                    required
                    value={formData.blood_urea ?? 32}
                    onChange={(e) => handleChange('blood_urea', e.target.value, 'numerical')}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
                  />
                  <span className="text-[11px] text-slate-400">Normal: 15–40 mg/dL</span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Hemoglobin (g/dL) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="5"
                    max="20"
                    required
                    value={formData.hemoglobin ?? 14.5}
                    onChange={(e) => handleChange('hemoglobin', e.target.value, 'numerical')}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Urine Albumin
                  </label>
                  <select
                    value={formData.urine_albumin ?? 'normal'}
                    onChange={(e) => handleChange('urine_albumin', e.target.value, 'categorical')}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
                  >
                    <option value="normal">Normal</option>
                    <option value="abnormal">Abnormal / Microalbuminuria</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-4">
              <h3 className="text-xs font-black text-teal-600 dark:text-teal-400 uppercase tracking-wider">
                Hepatic Panel (Liver Disease)
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Total Bilirubin (mg/dL) *
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.2"
                    max="10.0"
                    required
                    value={formData.total_bilirubin ?? 0.85}
                    onChange={(e) => handleChange('total_bilirubin', e.target.value, 'numerical')}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    ALT / SGPT (IU/L) *
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="300"
                    required
                    value={formData.alt ?? 26}
                    onChange={(e) => handleChange('alt', e.target.value, 'numerical')}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    AST / SGOT (IU/L) *
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="300"
                    required
                    value={formData.ast ?? 28}
                    onChange={(e) => handleChange('ast', e.target.value, 'numerical')}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Serum Albumin (g/dL) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="1.5"
                    max="6.5"
                    required
                    value={formData.albumin ?? 4.2}
                    onChange={(e) => handleChange('albumin', e.target.value, 'numerical')}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 5: Specialized Clinical & Imaging Findings */}
        {currentStep === 5 && (
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
              <h2 className="text-xl font-black text-slate-900 dark:text-white">
                Step 5: Specialized Clinical & Imaging Signs
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Targeted markers for respiratory, neurological (Parkinson's), and oncology (cancers). Default baseline values provided.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Respiratory & Asthma */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-3">
                <h3 className="text-xs font-black text-slate-900 dark:text-white uppercase flex items-center gap-1.5">
                  <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
                  Pulmonary & Respiratory
                </h3>

                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">
                    FEV1/FVC Ratio (Spirometry)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.4"
                    max="1.0"
                    value={formData.fev1_fvc_ratio ?? 0.82}
                    onChange={(e) => handleChange('fev1_fvc_ratio', e.target.value, 'numerical')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  />
                  <span className="text-[10px] text-slate-400">Normal: &gt; 0.75</span>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">
                    Air Quality Index (AQI exposure)
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="300"
                    value={formData.air_quality_index ?? 45}
                    onChange={(e) => handleChange('air_quality_index', e.target.value, 'numerical')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  />
                </div>

                <div className="space-y-2 pt-1">
                  {[
                    { key: 'chronic_cough', label: 'Persistent Chronic Cough' },
                    { key: 'shortness_of_breath', label: 'Dyspnea / Shortness of Breath' },
                    { key: 'wheezing', label: 'Audible Wheezing' },
                  ].map((f) => (
                    <label key={f.key} className="flex items-center gap-2 cursor-pointer text-xs">
                      <input
                        type="checkbox"
                        checked={Boolean(formData[f.key])}
                        onChange={(e) => handleCheckbox(f.key, e.target.checked)}
                        className="w-3.5 h-3.5 rounded text-teal-600"
                      />
                      <span className="text-slate-700 dark:text-slate-300">{f.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Neurological & Parkinson's */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-3">
                <h3 className="text-xs font-black text-slate-900 dark:text-white uppercase flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5 text-violet-600" />
                  Neurological (Parkinson’s)
                </h3>

                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">
                    Vocal Jitter % (Acoustic measurement)
                  </label>
                  <input
                    type="number"
                    step="0.0005"
                    min="0.001"
                    max="0.05"
                    value={formData.vocal_jitter_pct ?? 0.0055}
                    onChange={(e) => handleChange('vocal_jitter_pct', e.target.value, 'numerical')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">
                    Resting Tremor Rating (0 - 4)
                  </label>
                  <select
                    value={formData.tremor_score ?? 0}
                    onChange={(e) => handleChange('tremor_score', e.target.value, 'numerical')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  >
                    <option value="0">0 - None / Normal</option>
                    <option value="1">1 - Slight / Infrequent</option>
                    <option value="2">2 - Moderate</option>
                    <option value="3">3 - Marked / Severe</option>
                  </select>
                </div>

                <div className="space-y-2 pt-1">
                  {[
                    { key: 'pesticide_exposure', label: 'Occupational Pesticide Exposure' },
                    { key: 'head_injury_history', label: 'Significant Head Trauma History' },
                  ].map((f) => (
                    <label key={f.key} className="flex items-center gap-2 cursor-pointer text-xs">
                      <input
                        type="checkbox"
                        checked={Boolean(formData[f.key])}
                        onChange={(e) => handleCheckbox(f.key, e.target.checked)}
                        className="w-3.5 h-3.5 rounded text-violet-600"
                      />
                      <span className="text-slate-700 dark:text-slate-300">{f.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Oncology & Breast Imaging */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-3">
                <h3 className="text-xs font-black text-slate-900 dark:text-white uppercase flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-pink-600" />
                  Tissue Imaging & Oncology
                </h3>

                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">
                    Mean Cell Radius (mm)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="8"
                    max="30"
                    value={formData.radius_mean ?? 13.5}
                    onChange={(e) => handleChange('radius_mean', e.target.value, 'numerical')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1">
                    Menopause Status
                  </label>
                  <select
                    value={formData.menopause_status ?? 'pre'}
                    onChange={(e) => handleChange('menopause_status', e.target.value, 'categorical')}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs"
                  >
                    <option value="pre">Pre-menopausal</option>
                    <option value="peri">Peri-menopausal</option>
                    <option value="post">Post-menopausal</option>
                  </select>
                </div>

                <div className="space-y-2 pt-1">
                  {[
                    { key: 'brca_mutation_known', label: 'Known BRCA 1/2 Genetic Mutation' },
                    { key: 'hormone_therapy_history', label: 'Hormone Replacement Therapy' },
                  ].map((f) => (
                    <label key={f.key} className="flex items-center gap-2 cursor-pointer text-xs">
                      <input
                        type="checkbox"
                        checked={Boolean(formData[f.key])}
                        onChange={(e) => handleCheckbox(f.key, e.target.checked)}
                        className="w-3.5 h-3.5 rounded text-pink-600"
                      />
                      <span className="text-slate-700 dark:text-slate-300">{f.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Stepper Navigation Buttons */}
        <div className="flex items-center justify-between pt-4">
          <button
            type="button"
            disabled={currentStep === 1 || isSubmitting}
            onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
            className="px-5 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 disabled:opacity-40 transition-all flex items-center gap-1.5"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Previous Step</span>
          </button>

          <div className="flex items-center gap-3">
            {currentStep < totalSteps ? (
              <button
                type="button"
                onClick={() => setCurrentStep((prev) => Math.min(totalSteps, prev + 1))}
                className="px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-950 text-xs font-bold transition-all flex items-center gap-1.5 shadow-md"
              >
                <span>Continue to Step {currentStep + 1}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-8 py-3.5 rounded-2xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs sm:text-sm font-black transition-all flex items-center gap-2 shadow-lg shadow-teal-500/30 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Executing 10 Foundation Models...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Submit & Run Complete 10-Disease Assessment</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
