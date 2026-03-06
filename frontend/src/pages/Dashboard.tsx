import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../components/Header';
import { StatCard, StatusBadge, BudgetBar } from '../components/ui';
import { api } from '../api/client';
import { RefreshCw, Loader2, TrendingUp, DollarSign, FolderOpen, AlertTriangle } from 'lucide-react';
import type { DashboardStats, ProjectSummary, ProjectStatus } from '../types';

interface SyncResult {
  synced: number;
  total_cost: number;
  projects_updated: number;
  employees_with_rates: number;
  skipped_no_project: number;
  days: number;
}

function formatCost(n: number): string {
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}K`;
  if (n > 0) return `$${n.toFixed(0)}`;
  return '$0';
}

export function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const [s, p] = await Promise.all([
        api.getDashboardStats() as Promise<DashboardStats>,
        api.getDashboardProjects() as Promise<ProjectSummary[]>,
      ]);
      setStats(s);
      setProjects(p);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    setSyncResult(null);
    try {
      const result = await api.syncWorkyardTime(14) as SyncResult;
      setSyncResult(result);
      await load();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Sync failed');
    } finally {
      setSyncing(false);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="animate-spin text-gray-400" size={24} />
        </div>
      </>
    );
  }

  // Sort projects by spend descending
  const sortedProjects = [...projects].sort((a, b) => (b.total_actual || 0) - (a.total_actual || 0));
  const activeWithSpend = sortedProjects.filter(p => (p.total_actual || 0) > 0);

  return (
    <>
      <Header title="Dashboard" subtitle="Real-time portfolio overview" />

      <div className="flex-1 p-8 space-y-6 overflow-auto bg-gray-50/50">
        {/* Sync Bar */}
        <div className="flex items-center justify-between bg-white rounded-xl border border-gray-200 px-6 py-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Workyard Sync</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {syncResult
                ? `Last sync: ${syncResult.synced} time entries · ${formatCost(syncResult.total_cost)} labor cost · ${syncResult.projects_updated} sites updated`
                : 'Pull the latest time cards and crew costs from Workyard'
              }
            </p>
          </div>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 bg-emerald-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors shadow-sm"
          >
            {syncing ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            {syncing ? 'Syncing...' : 'Sync Now'}
          </button>
        </div>

        {/* Stat Cards */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Active Sites"
              value={stats.active_projects}
              sublabel={`${stats.total_projects} total`}
              color="blue"
            />
            <StatCard
              label="Labor Spend (14d)"
              value={formatCost(stats.total_actual)}
              color="emerald"
            />
            <StatCard
              label="Total Budget"
              value={stats.total_budget > 0 ? formatCost(stats.total_budget) : 'Not set'}
              sublabel={stats.total_budget > 0 ? undefined : 'Add budgets to track'}
              color="green"
            />
            <StatCard
              label="Over Budget"
              value={stats.over_budget_count}
              sublabel={stats.over_budget_count > 0 ? 'sites exceeded budget' : 'All on track'}
              color={stats.over_budget_count > 0 ? 'red' : 'green'}
            />
          </div>
        )}

        {/* Top Spend Projects */}
        {activeWithSpend.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Top Sites by Labor Spend</h3>
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/80">
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Site</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Carrier</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Labor Spend</th>
                  </tr>
                </thead>
                <tbody>
                  {activeWithSpend.slice(0, 15).map((p, i) => (
                    <tr
                      key={p.id}
                      onClick={() => navigate(`/projects/${p.id}`)}
                      className="border-b border-gray-50 hover:bg-blue-50/50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4">
                        <span className="font-medium text-gray-900">{p.site_name}</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">{p.carrier}</td>
                      <td className="px-6 py-4">
                        <StatusBadge status={p.status as ProjectStatus} />
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className="text-sm font-semibold text-gray-900">
                          {formatCost(p.total_actual)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* All Active Projects */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900">All Active Projects</h3>
            <button
              onClick={() => navigate('/projects')}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View all →
            </button>
          </div>

          {projects.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <FolderOpen className="mx-auto text-gray-300 mb-3" size={32} />
              <p className="text-gray-500">No active projects yet.</p>
              <button
                onClick={() => navigate('/projects')}
                className="mt-4 text-blue-600 text-sm font-medium hover:underline"
              >
                Import from Workyard →
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/80">
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Site</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Carrier</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Budget vs Spend</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedProjects.slice(0, 25).map((p) => (
                    <tr
                      key={p.id}
                      onClick={() => navigate(`/projects/${p.id}`)}
                      className="border-b border-gray-50 hover:bg-blue-50/50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4">
                        <span className="font-medium text-gray-900">{p.site_name}</span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">{p.carrier}</td>
                      <td className="px-6 py-4">
                        <StatusBadge status={p.status as ProjectStatus} />
                      </td>
                      <td className="px-6 py-4 w-48">
                        <BudgetBar budget={p.total_budget} actual={p.total_actual} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {sortedProjects.length > 25 && (
                <div className="px-6 py-3 bg-gray-50 text-center">
                  <button
                    onClick={() => navigate('/projects')}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    View all {sortedProjects.length} projects →
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
