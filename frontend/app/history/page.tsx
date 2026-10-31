'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertCircle,
  Calendar,
  ChevronRight,
  Filter,
  History,
  Loader2,
  Search,
  Stethoscope,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';
import { getRiskColor } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

export default function HistoryPage() {
  const { user, setAuthModalOpen } = useAuthStore();
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [diseaseFilter, setDiseaseFilter] = useState<string>('ALL');

  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await apiRequest('/api/v1/predictions/history?limit=100');
        setHistory(Array.isArray(res) ? res : []);
      } catch (err) {
        console.error('Failed to load history', err);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, [user]);

  const filtered = history.filter((item) => {
    if (riskFilter !== 'ALL' && item.risk_level !== riskFilter) return false;
    if (diseaseFilter !== 'ALL' && item.disease_code.toLowerCase() !== diseaseFilter.toLowerCase()) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        item.disease_name.toLowerCase().includes(q) ||
        item.model_name.toLowerCase().includes(q) ||
        item.id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Title */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300 text-xs font-bold uppercase mb-2">
            Audit Records
          </div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white">
            Clinical Assessment History
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Historical evaluations stored with input parameters, feature attributions, and algorithm outputs.
          </p>
        </div>

        <Link
          href="/assess"
          className="px-4 py-2.5 rounded-xl font-bold text-xs bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-2 shadow-sm self-start sm:self-auto"
        >
          <Stethoscope className="w-4 h-4" />
          <span>New Assessment</span>
        </Link>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by condition or ID..."
            className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500/40"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter Risk:</span>
          </div>

          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-700 dark:text-slate-300"
          >
            <option value="ALL">All Risk Tiers</option>
            <option value="LOW">Low Risk (&lt;30%)</option>
            <option value="MODERATE">Moderate (30-70%)</option>
            <option value="HIGH">High Risk (&gt;70%)</option>
          </select>

          <select
            value={diseaseFilter}
            onChange={(e) => setDiseaseFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs font-semibold text-slate-700 dark:text-slate-300"
          >
            <option value="ALL">All 10 Diseases</option>
            <option value="diabetes">Diabetes</option>
            <option value="heart_disease">Heart Disease</option>
            <option value="stroke">Stroke</option>
            <option value="hypertension">Hypertension</option>
            <option value="chronic_kidney_disease">Kidney Disease</option>
            <option value="liver_disease">Liver Disease</option>
            <option value="parkinsons">Parkinson&apos;s</option>
            <option value="breast_cancer">Breast Cancer</option>
            <option value="lung_cancer">Lung Cancer</option>
            <option value="asthma">Asthma</option>
          </select>
        </div>
      </div>

      {/* History Table */}
      <div className="rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm p-6 sm:p-8">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs flex flex-col items-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
            <span>Retrieving historical assessments from PostgreSQL...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <History className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto" />
            <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">
              No matching assessment records found
            </p>
            <p className="text-xs text-slate-400">
              Run an assessment from the multi-disease panel to generate your first clinical report.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 font-semibold">
                  <th className="pb-3">Disease Evaluation</th>
                  <th className="pb-3">Model Architecture</th>
                  <th className="pb-3">Calculated Probability</th>
                  <th className="pb-3">Assigned Category</th>
                  <th className="pb-3">Evaluation Date</th>
                  <th className="pb-3 text-right">PDF Report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filtered.map((item) => {
                  const colors = getRiskColor(item.risk_level);
                  return (
                    <tr key={item.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-4">
                        <div className="font-bold text-slate-900 dark:text-white">
                          {item.disease_name}
                        </div>
                        {item.assessment_mode === 'combined' && (
                          <span className="text-[10px] font-semibold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/60 px-2 py-0.5 rounded-full inline-block mt-0.5 border border-teal-200 dark:border-teal-800">
                            Complete 10-Disease Assessment
                          </span>
                        )}
                      </td>
                      <td className="py-4 text-slate-500">
                        {item.model_name} {item.model_version}
                      </td>
                      <td className="py-4 font-bold text-slate-800 dark:text-slate-200">
                        {item.risk_percentage}%
                      </td>
                      <td className="py-4">
                        <span className={`px-2.5 py-0.5 rounded-full font-bold uppercase text-[10px] ${colors.badge}`}>
                          {item.risk_level}
                        </span>
                      </td>
                      <td className="py-4 text-slate-400">
                        {new Date(item.created_at).toLocaleDateString()} {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/results/${item.id}`}
                            className="font-bold text-teal-600 dark:text-teal-400 hover:underline"
                          >
                            Individual Report →
                          </Link>
                          {item.assessment_mode === 'combined' && item.assessment_id && (
                            <Link
                              href={`/results/combined/${item.assessment_id}`}
                              className="font-bold text-slate-600 dark:text-slate-300 hover:text-teal-600 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md text-[10px]"
                            >
                              Combined 10D
                            </Link>
                          )}
                        </div>
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
