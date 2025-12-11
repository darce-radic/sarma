import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

interface SubscriptionTier {
  id: string;
  name: string;
  price: number;
  interval: 'month' | 'year';
  features: string[];
  recommended?: boolean;
  stripePriceId: string;
}

const SUBSCRIPTION_TIERS: SubscriptionTier[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    interval: 'month',
    stripePriceId: '',
    features: [
      '50 AI requests per month',
      'Gemini Flash AI only',
      'Basic meal tracking',
      'Recipe search',
      'Community support',
      'Standard features',
    ],
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 9.99,
    interval: 'month',
    recommended: true,
    stripePriceId: 'price_premium_monthly',
    features: [
      '✨ Unlimited AI requests',
      '🚀 GPT-4 Vision access',
      '🎯 Personalized meal plans',
      '📊 Advanced analytics',
      '🛒 Grocery list generation',
      '⚡ Priority support',
      'All Free features',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 19.99,
    interval: 'month',
    stripePriceId: 'price_pro_monthly',
    features: [
      '🌟 Everything in Premium',
      '🔌 API access',
      '📈 Business analytics',
      '🎨 White-label options',
      '👥 Team collaboration',
      '🤝 Dedicated support',
      '🔧 Custom integrations',
    ],
  },
];

interface Usage {
  requests_this_month: number;
}

