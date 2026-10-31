'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertTriangle,
  Award,
  BarChart3,
  Cpu,
  Layers,
  Loader2,
  TrendingUp,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiRequest } from '@/lib/api';

const ResponsiveBarChart = BarChart as any;
const ResponsivePieChart = PieChart as any;

const RISK_COLORS = ['#10b981', '#f59e0b', '#f43f5e'];

export default function AnalyticsPage() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const res = await apiRequest('/api/v1/analytics/overview');
        setData(res);
      } catch (err) {
        console.error('Failed to load analytics', err);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-16 space-y-3">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin" />
        <p className="text-sm font-semibold text-slate-500">Aggregating Phase 7B benchmarks and analytics...</p>
      </div>
    );
  }

  // Prepare benchmark chart data comparing TabPFN vs TabICL ROC-AUC
  const benchmarksByDisease: Record<string, { disease: string; tabpfn_auc?: number; tabicl_auc?: number }> = {};
  if (data?.benchmark_summary) {
    for (const b of data.benchmark_summary) {
      const dName = b.disease.replace(/_/g, ' ').replace('chronic kidney disease', 'CKD');
      if (!benchmarksByDisease[dName]) {
        benchmarksByDisease[dName] = { disease: dName };
      }
      if (b.model.toLowerCase().includes('tabpfn')) {
        benchmarksByDisease[dName].tabpfn_auc = Number((b.roc_auc || 0).toFixed(4));
      } else if (b.model.toLowerCase().includes('tabicl')) {
        benchmarksByDisease[dName].tabicl_auc = Number((b.roc_auc || 0).toFixed(4));
      }
    }
  }
  const benchmarkChartData = Object.values(benchmarksByDisease);

  // Risk distribution pie data
  const pieData = data?.risk_tier_distribution
    ? [
        { name: 'Low Risk (<30%)', value: data.risk_tier_distribution.LOW || 0 },
        { name: 'Moderate Risk (30-70%)', value: data.risk_tier_distribution.MODERATE || 0 },
        { name: 'High Risk (>70%)', value: data.risk_tier_distribution.HIGH || 0 },
      ].filter((p) => p.value > 0)
    : [];

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-10">
      {/* Page Title */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300 text-xs font-bold uppercase mb-2">
            Clinical AI Analytics
          </div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white">
            Pathology Statistics & Benchmark Comparison
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Empirical validation results across 10 disease categories and in-context tabular foundation models.
          </p>
        </div>

        <Link
          href="/assess/diabetes"
          className="px-4 py-2.5 rounded-xl font-bold text-xs bg-teal-600 hover:bg-teal-700 text-white shadow-sm self-start sm:self-auto"
        >
          Launch New Evaluation
        </Link>
      </div>

      {/* Main Benchmark Chart */}
      <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 gap-2">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-teal-600" />
              <span>Phase 7B Foundation Model Benchmark Comparison (ROC-AUC)</span>
            </h3>
            <p className="text-xs text-slate-500">
              Direct comparison between TabICLv2 2.2.0 and TabPFN 9.0.0 on validation cohorts (No winner declared).
            </p>
          </div>
          <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
            Validation Split (15%)
          </span>
        </div>

        <div className="h-80 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ResponsiveBarChart data={benchmarkChartData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
              <XAxis dataKey="disease" tick={{ fontSize: 11 }} />
              <YAxis domain={[0.7, 0.9]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '12px',
                  color: '#fff',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="tabicl_auc" name="TabICLv2 2.2.0 (Fast In-Context)" fill="#0d9488" radius={[4, 4, 0, 0]} />
              <Bar dataKey="tabpfn_auc" name="TabPFN 9.0.0" fill="#0284c7" radius={[4, 4, 0, 0]} />
            </ResponsiveBarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Two Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Risk Tier Pie Chart */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-teal-600" />
            <span>Risk Tier Categorization</span>
          </h3>
          <p className="text-xs text-slate-500">Distribution across completed patient assessments</p>

          <div className="h-56 w-full flex items-center justify-center">
            {pieData.length === 0 ? (
              <div className="text-center text-xs text-slate-400">
                Run assessments to populate real-time patient distribution data.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <ResponsivePieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label>
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={RISK_COLORS[index % RISK_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </ResponsivePieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Phase 7B Benchmark Table */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Official Phase 7B Performance Ledger (Validation Split)
            </h3>
            <span className="text-xs text-slate-400">Factual metrics • Frozen results</span>
          </div>

          <div className="overflow-x-auto max-h-64 overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 font-semibold sticky top-0 bg-white dark:bg-slate-900">
                  <th className="pb-2">Pathology</th>
                  <th className="pb-2">Algorithm</th>
                  <th className="pb-2">ROC-AUC</th>
                  <th className="pb-2">Accuracy</th>
                  <th className="pb-2">F1-Score</th>
                  <th className="pb-2 text-right">Inference Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {data?.benchmark_summary?.slice(0, 10).map((b: any, i: number) => (
                  <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 font-bold text-slate-900 dark:text-white capitalize">
                      {b.disease.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2.5 text-slate-500 font-medium">{b.model} {b.model_version}</td>
                    <td className="py-2.5 font-bold text-teal-600 dark:text-teal-400">
                      {b.roc_auc ? b.roc_auc.toFixed(4) : 'N/A'}
                    </td>
                    <td className="py-2.5">{b.accuracy ? `${(b.accuracy * 100).toFixed(1)}%` : 'N/A'}</td>
                    <td className="py-2.5">{b.f1_score ? b.f1_score.toFixed(4) : 'N/A'}</td>
                    <td className="py-2.5 text-right font-mono text-slate-500">
                      {b.inference_latency_ms ? `${b.inference_latency_ms.toFixed(0)} ms` : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
