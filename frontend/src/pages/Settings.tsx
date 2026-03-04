import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { api } from '../api/client';
import { Plug, Trash2, CheckCircle, Clock, DollarSign, Plus, TestTube2, Loader2 } from 'lucide-react';

interface Integration {
  id: string;
  platform: string;
  is_active: boolean;
  sync_frequency_minutes: number;
  last_sync_at: string | null;
  has_api_key: boolean;
  api_url: string | null;
}

interface LaborRate {
  id: string;
  role: string;
  hourly_rate: number;
  overtime_multiplier: number;
  per_diem: number;
}

const PLATFORMS = [
  {
    id: 'workyard',
    name: 'Workyard',
    description: 'GPS time tracking & workforce management for construction crews',
    color: 'bg-emerald-500',
    fields: [{ key: 'api_key', label: 'API Key', placeholder: 'Enter your Workyard API key' }],
  },
  {
    id: 'busybusy',
    name: 'busybusy',
    description: 'Time tracking built for construction with GPS & job costing',
    color: 'bg-orange-500',
    fields: [{ key: 'api_key', label: 'API Key', placeholder: 'Enter your busybusy API key' }],
  },
  {
    id: 'clockshark',
    name: 'ClockShark',
    description: 'Time tracking & scheduling for field service and construction',
    color: 'bg-blue-500',
    fields: [{ key: 'api_key', label: 'API Key', placeholder: 'Enter your ClockShark API key' }],
  },
  {
    id: 'exaktime',
    name: 'ExakTime',
    description: 'Rugged time tracking for remote construction jobsites',
    color: 'bg-purple-500',
    fields: [{ key: 'api_key', label: 'API Key', placeholder: 'Enter your ExakTime API key' }],
  },
];

const DEFAULT_RATES = [
  { role: 'foreman', hourly_rate: 45, overtime_multiplier: 1.5, per_diem: 100 },
  { role: 'technician', hourly_rate: 35, overtime_multiplier: 1.5, per_diem: 100 },
  { role: 'ground_hand', hourly_rate: 25, overtime_multiplier: 1.5, per_diem: 100 },
];