export default function Subscription() {
  const navigate = useNavigate();
  const { token } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [currentTier, setCurrentTier] = useState<string>('free');
  const [usage, setUsage] = useState<Usage | null>(null);

  const fetchSubscriptionStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/subscriptions/current', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentTier(data.tier || 'free');
      }
    } catch (error) {
      console.error('Failed to fetch subscription:', error);
    }
  }, [token]);

  const fetchUsage = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/subscriptions/usage', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsage(data);
      }
    } catch (error) {
      console.error('Failed to fetch usage:', error);
    }
  }, [token]);

  useEffect(() => {
    fetchSubscriptionStatus();
    fetchUsage();
  }, [fetchSubscriptionStatus, fetchUsage]);

  const handleSubscribe = async (tier: SubscriptionTier) => {
    if (tier.id === 'free') {
      // Handle downgrade to free
      if (confirm('Are you sure you want to downgrade to Free? You will lose premium features.')) {
        try {
          const response = await fetch('http://localhost:8000/api/v1/subscriptions/cancel', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (response.ok) {
            alert('Subscription cancelled. You are now on the Free tier.');
            fetchSubscriptionStatus();
          }
        } catch (error) {
          alert('Failed to cancel subscription');
        }
      }
      return;
    }

    setLoading(true);

    try {
      // Create Stripe checkout session
      const response = await fetch('http://localhost:8000/api/v1/subscriptions/checkout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          price_id: tier.stripePriceId,
          success_url: `${window.location.origin}/subscription/success`,
          cancel_url: `${window.location.origin}/subscription`,
        }),
      });

      const data = await response.json();

      if (data.checkout_url) {
        // Redirect to Stripe Checkout
        window.location.href = data.checkout_url;
      } else {
        throw new Error('No checkout URL returned');
      }
    } catch (error) {
      console.error('Failed to create checkout session:', error);
      alert('Failed to start checkout. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/subscriptions/portal', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          return_url: `${window.location.origin}/subscription`,
        }),
      });

      const data = await response.json();

      if (data.portal_url) {
        window.location.href = data.portal_url;
      }
    } catch (error) {
      alert('Failed to open customer portal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-green-600 hover:text-green-700 flex items-center gap-2 mb-4"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600">
            Unlock the full power of AI-driven health insights
          </p>
        </div>

        {/* Current Usage (if on free tier) */}
        {currentTier === 'free' && usage && (
          <div className="max-w-2xl mx-auto mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Your Usage This Month</h3>
                <span className="text-sm text-gray-600">Free Tier</span>
              </div>
              <div className="relative pt-1">
                <div className="flex mb-2 items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold inline-block text-green-600">
                      AI Requests
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-green-600">
                      {usage.requests_this_month} / 50
                    </span>
                  </div>
                </div>
                <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-green-100">
                  <div
                    style={{ width: `${(usage.requests_this_month / 50) * 100}%` }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-green-600"
                  ></div>
                </div>
              </div>
              {usage.requests_this_month >= 40 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                  {"⚠️ You're running low on requests! Upgrade to Premium for unlimited AI requests."}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
          {SUBSCRIPTION_TIERS.map(tier => (
            <div
              key={tier.id}
              className={`relative bg-white rounded-2xl shadow-xl overflow-hidden transition-transform hover:scale-105 ${
                tier.recommended ? 'ring-4 ring-green-500' : ''
              }`}
            >
              {tier.recommended && (
                <div className="absolute top-0 right-0 bg-green-500 text-white px-4 py-1 text-sm font-semibold rounded-bl-lg">
                  MOST POPULAR
                </div>
              )}

              <div className="p-8">
                {/* Tier Name */}
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                
                {/* Price */}
                <div className="mb-6">
                  <span className="text-5xl font-bold text-gray-900">${tier.price}</span>
                  <span className="text-gray-600 ml-2">/{tier.interval}</span>
                </div>

                {/* Current Tier Badge */}
                {currentTier === tier.id && (
                  <div className="mb-4 bg-green-100 text-green-800 px-4 py-2 rounded-lg text-center font-semibold">
                    ✓ Current Plan
                  </div>
                )}

                {/* Features */}
                <ul className="space-y-3 mb-8">
                  {tier.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                {currentTier === tier.id ? (
                  currentTier !== 'free' && (
                    <button
                      onClick={handleManageSubscription}
                      disabled={loading}
                      className="w-full bg-gray-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-gray-700 transition-colors disabled:bg-gray-300"
                    >
                      {loading ? 'Loading...' : 'Manage Subscription'}
                    </button>
                  )
                ) : (
                  <button
                    onClick={() => handleSubscribe(tier)}
                    disabled={loading}
                    className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
                      tier.recommended
                        ? 'bg-green-600 text-white hover:bg-green-700'
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                    } disabled:bg-gray-300 disabled:cursor-not-allowed`}
                  >
                    {loading ? 'Processing...' : tier.id === 'free' ? 'Downgrade' : 'Upgrade Now'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-lg p-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
            Frequently Asked Questions
          </h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can I change plans anytime?
              </h3>
              <p className="text-gray-600">
                Yes! You can upgrade, downgrade, or cancel your subscription at any time. Changes take effect immediately for upgrades, or at the end of your billing period for downgrades.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-gray-600">
                We accept all major credit cards (Visa, MasterCard, American Express) through our secure payment processor, Stripe.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                What happens if I exceed the free tier limit?
              </h3>
              <p className="text-gray-600">
                {"You'll receive a notification when you're close to your limit. Once you reach 50 requests, you'll be prompted to upgrade to continue using AI features."}
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Is there a free trial for Premium?
              </h3>
              <p className="text-gray-600">
                The Free tier lets you try our core features at no cost. When you upgrade to Premium, you can cancel anytime within the first 7 days for a full refund.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can I use my own API keys?
              </h3>
              <p className="text-gray-600">
                Yes! Premium and Pro users can add their own Gemini or OpenAI API keys in Settings to bypass platform limits and get truly unlimited requests.
              </p>
            </div>
          </div>
        </div>

        {/* Money-back Guarantee */}
        <div className="max-w-2xl mx-auto mt-8 text-center">
          <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 border-2 border-green-200">
            <div className="text-4xl mb-2">🛡️</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              7-Day Money-Back Guarantee
            </h3>
            <p className="text-gray-600">
                {"Try Premium or Pro risk-free. If you're not satisfied within the first 7 days, we'll refund your payment—no questions asked."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
