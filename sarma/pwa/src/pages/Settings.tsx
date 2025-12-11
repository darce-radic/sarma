import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

interface UserSettings {
  gemini_api_key?: string;
  openai_api_key?: string;
  default_ai_provider: 'gemini' | 'openai';
  dietary_restrictions: string[];
  health_goals: {
    daily_calories?: number;
    daily_protein?: number;
    daily_carbs?: number;
    daily_fat?: number;
    weight_goal?: 'lose' | 'maintain' | 'gain';
  };
  notifications_enabled: boolean;
  email_notifications: boolean;
}

const DIETARY_OPTIONS = [
  'Vegetarian',
  'Vegan',
  'Gluten-Free',
  'Dairy-Free',
  'Keto',
  'Paleo',
  'Low-Carb',
  'Low-Fat',
  'Halal',
  'Kosher',
  'Nut-Free',
  'Soy-Free',
];

const WEIGHT_GOALS: NonNullable<UserSettings['health_goals']['weight_goal']>[] = ['lose', 'maintain', 'gain'];

export default function Settings() {
  const navigate = useNavigate();
  const { token } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<'gemini' | 'openai' | null>(null);
  const [testResult, setTestResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  
  const [settings, setSettings] = useState<UserSettings>({
    default_ai_provider: 'gemini',
    dietary_restrictions: [],
    health_goals: {},
    notifications_enabled: true,
    email_notifications: true,
  });

  const [showApiKeys, setShowApiKeys] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/settings', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    setSaving(true);
    setTestResult(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/settings', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        setTestResult({ type: 'success', message: 'Settings saved successfully!' });
        setTimeout(() => setTestResult(null), 3000);
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      setTestResult({ type: 'error', message: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const testApiKey = async (provider: 'gemini' | 'openai') => {
    setTesting(provider);
    setTestResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/settings/test-api-key', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider }),
      });

      const data = await response.json();

      if (response.ok) {
        setTestResult({ 
          type: 'success', 
          message: `✅ ${provider === 'gemini' ? 'Gemini' : 'OpenAI'} API key is valid!` 
        });
      } else {
        setTestResult({ 
          type: 'error', 
          message: `❌ ${provider === 'gemini' ? 'Gemini' : 'OpenAI'} API key is invalid: ${data.detail}` 
        });
      }
    } catch (error) {
      setTestResult({ 
        type: 'error', 
        message: `Failed to test ${provider} API key` 
      });
    } finally {
      setTesting(null);
    }
  };

  const toggleDietaryRestriction = (restriction: string) => {
    setSettings(prev => ({
      ...prev,
      dietary_restrictions: prev.dietary_restrictions.includes(restriction)
        ? prev.dietary_restrictions.filter(r => r !== restriction)
        : [...prev.dietary_restrictions, restriction],
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-4 md:py-8 px-3 sm:px-4 lg:px-8 mobile-content">
      <div className="max-w-4xl mx-auto">
        {/* Mobile Header */}
        <div className="mobile-header md:mb-8 md:static md:border-0 md:p-0 -mx-3 sm:-mx-4 lg:mx-0">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-green-600 hover:text-green-700 md:flex items-center gap-2 touch-target"
              aria-label="Back to Dashboard"
            >
              <span className="text-2xl">←</span>
              <span className="hidden md:inline">Back to Dashboard</span>
            </button>
          </div>
          <h1 className="text-2xl md:text-4xl font-bold text-gray-900">Settings</h1>
          <p className="text-sm md:text-base text-gray-600 mt-1">Customize your Sarma experience</p>
        </div>

        {/* Test Result Alert */}
        {testResult && (
          <div className={`mb-4 md:mb-6 p-3 md:p-4 rounded-lg text-sm md:text-base mobile-card ${
            testResult.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {testResult.message}
          </div>
        )}

        {/* API Keys Section */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6 mb-4 md:mb-6 mobile-card">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
            <div>
              <h2 className="text-xl md:text-2xl font-semibold text-gray-900">AI Provider Settings</h2>
              <p className="text-gray-600 text-xs md:text-sm mt-1">Configure your AI API keys</p>
            </div>
            <button
              onClick={() => setShowApiKeys(!showApiKeys)}
              className="text-green-600 hover:text-green-700 text-sm font-medium touch-target self-start sm:self-auto"
            >
              {showApiKeys ? 'Hide' : 'Show'} API Keys
            </button>
          </div>

          {/* Default Provider */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default AI Provider
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                onClick={() => setSettings(prev => ({ ...prev, default_ai_provider: 'gemini' }))}
                className={`p-3 md:p-4 rounded-lg border-2 transition-all touch-target text-left ${
                  settings.default_ai_provider === 'gemini'
                    ? 'border-green-600 bg-green-50'
                    : 'border-gray-200 hover:border-green-300 active:border-green-300'
                }`}
              >
                <div className="font-semibold text-gray-900 text-sm md:text-base">Gemini 2.0 Flash</div>
                <div className="text-xs md:text-sm text-gray-600 mt-1">Fast & cost-effective</div>
                <div className="text-xs text-green-600 mt-1">~$0.001 per request</div>
              </button>
              <button
                onClick={() => setSettings(prev => ({ ...prev, default_ai_provider: 'openai' }))}
                className={`p-3 md:p-4 rounded-lg border-2 transition-all touch-target text-left ${
                  settings.default_ai_provider === 'openai'
                    ? 'border-green-600 bg-green-50'
                    : 'border-gray-200 hover:border-green-300 active:border-green-300'
                }`}
              >
                <div className="font-semibold text-gray-900 text-sm md:text-base">GPT-4 Vision</div>
                <div className="text-xs md:text-sm text-gray-600 mt-1">Premium quality</div>
                <div className="text-xs text-green-600 mt-1">~$0.02 per request</div>
              </button>
            </div>
          </div>

          {showApiKeys && (
            <>
              {/* Gemini API Key */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gemini API Key (Optional)
                </label>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="password"
                    value={settings.gemini_api_key || ''}
                    onChange={(e) => setSettings(prev => ({ ...prev, gemini_api_key: e.target.value }))}
                    placeholder="AIza..."
                    className="flex-1 px-3 md:px-4 py-2 md:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-base"
                  />
                  <button
                    onClick={() => testApiKey('gemini')}
                    disabled={!settings.gemini_api_key || testing === 'gemini'}
                    className="px-4 py-2 md:py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 active:bg-green-800 disabled:bg-gray-300 disabled:cursor-not-allowed whitespace-nowrap touch-target text-sm md:text-base"
                  >
                    {testing === 'gemini' ? 'Testing...' : 'Test'}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Get your key from: <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-green-600 hover:underline touch-target">Google AI Studio</a>
                </p>
              </div>

              {/* OpenAI API Key */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  OpenAI API Key (Optional)
                </label>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="password"
                    value={settings.openai_api_key || ''}
                    onChange={(e) => setSettings(prev => ({ ...prev, openai_api_key: e.target.value }))}
                    placeholder="sk-..."
                    className="flex-1 px-3 md:px-4 py-2 md:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-base"
                  />
                  <button
                    onClick={() => testApiKey('openai')}
                    disabled={!settings.openai_api_key || testing === 'openai'}
                    className="px-4 py-2 md:py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 active:bg-green-800 disabled:bg-gray-300 disabled:cursor-not-allowed whitespace-nowrap touch-target text-sm md:text-base"
                  >
                    {testing === 'openai' ? 'Testing...' : 'Test'}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Get your key from: <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-green-600 hover:underline touch-target">OpenAI Platform</a>
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 md:p-4 text-xs md:text-sm text-blue-800">
                <strong>💡 Pro Tip:</strong> Use your own API keys to bypass platform limits and get unlimited AI requests!
              </div>
            </>
          )}
        </div>

        {/* Dietary Restrictions */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6 mb-4 md:mb-6 mobile-card">
          <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-2 md:mb-4">Dietary Restrictions</h2>
          <p className="text-gray-600 text-xs md:text-sm mb-4">Select any dietary restrictions to personalize your meal recommendations</p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 md:gap-3">
            {DIETARY_OPTIONS.map(option => (
              <button
                key={option}
                onClick={() => toggleDietaryRestriction(option)}
                className={`p-2 md:p-3 rounded-lg border-2 text-xs md:text-sm font-medium transition-all touch-target ${
                  settings.dietary_restrictions.includes(option)
                    ? 'border-green-600 bg-green-50 text-green-700'
                    : 'border-gray-200 text-gray-700 hover:border-green-300 active:border-green-300'
                }`}
              >
                {settings.dietary_restrictions.includes(option) && '✓ '}
                {option}
              </button>
            ))}
          </div>
        </div>

        {/* Health Goals */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6 mb-4 md:mb-6 mobile-card">
          <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-2 md:mb-4">Health Goals</h2>
          <p className="text-gray-600 text-xs md:text-sm mb-4">Set your daily nutritional targets</p>

          {/* Weight Goal */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Weight Goal</label>
            <div className="grid grid-cols-3 gap-2 md:gap-4">
              {WEIGHT_GOALS.map(goal => (
                <button
                  key={goal}
                  onClick={() => setSettings(prev => ({
                    ...prev,
                    health_goals: { ...prev.health_goals, weight_goal: goal }
                  }))}
                  className={`p-2 md:p-3 rounded-lg border-2 capitalize transition-all touch-target text-xs md:text-sm ${
                    settings.health_goals.weight_goal === goal
                      ? 'border-green-600 bg-green-50 text-green-700 font-semibold'
                      : 'border-gray-200 text-gray-700 hover:border-green-300 active:border-green-300'
                  }`}
                >
                  <span className="hidden sm:inline">{goal} Weight</span>
                  <span className="sm:hidden">{goal}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Macro Goals */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Daily Calories</label>
              <input
                type="number"
                value={settings.health_goals.daily_calories || ''}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  health_goals: { ...prev.health_goals, daily_calories: parseInt(e.target.value) || undefined }
                }))}
                placeholder="2000"
                className="w-full px-3 md:px-4 py-2 md:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-base"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Daily Protein (g)</label>
              <input
                type="number"
                value={settings.health_goals.daily_protein || ''}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  health_goals: { ...prev.health_goals, daily_protein: parseInt(e.target.value) || undefined }
                }))}
                placeholder="150"
                className="w-full px-3 md:px-4 py-2 md:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-base"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Daily Carbs (g)</label>
              <input
                type="number"
                value={settings.health_goals.daily_carbs || ''}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  health_goals: { ...prev.health_goals, daily_carbs: parseInt(e.target.value) || undefined }
                }))}
                placeholder="200"
                className="w-full px-3 md:px-4 py-2 md:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-base"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Daily Fat (g)</label>
              <input
                type="number"
                value={settings.health_goals.daily_fat || ''}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  health_goals: { ...prev.health_goals, daily_fat: parseInt(e.target.value) || undefined }
                }))}
                placeholder="70"
                className="w-full px-3 md:px-4 py-2 md:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-base"
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white rounded-xl shadow-lg p-4 md:p-6 mb-4 md:mb-6 mobile-card">
          <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">Notifications</h2>
          
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer touch-target py-2">
              <div>
                <div className="font-medium text-gray-900 text-sm md:text-base">Push Notifications</div>
                <div className="text-xs md:text-sm text-gray-600">Receive meal reminders and tips</div>
              </div>
              <input
                type="checkbox"
                checked={settings.notifications_enabled}
                onChange={(e) => setSettings(prev => ({ ...prev, notifications_enabled: e.target.checked }))}
                className="h-5 w-5 md:h-6 md:w-6 text-green-600 focus:ring-green-500 border-gray-300 rounded"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer touch-target py-2">
              <div>
                <div className="font-medium text-gray-900 text-sm md:text-base">Email Notifications</div>
                <div className="text-xs md:text-sm text-gray-600">Weekly health reports and updates</div>
              </div>
              <input
                type="checkbox"
                checked={settings.email_notifications}
                onChange={(e) => setSettings(prev => ({ ...prev, email_notifications: e.target.checked }))}
                className="h-5 w-5 md:h-6 md:w-6 text-green-600 focus:ring-green-500 border-gray-300 rounded"
              />
            </label>
          </div>
        </div>

        {/* Save Button - Sticky on mobile */}
        <div className="flex flex-col sm:flex-row gap-3 md:gap-4 sticky bottom-16 md:static bg-gradient-to-br from-green-50 to-blue-50 p-3 md:p-0 -mx-3 sm:-mx-4 lg:mx-0 z-10">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 bg-green-600 text-white py-3 md:py-4 px-6 rounded-lg font-semibold hover:bg-green-700 active:bg-green-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors touch-target shadow-lg md:shadow-none text-sm md:text-base"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 md:py-4 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:border-gray-400 active:border-gray-500 transition-colors touch-target bg-white shadow-lg md:shadow-none text-sm md:text-base"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