export function Settings() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [laborRates, setLaborRates] = useState<LaborRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [tab, setTab] = useState<'integrations' | 'labor' | 'org'>('integrations');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [intgs, rates] = await Promise.all([
        api.getIntegrations() as Promise<Integration[]>,
        api.getLaborRates() as Promise<LaborRate[]>,
      ]);
      setIntegrations(intgs);
      setLaborRates(rates);
    } catch {
      // handled by api client
    } finally {
      setLoading(false);
    }
  }

  const connectedPlatforms = new Set(integrations.map((i) => i.platform));

  async function handleConnect(platformId: string) {
    const apiKey = formData[`${platformId}_api_key`];
    if (!apiKey) return;
    setConnecting(platformId);
    try {
      await api.createIntegration({ platform: platformId, api_key: apiKey });
      setFormData((prev) => ({ ...prev, [`${platformId}_api_key`]: '' }));
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setConnecting(null);
    }
  }

  async function handleDisconnect(id: string) {
    if (!confirm('Disconnect this integration? Synced data will be preserved.')) return;
    try {
      await api.deleteIntegration(id);
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to disconnect');
    }
  }

  async function handleTest(id: string) {
    setTesting(id);
    try {
      const result = (await api.testIntegration(id)) as { message: string };
      alert(result.message);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Connection test failed');
    } finally {
      setTesting(null);
    }
  }

  async function handleAddRate(rate: typeof DEFAULT_RATES[0]) {
    try {
      await api.createLaborRate(rate);
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to add rate');
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Settings" />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="animate-spin text-gray-400" size={24} />
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Settings" subtitle="Manage integrations, rates, and organization" />

      <div className="flex-1 p-8 overflow-auto">
        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit mb-8">
          {[
            { id: 'integrations' as const, label: 'Integrations', icon: Plug },
            { id: 'labor' as const, label: 'Labor Rates', icon: DollarSign },
            { id: 'org' as const, label: 'Organization', icon: Clock },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                tab === id ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        {/* Integrations Tab */}
        {tab === 'integrations' && (
          <div className="space-y-6">
            <div className="max-w-3xl">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">Time Tracking Integrations</h3>
              <p className="text-sm text-gray-500 mb-6">
                Connect your field time-tracking platform to automatically sync crew hours, calculate labor costs, and track burn rates in real time.
              </p>
            </div>

            <div className="grid gap-4 max-w-3xl">
              {PLATFORMS.map((platform) => {
                const connected = integrations.find((i) => i.platform === platform.id);
                return (
                  <div
                    key={platform.id}
                    className={`bg-white rounded-xl border p-6 transition-all ${
                      connected ? 'border-green-200 bg-green-50/30' : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-lg ${platform.color} flex items-center justify-center text-white font-bold text-sm`}>
                          {platform.name[0]}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-gray-900">{platform.name}</h4>
                            {connected && (
                              <span className="flex items-center gap-1 text-xs font-medium text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
                                <CheckCircle size={12} /> Connected
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 mt-0.5">{platform.description}</p>
                          {connected?.last_sync_at && (
                            <p className="text-xs text-gray-400 mt-1">
                              Last synced: {new Date(connected.last_sync_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                      </div>

                      {connected && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleTest(connected.id)}
                            disabled={testing === connected.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                          >
                            {testing === connected.id ? <Loader2 size={12} className="animate-spin" /> : <TestTube2 size={12} />}
                            Test
                          </button>
                          <button
                            onClick={() => handleDisconnect(connected.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100"
                          >
                            <Trash2 size={12} /> Remove
                          </button>
                        </div>
                      )}
                    </div>

                    {!connected && (
                      <div className="mt-4 flex gap-3">
                        <input
                          type="password"
                          placeholder={platform.fields[0].placeholder}
                          value={formData[`${platform.id}_api_key`] || ''}
                          onChange={(e) =>
                            setFormData((prev) => ({ ...prev, [`${platform.id}_api_key`]: e.target.value }))
                          }
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                        />
                        <button
                          onClick={() => handleConnect(platform.id)}
                          disabled={!formData[`${platform.id}_api_key`] || connecting === platform.id}
                          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                          {connecting === platform.id ? (
                            <Loader2 size={14} className="animate-spin" />
                          ) : (
                            <Plug size={14} />
                          )}
                          Connect
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Labor Rates Tab */}
        {tab === 'labor' && (
          <div className="space-y-6 max-w-3xl">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">Labor Rates</h3>
              <p className="text-sm text-gray-500 mb-6">
                Set hourly rates by crew role. These rates are used to automatically calculate labor costs from synced time entries.
              </p>
            </div>

            {laborRates.length > 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50/50">
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Role</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Hourly Rate</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">OT Multiplier</th>
                      <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Per Diem</th>
                    </tr>
                  </thead>
                  <tbody>
                    {laborRates.map((rate) => (
                      <tr key={rate.id} className="border-b border-gray-50">
                        <td className="px-6 py-4 font-medium text-gray-900 capitalize">{rate.role.replace('_', ' ')}</td>
                        <td className="px-6 py-4 text-sm text-gray-600">${rate.hourly_rate.toFixed(2)}/hr</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{rate.overtime_multiplier}x</td>
                        <td className="px-6 py-4 text-sm text-gray-600">${rate.per_diem.toFixed(2)}/day</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                <DollarSign className="mx-auto text-gray-300 mb-3" size={32} />
                <p className="text-gray-500 mb-4">No labor rates configured yet.</p>
                <button
                  onClick={() => DEFAULT_RATES.forEach((r) => handleAddRate(r))}
                  className="flex items-center gap-2 mx-auto bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
                >
                  <Plus size={16} /> Load Default Rates
                </button>
              </div>
            )}
          </div>
        )}

        {/* Organization Tab */}
        {tab === 'org' && (
          <div className="space-y-6 max-w-3xl">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">Organization</h3>
              <p className="text-sm text-gray-500 mb-6">Manage your organization settings and team members.</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Organization Name</label>
                  <input
                    type="text"
                    defaultValue="Tennessee Tower Services"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Per Diem Distance Threshold</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      defaultValue="45"
                      className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    />
                    <span className="text-sm text-gray-500">minutes from home base</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Crew members traveling beyond this threshold qualify for per diem.</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Home Base Address</label>
                  <input
                    type="text"
                    defaultValue="5295 N Michigan Road"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>
              </div>
              <button className="mt-6 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
                Save Changes
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
