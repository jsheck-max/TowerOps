import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { StatCard, StatusBadge, BudgetBar } from '../components/ui';
import { api } from '../api/client';
import type { DashboardStats, ProjectSummary, ProjectStatus } from '../types';

export function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, p] = await Promise.all([
          api.getDashboardStats() as Promise<DashboardStats>,
          api.getDashboardProjects() as Promise<ProjectSummary[]>,
        ]);
        setStats(s);
        setProjects(p);
      } catch {
        // If unauthorized, redirect handled by api client
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-400">Loading...</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Dashboard" subtitle="Real-time portfolio overview" />

      <div className="flex-1 p-8 space-y-8 overflow-auto">
        {/* Stat Cards */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Active Projects" value={stats.active_projects} color="blue" />
            <StatCard
              label="Total Budget"
              value={`$${(stats.total_budget / 1000).toFixed(0)}K`}
              color="green"
            />
            <StatCard
              label="Total Spent"
              value={`$${(stats.total_actual / 1000).toFixed(0)}K`}
              color="yellow"
            />
            <StatCard label="Over Budget" value={stats.over_budget_count} color="red" />
          </div>
        )}

        {/* Project List */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Projects</h3>

          {projects.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <p className="text-gray-500">No active projects yet.</p>
              <button
                onClick={() => navigate('/projects')}
                className="mt-4 text-blue-600 text-sm font-medium hover:underline"
              >
                Create your first project →
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/50">
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Site</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Carrier</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Budget</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Days</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr
                      key={p.id}
                      onClick={() => navigate(`/projects/${p.id}`)}
                      className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4">
                        <span className="font-medium text-gray-900">{p.site_name}</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">{p.carrier}</td>
                      <td className="px-6 py-4">
                        <StatusBadge status={p.status as ProjectStatus} />
                      </td>
                      <td className="px-6 py-4 w-64">
                        <BudgetBar budget={p.total_budget} actual={p.total_actual} />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {p.days_active != null ? `${p.days_active}d` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
