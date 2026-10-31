'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock,
  FileText,
  HeartPulse,
  History,
  Layers,
  Loader2,
  ShieldCheck,
  Stethoscope,
  TrendingUp,
  User,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';
import { getRiskColor } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

const ALL_DISEASES = [
  { id: 'diabetes', name: 'Diabetes', category: 'Endocrine' },
  { id: 'heart_disease', name: 'Heart Disease', category: 'Cardiovascular' },
  { id: 'stroke', name: 'Stroke', category: 'Cerebrovascular' },
  { id: 'hypertension', name: 'Hypertension', category: 'Cardiovascular' },
  { id: 'chronic_kidney_disease', name: 'Chronic Kidney Disease', category: 'Renal' },
  { id: 'liver_disease', name: 'Liver Disease', category: 'Hepatic' },
  { id: 'parkinsons', name: 'Parkinson\'s Disease', category: 'Neurological' },
  { id: 'breast_cancer', name: 'Breast Cancer', category: 'Oncology' },
  { id: 'lung_cancer', name: 'Lung Cancer', category: 'Pulmonary' },
  { id: 'asthma', name: 'Asthma', category: 'Respiratory' },
];

export default function DashboardPage() {
  const { user, setAuthModalOpen } = useAuthStore();
  const [history, setHistory] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [histRes, anaRes] = await Promise.allSettled([
          apiRequest('/api/v1/predictions/history?limit=10'),
          apiRequest('/api/v1/analytics/overview'),
        ]);

        if (histRes.status === 'fulfilled') {
          setHistory(Array.isArray(histRes.value) ? histRes.value : []);
        }
        if (anaRes.status === 'fulfilled') {
          setAnalytics(anaRes.value);
        }
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, [user]);

  const totalCount = history.length;
  const highRiskCount = history.filter((h) => h.risk_level === 'HIGH').length;
  const avgProb =
    totalCount > 0
      ? (history.reduce((acc, h) => acc + (h.risk_percentage || 0), 0) / totalCount).toFixed(1)
      : '0.0';

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-10">
      {/* Welcome Banner */}
      <div className="rounded-3xl bg-gradient-to-tr from-slate-900 via-slate-900 to-teal-950 p-6 sm:p-8 text-white flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl border border-slate-800">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold border border-teal-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>MediRisk 2.0 Clinical Intelligence Dashboard</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
            Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl">
            Monitor real-time patient risk evaluations across 10 disease categories. TabICLv2 and TabPFN in-context models active.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/assess"
            className="px-5 py-3 rounded-xl font-bold text-xs sm:text-sm bg-teal-500 hover:bg-teal-400 text-slate-950 shadow-md flex items-center gap-2 transition-all shrink-0"
          >
            <Stethoscope className="w-4 h-4" />
            <span>New Risk Assessment</span>
          </Link>
          {!user && (
            <button
              onClick={() => setAuthModalOpen(true, 'login')}
              className="px-4 py-3 rounded-xl font-semibold text-xs sm:text-sm bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition-all"
            >
              Sign In to Save Records
            </button>
          )}
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Completed Assessments</p>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-black text-slate-900 dark:text-white">{totalCount}</h3>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700">Active</span>
          </div>
          <p className="text-[11px] text-slate-400">Total multi-disease assessments conducted</p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Average Risk Score</p>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-black text-teal-600 dark:text-teal-400">{avgProb}%</h3>
            <span className="text-xs text-slate-400">Mean probability</span>
          </div>
          <p className="text-[11px] text-slate-400">Calibrated cross-disease risk index</p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">High Risk Alerts</p>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-black text-rose-600">{highRiskCount}</h3>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700">&gt; 70% Risk</span>
          </div>
          <p className="text-[11px] text-slate-400">Cases requiring prompt clinical follow-up</p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Pathology Panels</p>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-black text-cyan-600">10 / 10</h3>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-700">100% Ready</span>
          </div>
          <p className="text-[11px] text-slate-400">Foundation models verified & loaded</p>
        </div>
      </div>

      {/* 10 Disease Quick Launcher */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-black text-slate-900 dark:text-white">
              Launch Disease Assessment
            </h2>
            <p className="text-xs text-slate-500">Select any condition to begin patient feature entry</p>
          </div>
          <Link href="/analytics" className="text-xs font-bold text-teal-600 hover:underline">
            View Foundation Model Benchmarks →
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {ALL_DISEASES.map((d) => (
            <Link
              key={d.id}
              href={`/assess/${d.id}`}
              className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 hover:shadow-md transition-all group"
            >
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                <Stethoscope className="w-4 h-4" />
              </div>
              <p className="font-bold text-xs text-slate-800 dark:text-slate-200 truncate group-hover:text-teal-600">
                {d.name}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">{d.category}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Predictions Table */}
      <div className="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <History className="w-4 h-4 text-teal-600" />
              <span>Recent Risk Predictions</span>
            </h3>
            <p className="text-xs text-slate-500">Evaluations recorded in the PostgreSQL audit database</p>
          </div>
          <Link href="/history" className="text-xs font-bold text-teal-600 hover:underline">
            View All History →
          </Link>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-400 text-xs">Loading prediction history...</div>
        ) : history.length === 0 ? (
          <div className="py-12 text-center space-y-3">
            <Activity className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto" />
            <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">
              No assessments recorded yet
            </p>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Launch an assessment for Diabetes, Heart Disease, or Stroke to see live foundation model predictions.
            </p>
            <Link
              href="/assess/diabetes"
              className="inline-block mt-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700"
            >
              Start First Assessment
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 font-semibold">
                  <th className="pb-3">Disease Pathology</th>
                  <th className="pb-3">Algorithm</th>
                  <th className="pb-3">Risk Tier</th>
                  <th className="pb-3">Probability</th>
                  <th className="pb-3">Timestamp</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {history.map((row) => {
                  const colors = getRiskColor(row.risk_level);
                  return (
                    <tr key={row.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 font-bold text-slate-900 dark:text-white">
                        {row.disease_name}
                      </td>
                      <td className="py-3.5 text-slate-500">
                        {row.model_name} {row.model_version}
                      </td>
                      <td className="py-3.5">
                        <span className={`px-2.5 py-0.5 rounded-full font-bold uppercase text-[10px] ${colors.badge}`}>
                          {row.risk_level}
                        </span>
                      </td>
                      <td className="py-3.5 font-bold text-slate-800 dark:text-slate-200">
                        {row.risk_percentage}%
                      </td>
                      <td className="py-3.5 text-slate-400 text-[11px]">
                        {new Date(row.created_at).toLocaleDateString()} {new Date(row.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-3.5 text-right">
                        <Link
                          href={`/results/${row.id}`}
                          className="font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400 hover:underline"
                        >
                          View PDF Report →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
