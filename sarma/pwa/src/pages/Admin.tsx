import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

interface AdminStats {
  users: {
    total: number;
    active: number;
    premium: number;
    pro: number;
    new_this_month: number;
  };
  revenue: {
    total_this_month: number;
    total_all_time: number;
    mrr: number;
    churn_rate: number;
  };
  ai_usage: {
    total_requests: number;
    gemini_requests: number;
    openai_requests: number;
    cost_this_month: number;
  };
  system: {
    uptime: string;
    api_response_time: number;
    error_rate: number;
  };
}

interface User {
  id: string;
  email: string;
  created_at: string;
  subscription_tier: string;
  ai_requests_this_month: number;
  last_login: string;
}

export default function Admin() {
  const navigate = useNavigate();
  const { user, token } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'system'>('overview');
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [systemSettings, setSystemSettings] = useState({
    openai_api_key: '',
    gemini_api_key: '',
    spoonacular_api_key: '',
    stripe_secret_key: '',
    coles_woolworths_mcp_url: '',
  });

  const fetchAdminData = useCallback(async () => {
    try {
      const [statsResponse, usersResponse] = await Promise.all([
        fetch('http://localhost:8000/api/v1/admin/stats', {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch('http://localhost:8000/api/v1/admin/users', {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
      ]);

      if (statsResponse.ok && usersResponse.ok) {
        setStats(await statsResponse.json());
        setUsers(await usersResponse.json());
      }
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
      // Mock data for demo
      setStats({
        users: {
          total: 1247,
          active: 856,
          premium: 312,
          pro: 87,
          new_this_month: 143,
        },
        revenue: {
          total_this_month: 4789.23,
          total_all_time: 32456.78,
          mrr: 4789.23,
          churn_rate: 2.8,
        },
        ai_usage: {
          total_requests: 45678,
          gemini_requests: 36542,
          openai_requests: 9136,
          cost_this_month: 287.45,
        },
        system: {
          uptime: '99.97%',
          api_response_time: 145,
          error_rate: 0.12,
        },
      });

      setUsers([
        {
          id: '1',
          email: 'user1@example.com',
          created_at: '2024-11-15',
          subscription_tier: 'premium',
          ai_requests_this_month: 127,
          last_login: '2024-12-10',
        },
        {
          id: '2',
          email: 'user2@example.com',
          created_at: '2024-10-22',
          subscription_tier: 'pro',
          ai_requests_this_month: 453,
          last_login: '2024-12-11',
        },
        {
          id: '3',
          email: 'user3@example.com',
          created_at: '2024-12-01',
          subscription_tier: 'free',
          ai_requests_this_month: 23,
          last_login: '2024-12-09',
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const fetchSystemSettings = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/admin/system-settings', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setSystemSettings({
          openai_api_key: data.openai_api_key || '',
          gemini_api_key: data.gemini_api_key || '',
          spoonacular_api_key: data.spoonacular_api_key || '',
          stripe_secret_key: data.stripe_secret_key || '',
          coles_woolworths_mcp_url: data.coles_woolworths_mcp_url || '',
        });
      }
    } catch (error) {
      console.error('Failed to fetch system settings:', error);
    } finally {
      setSettingsLoading(false);
    }
  }, [token]);

  const saveSystemSettings = async () => {
    setSettingsSaving(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/admin/system-settings', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(systemSettings),
      });
      if (!response.ok) {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      console.error(error);
      alert('Failed to save system settings');
    } finally {
      setSettingsSaving(false);
    }
  };

  useEffect(() => {
    // Check if user is admin
    if (!user?.is_admin) {
      navigate('/dashboard');
      return;
    }
    
    fetchAdminData();
    fetchSystemSettings();
  }, [user, navigate, fetchAdminData, fetchSystemSettings]);

  if (loading || !stats) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold">Admin Dashboard</h1>
              <p className="text-gray-400 mt-2">Platform overview and management</p>
            </div>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b border-gray-700">
            {(['overview', 'users', 'system'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 font-medium capitalize transition-colors ${
                  activeTab === tab
                    ? 'text-green-500 border-b-2 border-green-500'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-3xl">👥</div>
                  <span className="text-xs text-gray-400">Total</span>
                </div>
                <div className="text-3xl font-bold text-white mb-2">{stats.users.total.toLocaleString()}</div>
                <div className="text-sm text-gray-400">Total Users</div>
                <div className="mt-3 text-xs text-green-400">
                  +{stats.users.new_this_month} this month
                </div>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-3xl">💰</div>
                  <span className="text-xs text-gray-400">MRR</span>
                </div>
                <div className="text-3xl font-bold text-white mb-2">
                  ${stats.revenue.mrr.toLocaleString()}
                </div>
                <div className="text-sm text-gray-400">Monthly Revenue</div>
                <div className="mt-3 text-xs text-gray-400">
                  Churn: {stats.revenue.churn_rate}%
                </div>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-3xl">🤖</div>
                  <span className="text-xs text-gray-400">Requests</span>
                </div>
                <div className="text-3xl font-bold text-white mb-2">
                  {stats.ai_usage.total_requests.toLocaleString()}
                </div>
                <div className="text-sm text-gray-400">AI Requests</div>
                <div className="mt-3 text-xs text-gray-400">
                  Cost: ${stats.ai_usage.cost_this_month}
                </div>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-3xl">⚡</div>
                  <span className="text-xs text-gray-400">System</span>
                </div>
                <div className="text-3xl font-bold text-green-500 mb-2">{stats.system.uptime}</div>
                <div className="text-sm text-gray-400">Uptime</div>
                <div className="mt-3 text-xs text-gray-400">
                  {stats.system.api_response_time}ms avg
                </div>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* User Distribution */}
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 className="text-xl font-bold mb-6">User Distribution</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300">Free</span>
                      <span className="font-bold">
                        {(stats.users.total - stats.users.premium - stats.users.pro).toLocaleString()}
                      </span>
                    </div>
                    <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gray-500"
                        style={{ 
                          width: `${((stats.users.total - stats.users.premium - stats.users.pro) / stats.users.total) * 100}%` 
                        }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300">Premium ($9.99/mo)</span>
                      <span className="font-bold">{stats.users.premium.toLocaleString()}</span>
                    </div>
                    <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500"
                        style={{ width: `${(stats.users.premium / stats.users.total) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300">Pro ($19.99/mo)</span>
                      <span className="font-bold">{stats.users.pro.toLocaleString()}</span>
                    </div>
                    <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500"
                        style={{ width: `${(stats.users.pro / stats.users.total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-6 border-t border-gray-700">
                  <div className="text-sm text-gray-400">
                    Conversion Rate: {(((stats.users.premium + stats.users.pro) / stats.users.total) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* AI Provider Stats */}
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 className="text-xl font-bold mb-6">AI Provider Usage</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300">Gemini 2.0 Flash</span>
                      <span className="font-bold">{stats.ai_usage.gemini_requests.toLocaleString()}</span>
                    </div>
                    <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500"
                        style={{ 
                          width: `${(stats.ai_usage.gemini_requests / stats.ai_usage.total_requests) * 100}%` 
                        }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      Cost: ~${(stats.ai_usage.gemini_requests * 0.001).toFixed(2)}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300">GPT-4 Vision</span>
                      <span className="font-bold">{stats.ai_usage.openai_requests.toLocaleString()}</span>
                    </div>
                    <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500"
                        style={{ 
                          width: `${(stats.ai_usage.openai_requests / stats.ai_usage.total_requests) * 100}%` 
                        }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      Cost: ~${(stats.ai_usage.openai_requests * 0.02).toFixed(2)}
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-6 border-t border-gray-700">
                  <div className="text-sm text-gray-400">
                    <strong className="text-green-400">💰 Cost Savings:</strong> Multi-model routing saved ~$
                    {((stats.ai_usage.gemini_requests * 0.019) + (stats.ai_usage.openai_requests * 0.00)).toFixed(2)}
                    {' '}vs GPT-4 only
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="p-6 border-b border-gray-700">
              <h3 className="text-xl font-bold">User Management</h3>
              <p className="text-gray-400 text-sm mt-1">Manage platform users and subscriptions</p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-750">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Tier
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      AI Usage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Joined
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Last Login
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {users.map(user => (
                    <tr key={user.id} className="hover:bg-gray-750 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{user.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                          user.subscription_tier === 'pro' 
                            ? 'bg-blue-900 text-blue-300' 
                            : user.subscription_tier === 'premium'
                            ? 'bg-green-900 text-green-300'
                            : 'bg-gray-700 text-gray-300'
                        }`}>
                          {user.subscription_tier.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {user.ai_requests_this_month} requests
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        {new Date(user.last_login).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button className="text-green-500 hover:text-green-400 mr-3">View</button>
                        <button className="text-red-500 hover:text-red-400">Suspend</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-6 border-t border-gray-700 bg-gray-750">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-400">
                  Showing {users.length} of {stats.users.total.toLocaleString()} users
                </div>
                <div className="flex gap-2">
                  <button className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50">
                    Previous
                  </button>
                  <button className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600">
                    Next
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* System Tab */}
        {activeTab === 'system' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold mb-6">System Health</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-750 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-400">Uptime</div>
                    <div className="text-2xl font-bold text-green-500">{stats.system.uptime}</div>
                  </div>
                  <div className="text-3xl">✅</div>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-750 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-400">API Response Time</div>
                    <div className="text-2xl font-bold">{stats.system.api_response_time}ms</div>
                  </div>
                  <div className="text-3xl">⚡</div>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-750 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-400">Error Rate</div>
                    <div className="text-2xl font-bold text-green-500">{stats.system.error_rate}%</div>
                  </div>
                  <div className="text-3xl">🛡️</div>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold mb-6">API & Integration Keys</h3>
              {settingsLoading ? (
                <div className="text-gray-400">Loading settings...</div>
              ) : (
                <div className="space-y-4">
                  {[
                    { key: 'openai_api_key', label: 'OpenAI API Key' },
                    { key: 'gemini_api_key', label: 'Gemini API Key' },
                    { key: 'spoonacular_api_key', label: 'Spoonacular API Key' },
                    { key: 'stripe_secret_key', label: 'Stripe Secret Key' },
                    { key: 'coles_woolworths_mcp_url', label: 'MCP Server URL' },
                  ].map((field) => (
                    <div key={field.key} className="space-y-1">
                      <label className="block text-sm text-gray-300">{field.label}</label>
                      <input
                        type="text"
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                        value={(systemSettings as any)[field.key]}
                        onChange={(e) => setSystemSettings((prev) => ({ ...prev, [field.key]: e.target.value }))}
                      />
                    </div>
                  ))}
                  <button
                    onClick={saveSystemSettings}
                    disabled={settingsSaving}
                    className="w-full p-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-colors disabled:opacity-50"
                  >
                    {settingsSaving ? 'Saving...' : 'Save Settings'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
