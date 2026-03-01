import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Header } from '../components/Header';
import { StatusBadge, BudgetBar } from '../components/ui';
import { api } from '../api/client';
import { CATEGORY_LABELS, type Project, type BudgetLine, type ProjectStatus } from '../types';

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [budget, setBudget] = useState<BudgetLine[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      api.getProject(id) as Promise<Project>,
      api.getProjectBudget(id) as Promise<BudgetLine[]>,
    ]).then(([p, b]) => {
      setProject(p);
      setBudget(b);
      setLoading(false);
    });
  }, [id]);

  if (loading || !project) {
    return (
      <>
        <Header title="Project" />
        <div className="flex-1 flex items-center justify-center">
          <p className="text-gray-400">Loading...</p>
        </div>
      </>
    );
  }

  const totalBudget = project.total_budget || 0;
  const totalActual = project.total_actual || 0;

  return (
    <>
      <Header title={project.site_name} subtitle={`${project.carrier} · ${project.market || 'No market'}`} />

      <div className="flex-1 p-8 overflow-auto space-y-6">
        {/* Back button */}
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft size={16} /> Back
        </button>

        {/* Summary row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Project Info */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Project Info</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Status</dt>
                <dd><StatusBadge status={project.status as ProjectStatus} /></dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Site Number</dt>
                <dd className="text-gray-900">{project.site_number || '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Tower Type</dt>
                <dd className="text-gray-900">{project.tower_type || '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Scope</dt>
                <dd className="text-gray-900">{project.scope_type || '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">NTP Date</dt>
                <dd className="text-gray-900">{project.ntp_date || '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Target Completion</dt>
                <dd className="text-gray-900">{project.target_completion || '—'}</dd>
              </div>
            </dl>
          </div>

          {/* Budget Overview */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 lg:col-span-2">
            <h3 className="font-semibold text-gray-900 mb-4">Budget Overview</h3>
            <div className="mb-6">
              <BudgetBar budget={totalBudget} actual={totalActual} />
            </div>

            {budget.length > 0 ? (
              <div className="space-y-3">
                {budget.map((line) => (
                  <div key={line.id} className="flex items-center gap-4">
                    <span className="text-sm text-gray-600 w-36 shrink-0">
                      {CATEGORY_LABELS[line.category] || line.category}
                    </span>
                    <div className="flex-1">
                      <BudgetBar budget={line.budgeted_amount} actual={line.actual_amount} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No budget lines yet. Add budget categories to start tracking costs.</p>
            )}
          </div>
        </div>

        {/* Placeholder sections for future features */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-2">Time Entries</h3>
            <p className="text-sm text-gray-400">Time tracking data will appear here once integrations are connected.</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-2">Documents</h3>
            <p className="text-sm text-gray-400">Upload NTPs, construction drawings, and closeout packages here.</p>
          </div>
        </div>
      </div>
    </>
  );
}
