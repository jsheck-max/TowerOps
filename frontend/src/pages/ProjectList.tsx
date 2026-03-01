import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { Header } from '../components/Header';
import { StatusBadge, BudgetBar } from '../components/ui';
import { api } from '../api/client';
import { CARRIERS, type Project, type ProjectStatus } from '../types';

export function ProjectList() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  // Create form state
  const [form, setForm] = useState({ site_name: '', carrier: 'AT&T', site_number: '', market: '', state: '' });

  useEffect(() => {
    api.getProjects().then((p) => { setProjects(p as Project[]); setLoading(false); });
  }, []);

  const handleCreate = async () => {
    try {
      await api.createProject(form);
      const updated = await api.getProjects() as Project[];
      setProjects(updated);
      setShowCreate(false);
      setForm({ site_name: '', carrier: 'AT&T', site_number: '', market: '', state: '' });
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create project');
    }
  };

  return (
    <>
      <Header title="Projects" subtitle={`${projects.length} total`} />

      <div className="flex-1 p-8 overflow-auto">
        {/* Toolbar */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex gap-2">
            {/* Future: filter buttons */}
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Plus size={16} /> New Project
          </button>
        </div>

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl">
              <h3 className="text-lg font-semibold mb-4">New Project</h3>
              <div className="space-y-3">
                <input
                  placeholder="Site Name *"
                  value={form.site_name}
                  onChange={(e) => setForm({ ...form, site_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
                <div className="grid grid-cols-2 gap-3">
                  <select
                    value={form.carrier}
                    onChange={(e) => setForm({ ...form, carrier: e.target.value })}
                    className="px-3 py-2 border rounded-lg text-sm"
                  >
                    {CARRIERS.map((c) => <option key={c}>{c}</option>)}
                  </select>
                  <input
                    placeholder="Site Number"
                    value={form.site_number}
                    onChange={(e) => setForm({ ...form, site_number: e.target.value })}
                    className="px-3 py-2 border rounded-lg text-sm"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    placeholder="Market"
                    value={form.market}
                    onChange={(e) => setForm({ ...form, market: e.target.value })}
                    className="px-3 py-2 border rounded-lg text-sm"
                  />
                  <input
                    placeholder="State"
                    value={form.state}
                    onChange={(e) => setForm({ ...form, state: e.target.value })}
                    className="px-3 py-2 border rounded-lg text-sm"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
                <button onClick={handleCreate} disabled={!form.site_name} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">Create</button>
              </div>
            </div>
          </div>
        )}

        {/* Table */}
        {loading ? (
          <p className="text-gray-400 text-center py-12">Loading...</p>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50">
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Site</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Carrier</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Market</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Budget vs Actual</th>
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
                      <div className="font-medium text-gray-900">{p.site_name}</div>
                      {p.site_number && <div className="text-xs text-gray-400">{p.site_number}</div>}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{p.carrier}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{p.market || '—'}</td>
                    <td className="px-6 py-4"><StatusBadge status={p.status as ProjectStatus} /></td>
                    <td className="px-6 py-4 w-56">
                      <BudgetBar budget={p.total_budget || 0} actual={p.total_actual || 0} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
