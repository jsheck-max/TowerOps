import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Download, CheckCircle, Loader2, Search, X } from 'lucide-react';
import { Header } from '../components/Header';
import { StatusBadge, BudgetBar } from '../components/ui';
import { api } from '../api/client';
import { CARRIERS, type Project, type ProjectStatus } from '../types';

interface WorkyardProject {
  workyard_id: string;
  site_name: string;
  site_number: string;
  address: string;
  state: string;
  market: string;
  status: string;
  customer_name: string;
  already_imported: boolean;
  recently_active: boolean;
  activity_status: string;
  raw: Record<string, unknown>;
}

export function ProjectList() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showImport, setShowImport] = useState(false);

  // Create form state
  const [form, setForm] = useState({
    site_name: '', carrier: 'AT&T', site_number: '', market: '', state: '',
    address: '', scope_type: '', tower_type: '', total_budget: 0,
  });

  // Workyard import state
  const [wyProjects, setWyProjects] = useState<WorkyardProject[]>([]);
  const [wyLoading, setWyLoading] = useState(false);
  const [wyError, setWyError] = useState('');
  const [wySearch, setWySearch] = useState('');
  const [selectedWy, setSelectedWy] = useState<Set<string>>(new Set());
  const [wyFilter, setWyFilter] = useState<'all' | 'active' | 'inactive'>('active');
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const p = await api.getProjects() as Project[];
      setProjects(p);
    } finally {
      setLoading(false);
    }
  }

  const handleCreate = async () => {
    try {
      await api.createProject(form);
      await loadProjects();
      setShowCreate(false);
      setForm({ site_name: '', carrier: 'AT&T', site_number: '', market: '', state: '', address: '', scope_type: '', tower_type: '', total_budget: 0 });
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create project');
    }
  };

  const handleOpenImport = async () => {
    setShowImport(true);
    setWyLoading(true);
    setWyError('');
    try {
      const result = await api.getWorkyardProjects() as { projects: WorkyardProject[]; total: number; active_count: number; inactive_count: number };
      setWyProjects(result.projects);
    } catch (err) {
      setWyError(err instanceof Error ? err.message : 'Failed to fetch Workyard projects');
    } finally {
      setWyLoading(false);
    }
  };

  const handleImportSelected = async () => {
    if (selectedWy.size === 0) return;
    setImporting(true);
    try {
      const result = await api.importWorkyardProjectsBulk(Array.from(selectedWy)) as {
        imported: number; skipped: number;
      };
      alert(`Imported ${result.imported} projects${result.skipped > 0 ? `, skipped ${result.skipped}` : ''}`);
      setShowImport(false);
      setSelectedWy(new Set());
      await loadProjects();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const handleImportSingle = (proj: WorkyardProject) => {
    setForm({
      site_name: proj.site_name,
      site_number: proj.site_number || '',
      carrier: 'AT&T',
      market: proj.market || '',
      state: proj.state || '',
      address: proj.address || '',
      scope_type: '',
      tower_type: '',
      total_budget: 0,
    });
    setShowImport(false);
    setShowCreate(true);
  };

  const toggleSelect = (id: string) => {
    setSelectedWy((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    const available = filteredWy.filter((p) => !p.already_imported).map((p) => p.workyard_id);
    setSelectedWy(new Set(available));
  };

  const filteredWy = wyProjects.filter((p) => {
    // Activity filter
    if (wyFilter === 'active' && !p.recently_active) return false;
    if (wyFilter === 'inactive' && p.recently_active) return false;
    // Search filter
    if (!wySearch) return true;
    const q = wySearch.toLowerCase();
    return p.site_name.toLowerCase().includes(q) ||
      (p.site_number || '').toLowerCase().includes(q) ||
      (p.market || '').toLowerCase().includes(q) ||
      (p.customer_name || '').toLowerCase().includes(q);
  });

  return (
    <>
      <Header title="Projects" subtitle={`${projects.length} total`} />

      <div className="flex-1 p-8 overflow-auto">
        {/* Toolbar */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex gap-2">
            {/* Future: filter buttons */}
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleOpenImport}
              className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors"
            >
              <Download size={16} /> Import from Workyard
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              <Plus size={16} /> New Project
            </button>
          </div>
        </div>

        {/* Workyard Import Modal */}
        {showImport && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl w-full max-w-4xl shadow-xl max-h-[85vh] flex flex-col">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Import from Workyard</h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      Select projects to import into TowerOps. Data auto-fills from your Workyard account.
                    </p>
                  </div>
                  <button onClick={() => setShowImport(false)} className="text-gray-400 hover:text-gray-600">
                    <X size={20} />
                  </button>
                </div>

                {!wyLoading && !wyError && (
                  <div className="space-y-3 mt-4">
                    <div className="flex gap-2">
                      {(['active', 'inactive', 'all'] as const).map((f) => (
                        <button
                          key={f}
                          onClick={() => setWyFilter(f)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            wyFilter === f
                              ? f === 'active' ? 'bg-emerald-100 text-emerald-700' : f === 'inactive' ? 'bg-gray-200 text-gray-700' : 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                          }`}
                        >
                          {f === 'active' ? `In Construction (${wyProjects.filter(p => p.recently_active).length})` :
                           f === 'inactive' ? `Inactive (${wyProjects.filter(p => !p.recently_active).length})` :
                           `All (${wyProjects.length})`}
                        </button>
                      ))}
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="relative flex-1">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                          placeholder="Search by name, number, or market..."
                          value={wySearch}
                          onChange={(e) => setWySearch(e.target.value)}
                          className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                        />
                      </div>
                      <button
                        onClick={selectAll}
                        className="text-sm text-emerald-600 hover:text-emerald-700 font-medium whitespace-nowrap"
                      >
                        Select all ({filteredWy.filter((p) => !p.already_imported).length})
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex-1 overflow-auto p-6">
                {wyLoading ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <Loader2 className="animate-spin text-emerald-500 mb-3" size={28} />
                    <p className="text-sm text-gray-500">Fetching projects from Workyard...</p>
                  </div>
                ) : wyError ? (
                  <div className="bg-red-50 text-red-700 p-4 rounded-lg text-sm">{wyError}</div>
                ) : filteredWy.length === 0 ? (
                  <p className="text-center text-gray-400 py-12">No projects found in Workyard.</p>
                ) : (
                  <div className="space-y-2">
                    {filteredWy.map((proj) => (
                      <div
                        key={proj.workyard_id}
                        className={`flex items-center gap-4 p-4 rounded-lg border transition-all cursor-pointer ${
                          proj.already_imported
                            ? 'border-gray-100 bg-gray-50 opacity-60'
                            : selectedWy.has(proj.workyard_id)
                            ? 'border-emerald-300 bg-emerald-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => !proj.already_imported && toggleSelect(proj.workyard_id)}
                      >
                        <div className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 ${
                          proj.already_imported
                            ? 'border-gray-300 bg-gray-200'
                            : selectedWy.has(proj.workyard_id)
                            ? 'border-emerald-500 bg-emerald-500'
                            : 'border-gray-300'
                        }`}>
                          {(selectedWy.has(proj.workyard_id) || proj.already_imported) && (
                            <CheckCircle size={14} className="text-white" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 truncate">{proj.site_name}</span>
                            {proj.site_number && (
                              <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{proj.site_number}</span>
                            )}
                            {proj.already_imported && (
                              <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full font-medium">Already imported</span>
                            )}
                            {!proj.recently_active && (
                              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full font-medium">No activity 5d+</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-500 mt-0.5 flex gap-3">
                            {proj.market && <span>{proj.market}{proj.state ? `, ${proj.state}` : ''}</span>}
                            {proj.address && <span className="truncate">{proj.address}</span>}
                            {proj.customer_name && <span>Client: {proj.customer_name}</span>}
                          </div>
                        </div>
                        {!proj.already_imported && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleImportSingle(proj); }}
                            className="text-xs text-blue-600 hover:text-blue-700 font-medium whitespace-nowrap px-2 py-1 rounded hover:bg-blue-50"
                          >
                            Edit & Import
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {selectedWy.size > 0 && (
                <div className="p-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between rounded-b-xl">
                  <span className="text-sm text-gray-600">{selectedWy.size} project{selectedWy.size > 1 ? 's' : ''} selected</span>
                  <div className="flex gap-3">
                    <button onClick={() => setSelectedWy(new Set())} className="text-sm text-gray-500 hover:text-gray-700">
                      Clear
                    </button>
                    <button
                      onClick={handleImportSelected}
                      disabled={importing}
                      className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
                    >
                      {importing ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                      Import {selectedWy.size} Project{selectedWy.size > 1 ? 's' : ''}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl">
              <h3 className="text-lg font-semibold mb-4">
                {form.site_name ? 'Import Project' : 'New Project'}
              </h3>
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
                <input
                  placeholder="Address"
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
                <div className="grid grid-cols-2 gap-3">
                  <input
                    placeholder="Market / City"
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
                <div className="grid grid-cols-2 gap-3">
                  <select
                    value={form.scope_type}
                    onChange={(e) => setForm({ ...form, scope_type: e.target.value })}
                    className="px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Scope Type</option>
                    <option value="new_build">New Build</option>
                    <option value="modification">Modification</option>
                    <option value="decommission">Decommission</option>
                    <option value="maintenance">Maintenance</option>
                  </select>
                  <select
                    value={form.tower_type}
                    onChange={(e) => setForm({ ...form, tower_type: e.target.value })}
                    className="px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Tower Type</option>
                    <option value="self_support">Self Support</option>
                    <option value="monopole">Monopole</option>
                    <option value="guyed">Guyed</option>
                    <option value="rooftop">Rooftop</option>
                    <option value="small_cell">Small Cell</option>
                  </select>
                </div>
                <input
                  placeholder="Total Budget ($)"
                  type="number"
                  value={form.total_budget || ''}
                  onChange={(e) => setForm({ ...form, total_budget: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button onClick={() => { setShowCreate(false); setForm({ site_name: '', carrier: 'AT&T', site_number: '', market: '', state: '', address: '', scope_type: '', tower_type: '', total_budget: 0 }); }} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
                <button onClick={handleCreate} disabled={!form.site_name} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">Create</button>
              </div>
            </div>
          </div>
        )}

        {/* Table */}
        {loading ? (
          <p className="text-gray-400 text-center py-12">Loading...</p>
        ) : projects.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <p className="text-gray-500 mb-2">No projects yet.</p>
            <p className="text-sm text-gray-400">Create one manually or import from Workyard.</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50">
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Site</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Carrier</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Market</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Labor Spend</th>
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
                    <td className="px-6 py-4 w-48">
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
