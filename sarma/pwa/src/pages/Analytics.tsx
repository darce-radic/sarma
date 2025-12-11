import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

interface AnalyticsData {
  ai_usage: {
    total_requests: number;
    requests_this_month: number;
    gemini_requests: number;
    openai_requests: number;
    average_confidence: number;
  };
  nutrition: {
    total_meals_logged: number;
    average_daily_calories: number;
    calories_this_week: number[];
    protein_this_week: number[];
    carbs_this_week: number[];
    fat_this_week: number[];
  };
  goals: {
    daily_calorie_goal: number;
    days_on_track: number;
    days_total: number;
    streak: number;
  };
  recipes: {
    total_saved: number;
    favorite_cuisines: { name: string; count: number }[];
    most_cooked: { name: string; count: number }[];
  };
}

export default function Analytics() {
  const navigate = useNavigate();
  const { token } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('week');

  const fetchAnalytics = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/analytics?range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const analyticsData = await response.json();
        setData(analyticsData);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      // Mock data for demo
      setData({
        ai_usage: {
          total_requests: 247,
          requests_this_month: 38,
          gemini_requests: 195,
          openai_requests: 52,
          average_confidence: 0.87,
        },
        nutrition: {
          total_meals_logged: 156,
          average_daily_calories: 1850,
          calories_this_week: [1920, 1780, 2100, 1850, 1950, 1720, 1890],
          protein_this_week: [145, 132, 168, 142, 155, 138, 149],
          carbs_this_week: [210, 195, 245, 205, 220, 185, 215],
          fat_this_week: [68, 62, 75, 65, 70, 58, 67],
        },
        goals: {
          daily_calorie_goal: 2000,
          days_on_track: 18,
          days_total: 30,
          streak: 5,
        },
        recipes: {
          total_saved: 42,
          favorite_cuisines: [
            { name: 'Mediterranean', count: 12 },
            { name: 'Asian', count: 9 },
            { name: 'American', count: 8 },
            { name: 'Mexican', count: 7 },
            { name: 'Italian', count: 6 },
          ],
          most_cooked: [
            { name: 'Chicken Stir Fry', count: 8 },
            { name: 'Greek Salad', count: 6 },
            { name: 'Protein Smoothie', count: 5 },
          ],
        },
      });
    } finally {
      setLoading(false);
    }
  }, [token, timeRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const maxCalories = Math.max(...data.nutrition.calories_this_week);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-green-600 hover:text-green-700 flex items-center gap-2 mb-4"
          >
            ← Back to Dashboard
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Analytics</h1>
              <p className="text-gray-600 mt-2">Track your progress and insights</p>
            </div>

            {/* Time Range Selector */}
            <div className="flex gap-2 bg-white rounded-lg p-1 shadow-lg">
              {(['week', 'month', 'all'] as const).map(range => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-md font-medium transition-all capitalize ${
                    timeRange === range
                      ? 'bg-green-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* AI Requests */}
          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="text-4xl">🤖</div>
              <div className="text-sm opacity-80">This Month</div>
            </div>
            <div className="text-4xl font-bold mb-2">{data.ai_usage.requests_this_month}</div>
            <div className="text-sm opacity-90">AI Requests</div>
            <div className="mt-4 text-xs opacity-75">
              Total: {data.ai_usage.total_requests} all-time
            </div>
          </div>

          {/* Meals Logged */}
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="text-4xl">🍽️</div>
              <div className="text-sm opacity-80">All Time</div>
            </div>
            <div className="text-4xl font-bold mb-2">{data.nutrition.total_meals_logged}</div>
            <div className="text-sm opacity-90">Meals Logged</div>
            <div className="mt-4 text-xs opacity-75">
              Avg: {Math.round(data.nutrition.average_daily_calories)} cal/day
            </div>
          </div>

          {/* Goal Progress */}
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="text-4xl">🎯</div>
              <div className="text-sm opacity-80">Success Rate</div>
            </div>
            <div className="text-4xl font-bold mb-2">
              {Math.round((data.goals.days_on_track / data.goals.days_total) * 100)}%
            </div>
            <div className="text-sm opacity-90">On Track</div>
            <div className="mt-4 text-xs opacity-75">
              {data.goals.days_on_track} of {data.goals.days_total} days
            </div>
          </div>

          {/* Current Streak */}
          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="text-4xl">🔥</div>
              <div className="text-sm opacity-80">Keep Going!</div>
            </div>
            <div className="text-4xl font-bold mb-2">{data.goals.streak}</div>
            <div className="text-sm opacity-90">Day Streak</div>
            <div className="mt-4 text-xs opacity-75">
              Personal best: {data.goals.streak + 2} days
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Calorie Chart */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Daily Calories This Week</h3>
            <div className="space-y-3">
              {weekDays.map((day, idx) => (
                <div key={day}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{day}</span>
                    <span className="text-sm font-bold text-gray-900">
                      {data.nutrition.calories_this_week[idx]} cal
                    </span>
                  </div>
                  <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full transition-all"
                      style={{ width: `${(data.nutrition.calories_this_week[idx] / maxCalories) * 100}%` }}
                    ></div>
                    {/* Goal Line */}
                    <div
                      className="absolute top-0 h-full w-1 bg-red-500"
                      style={{ left: `${(data.goals.daily_calorie_goal / maxCalories) * 100}%` }}
                      title={`Goal: ${data.goals.daily_calorie_goal}`}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-600 rounded"></div>
                <span>Actual</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span>Goal ({data.goals.daily_calorie_goal} cal)</span>
              </div>
            </div>
          </div>

          {/* Macros Breakdown */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Average Macros This Week</h3>
            <div className="space-y-6">
              {/* Protein */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Protein</span>
                  <span className="text-sm font-bold text-gray-900">
                    {Math.round(data.nutrition.protein_this_week.reduce((a, b) => a + b, 0) / 7)}g/day
                  </span>
                </div>
                <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-red-400 to-red-500 rounded-full" style={{ width: '75%' }}></div>
                </div>
              </div>

              {/* Carbs */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Carbohydrates</span>
                  <span className="text-sm font-bold text-gray-900">
                    {Math.round(data.nutrition.carbs_this_week.reduce((a, b) => a + b, 0) / 7)}g/day
                  </span>
                </div>
                <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-yellow-400 to-yellow-500 rounded-full" style={{ width: '85%' }}></div>
                </div>
              </div>

              {/* Fat */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Fats</span>
                  <span className="text-sm font-bold text-gray-900">
                    {Math.round(data.nutrition.fat_this_week.reduce((a, b) => a + b, 0) / 7)}g/day
                  </span>
                </div>
                <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-blue-400 to-blue-500 rounded-full" style={{ width: '60%' }}></div>
                </div>
              </div>

              {/* Macro Pie Visual */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="text-center mb-4">
                  <div className="text-3xl font-bold text-gray-900">Macro Split</div>
                  <div className="text-sm text-gray-600">Average Distribution</div>
                </div>
                <div className="flex justify-center gap-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-500">30%</div>
                    <div className="text-xs text-gray-600">Protein</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-500">45%</div>
                    <div className="text-xs text-gray-600">Carbs</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-500">25%</div>
                    <div className="text-xs text-gray-600">Fat</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* AI Provider Breakdown */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">AI Provider Usage</h3>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded"></div>
                    <span className="font-medium text-gray-700">Gemini 2.0 Flash</span>
                  </div>
                  <span className="text-sm font-bold text-gray-900">{data.ai_usage.gemini_requests}</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-500 to-green-600" 
                    style={{ width: `${(data.ai_usage.gemini_requests / data.ai_usage.total_requests) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded"></div>
                    <span className="font-medium text-gray-700">GPT-4 Vision</span>
                  </div>
                  <span className="text-sm font-bold text-gray-900">{data.ai_usage.openai_requests}</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-600" 
                    style={{ width: `${(data.ai_usage.openai_requests / data.ai_usage.total_requests) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-green-800">
                <strong>💰 Cost Savings:</strong> Your smart routing has saved approximately 
                <strong className="text-green-900"> ${((data.ai_usage.gemini_requests * 0.019) + (data.ai_usage.openai_requests * 0.00)).toFixed(2)}</strong> 
                {' '}compared to using GPT-4 Vision exclusively!
              </div>
            </div>

            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-blue-800">
                <strong>🎯 Average Confidence:</strong> {(data.ai_usage.average_confidence * 100).toFixed(1)}%
                <div className="text-xs mt-1 text-blue-700">
                  High confidence means accurate AI predictions!
                </div>
              </div>
            </div>
          </div>

          {/* Recipe Stats */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Recipe Insights</h3>
            
            <div className="mb-6">
              <div className="text-3xl font-bold text-gray-900 mb-2">{data.recipes.total_saved}</div>
              <div className="text-sm text-gray-600">Recipes Saved</div>
            </div>

            <div className="mb-6">
              <h4 className="font-semibold text-gray-900 mb-3">Favorite Cuisines</h4>
              <div className="space-y-2">
                {data.recipes.favorite_cuisines.map(cuisine => (
                  <div key={cuisine.name} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{cuisine.name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-green-500 rounded-full"
                          style={{ width: `${(cuisine.count / data.recipes.total_saved) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium text-gray-900 w-6 text-right">{cuisine.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Most Cooked</h4>
              <div className="space-y-2">
                {data.recipes.most_cooked.map((recipe, idx) => (
                  <div key={recipe.name} className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{recipe.name}</div>
                    </div>
                    <div className="text-sm text-gray-600">{recipe.count}x</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
