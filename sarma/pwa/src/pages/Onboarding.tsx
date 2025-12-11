import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

type WeightGoal = 'lose' | 'maintain' | 'gain';

interface OnboardingStep {
  id: number;
  title: string;
  description: string;
}

const STEPS: OnboardingStep[] = [
  {
    id: 1,
    title: 'Welcome to Sarma! 👋',
    description: 'Your AI-powered health and nutrition companion. Let\'s get you started!',
  },
  {
    id: 2,
    title: 'Set Your Goals 🎯',
    description: 'Tell us about your health objectives to personalize your experience.',
  },
  {
    id: 3,
    title: 'Dietary Preferences 🥗',
    description: 'Let us know if you have any dietary restrictions or preferences.',
  },
  {
    id: 4,
    title: 'AI Features 🤖',
    description: 'Discover what our AI can do for you!',
  },
  {
    id: 5,
    title: 'You\'re All Set! 🎉',
    description: 'Ready to start your health journey?',
  },
];

const DIETARY_OPTIONS = [
  'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free',
  'Keto', 'Paleo', 'Low-Carb', 'Low-Fat',
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { token } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Onboarding data
  const [data, setData] = useState({
    weight_goal: 'maintain' as WeightGoal,
    daily_calories: 2000,
    dietary_restrictions: [] as string[],
  });

  const handleNext = async () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    } else {
      await completeOnboarding();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const completeOnboarding = async () => {
    setLoading(true);

    try {
      // Save settings
      await fetch('http://localhost:8000/api/v1/settings', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          health_goals: {
            weight_goal: data.weight_goal,
            daily_calories: data.daily_calories,
          },
          dietary_restrictions: data.dietary_restrictions,
          default_ai_provider: 'gemini',
          notifications_enabled: true,
          email_notifications: true,
        }),
      });

      // Mark onboarding as complete (you can add this to user profile)
      localStorage.setItem('onboarding_complete', 'true');

      // Navigate to dashboard
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      alert('Failed to save settings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleDietary = (option: string) => {
    setData(prev => ({
      ...prev,
      dietary_restrictions: prev.dietary_restrictions.includes(option)
        ? prev.dietary_restrictions.filter(r => r !== option)
        : [...prev.dietary_restrictions, option],
    }));
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="text-center">
            <div className="text-8xl mb-8">🌱</div>
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Welcome to Sarma Health!
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              {"Your journey to better health starts here. Let's personalize your experience in just a few steps."}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
              <div className="bg-green-50 p-6 rounded-xl">
                <div className="text-4xl mb-4">📸</div>
                <h3 className="font-semibold text-gray-900 mb-2">AI Meal Analysis</h3>
                <p className="text-gray-600 text-sm">
                  Snap a photo of your meal and get instant nutrition insights
                </p>
              </div>
              <div className="bg-blue-50 p-6 rounded-xl">
                <div className="text-4xl mb-4">🍳</div>
                <h3 className="font-semibold text-gray-900 mb-2">Smart Recipes</h3>
                <p className="text-gray-600 text-sm">
                  Get personalized recipe recommendations based on your goals
                </p>
              </div>
              <div className="bg-purple-50 p-6 rounded-xl">
                <div className="text-4xl mb-4">💬</div>
                <h3 className="font-semibold text-gray-900 mb-2">AI Health Coach</h3>
                <p className="text-gray-600 text-sm">
                  Chat with AI for nutrition advice and health tips
                </p>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">{"What's Your Health Goal?"}</h2>
            <p className="text-gray-600 mb-8">This helps us personalize your recommendations</p>

            <div className="space-y-6">
              {/* Weight Goal */}
              <div>
                <label className="block text-lg font-semibold text-gray-900 mb-4">
                  I want to...
                </label>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { value: 'lose', label: 'Lose Weight', emoji: '📉' },
                    { value: 'maintain', label: 'Maintain Weight', emoji: '⚖️' },
                    { value: 'gain', label: 'Gain Weight', emoji: '📈' },
                  ].map(option => (
                    <button
                      key={option.value}
                      onClick={() => setData(prev => ({ ...prev, weight_goal: option.value as WeightGoal }))}
                      className={`p-6 rounded-xl border-2 transition-all ${
                        data.weight_goal === option.value
                          ? 'border-green-600 bg-green-50 shadow-lg scale-105'
                          : 'border-gray-200 hover:border-green-300'
                      }`}
                    >
                      <div className="text-4xl mb-2">{option.emoji}</div>
                      <div className="font-semibold text-gray-900">{option.label}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Daily Calories */}
              <div>
                <label className="block text-lg font-semibold text-gray-900 mb-4">
                  Daily Calorie Target
                </label>
                <div className="relative">
                  <input
                    type="range"
                    min="1200"
                    max="4000"
                    step="100"
                    value={data.daily_calories}
                    onChange={(e) => setData(prev => ({ ...prev, daily_calories: parseInt(e.target.value) }))}
                    className="w-full h-3 bg-green-100 rounded-lg appearance-none cursor-pointer accent-green-600"
                  />
                  <div className="flex justify-between text-sm text-gray-600 mt-2">
                    <span>1,200</span>
                    <span className="text-2xl font-bold text-green-600">{data.daily_calories}</span>
                    <span>4,000</span>
                  </div>
                </div>
                <p className="text-sm text-gray-500 mt-4 text-center">
                  {"Don't worry, you can adjust this anytime in Settings"}
                </p>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Dietary Preferences</h2>
            <p className="text-gray-600 mb-8">Select any that apply to you (optional)</p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {DIETARY_OPTIONS.map(option => (
                <button
                  key={option}
                  onClick={() => toggleDietary(option)}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    data.dietary_restrictions.includes(option)
                      ? 'border-green-600 bg-green-50 shadow-lg'
                      : 'border-gray-200 hover:border-green-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900">
                    {data.dietary_restrictions.includes(option) && '✓ '}
                    {option}
                  </div>
                </button>
              ))}
            </div>

            <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-sm text-blue-800">
                <strong>💡 Tip:</strong> {"We'll use this to filter recipes and meal recommendations to match your dietary needs."}
              </p>
            </div>
          </div>
        );

      case 4:
        return (
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">AI-Powered Features</h2>
            <p className="text-gray-600 mb-8">{"Here's what you can do with Sarma"}</p>

            <div className="space-y-6">
              <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-xl border-2 border-green-200">
                <div className="flex items-start gap-4">
                  <div className="text-4xl">📸</div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Meal Photo Analysis</h3>
                    <p className="text-gray-700 mb-3">
                      Take a photo of any meal and our AI will instantly identify ingredients, estimate calories, 
                      and provide detailed nutrition information.
                    </p>
                    <div className="bg-white rounded-lg p-3 text-sm">
                      <strong>Example:</strong> &quot;Grilled chicken breast with rice and broccoli&quot;<br/>
                      <span className="text-green-600">→ 520 calories, 45g protein, 55g carbs, 12g fat</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-xl border-2 border-blue-200">
                <div className="flex items-start gap-4">
                  <div className="text-4xl">🍳</div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">AI Recipe Generator</h3>
                    <p className="text-gray-700 mb-3">
                      {"Tell our AI what ingredients you have or what you're craving, and it will create personalized recipes that match your dietary preferences and health goals."}
                    </p>
                    <div className="bg-white rounded-lg p-3 text-sm">
                      <strong>Try:</strong> &quot;Create a high-protein breakfast under 400 calories&quot;<br/>
                      <span className="text-blue-600">→ Get custom recipes with instructions and nutrition</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-xl border-2 border-purple-200">
                <div className="flex items-start gap-4">
                  <div className="text-4xl">💬</div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Health Chat Assistant</h3>
                    <p className="text-gray-700 mb-3">
                      Ask any nutrition or health question and get instant, personalized advice 
                      from our AI health coach.
                    </p>
                    <div className="bg-white rounded-lg p-3 text-sm">
                      <strong>Ask:</strong> &quot;What should I eat before a workout?&quot;<br/>
                      <span className="text-purple-600">→ Get personalized recommendations based on your goals</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="text-center">
            <div className="text-8xl mb-8">🎉</div>
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              {"You're All Set!"}
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Your personalized health journey starts now
            </p>

            <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-2xl p-8 mb-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Your Profile</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
                <div className="bg-white p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Goal</div>
                  <div className="font-semibold text-gray-900 capitalize">{data.weight_goal} Weight</div>
                </div>
                <div className="bg-white p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Daily Target</div>
                  <div className="font-semibold text-gray-900">{data.daily_calories} calories</div>
                </div>
                <div className="bg-white p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Dietary Preferences</div>
                  <div className="font-semibold text-gray-900">
                    {data.dietary_restrictions.length > 0 
                      ? data.dietary_restrictions.join(', ') 
                      : 'None selected'}
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-amber-800">
                <strong>🎁 Free Tier:</strong> You start with 50 AI requests per month. 
                Upgrade to Premium anytime for unlimited access!
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep} of {STEPS.length}
            </span>
            <span className="text-sm font-medium text-gray-700">
              {Math.round((currentStep / STEPS.length) * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / STEPS.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12 mb-8">
          {renderStepContent()}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:border-gray-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Back
          </button>

          <div className="flex gap-2">
            <button
              onClick={() => {
                localStorage.setItem('onboarding_complete', 'true');
                navigate('/dashboard');
              }}
              className="px-6 py-3 text-gray-600 hover:text-gray-700 font-medium"
            >
              Skip
            </button>
            <button
              onClick={handleNext}
              disabled={loading}
              className="px-8 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {loading ? 'Saving...' : currentStep === STEPS.length ? 'Get Started! 🚀' : 'Next →'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
