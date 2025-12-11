import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

interface NavItem {
  path: string;
  label: string;
  icon: string;
  requiresAuth?: boolean;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: 'Home', icon: '🏠', requiresAuth: true },
  { path: '/meals', label: 'Meals', icon: '🍽️', requiresAuth: true },
  { path: '/recipes', label: 'Recipes', icon: '🍳', requiresAuth: true },
  { path: '/analytics', label: 'Stats', icon: '📊', requiresAuth: true },
  { path: '/settings', label: 'Settings', icon: '⚙️', requiresAuth: true },
];

export default function MobileNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = () => {
    logout();
    navigate('/login');
    setIsMenuOpen(false);
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      {/* Bottom Navigation Bar (Mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 safe-area-inset-bottom">
        <div className="flex items-center justify-around h-16">
          {navItems.slice(0, 4).map((item) => {
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                  active
                    ? 'text-green-600'
                    : 'text-gray-500 active:text-green-600'
                }`}
              >
                <span className="text-2xl mb-1">{item.icon}</span>
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
          
          {/* More Menu Button */}
          <button
            onClick={() => setIsMenuOpen(true)}
            className="flex flex-col items-center justify-center flex-1 h-full text-gray-500 active:text-green-600 transition-colors"
          >
            <span className="text-2xl mb-1">☰</span>
            <span className="text-xs font-medium">More</span>
          </button>
        </div>
      </nav>

      {/* Slide-out Menu */}
      {isMenuOpen && (
        <>
          {/* Backdrop */}
          <div
            className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={() => setIsMenuOpen(false)}
          />

          {/* Menu Panel */}
          <div className="md:hidden fixed top-0 right-0 bottom-0 w-80 max-w-[85vw] bg-white z-50 shadow-xl overflow-y-auto">
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-green-700 p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">Menu</h2>
                <button
                  onClick={() => setIsMenuOpen(false)}
                  className="text-white text-3xl leading-none"
                >
                  ×
                </button>
              </div>
              
              {user && (
                <div>
                  <p className="text-sm opacity-90">Welcome back,</p>
                  <p className="font-semibold text-lg">{user.full_name || user.email}</p>
                  {user.subscription_tier && (
                    <span className="inline-block mt-2 px-3 py-1 bg-white/20 rounded-full text-xs font-medium">
                      {user.subscription_tier.toUpperCase()} MEMBER
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Menu Items */}
            <div className="p-4">
              {/* All Navigation Items */}
              <div className="mb-6">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
                  Navigation
                </h3>
                {navItems.map((item) => {
                  const active = isActive(item.path);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setIsMenuOpen(false)}
                      className={`flex items-center gap-4 px-4 py-3 rounded-lg mb-1 transition-colors ${
                        active
                          ? 'bg-green-50 text-green-700 font-semibold'
                          : 'text-gray-700 hover:bg-gray-50 active:bg-gray-100'
                      }`}
                    >
                      <span className="text-2xl">{item.icon}</span>
                      <span className="text-base">{item.label}</span>
                    </Link>
                  );
                })}
              </div>

              {/* Account Section */}
              <div className="mb-6">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
                  Account
                </h3>
                
                <Link
                  to="/subscription"
                  onClick={() => setIsMenuOpen(false)}
                  className="flex items-center gap-4 px-4 py-3 rounded-lg mb-1 text-gray-700 hover:bg-gray-50 active:bg-gray-100 transition-colors"
                >
                  <span className="text-2xl">💳</span>
                  <span className="text-base">Subscription</span>
                </Link>

                <Link
                  to="/onboarding"
                  onClick={() => setIsMenuOpen(false)}
                  className="flex items-center gap-4 px-4 py-3 rounded-lg mb-1 text-gray-700 hover:bg-gray-50 active:bg-gray-100 transition-colors"
                >
                  <span className="text-2xl">👋</span>
                  <span className="text-base">Tour</span>
                </Link>

                {user?.is_admin && (
                  <Link
                    to="/admin"
                    onClick={() => setIsMenuOpen(false)}
                    className="flex items-center gap-4 px-4 py-3 rounded-lg mb-1 text-gray-700 hover:bg-gray-50 active:bg-gray-100 transition-colors"
                  >
                    <span className="text-2xl">👨‍💼</span>
                    <span className="text-base">Admin Panel</span>
                  </Link>
                )}
              </div>

              {/* Support Section */}
              <div className="mb-6">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
                  Support
                </h3>
                
                <a
                  href="mailto:support@sarma.app"
                  className="flex items-center gap-4 px-4 py-3 rounded-lg mb-1 text-gray-700 hover:bg-gray-50 active:bg-gray-100 transition-colors"
                >
                  <span className="text-2xl">💬</span>
                  <span className="text-base">Contact Support</span>
                </a>

                <a
                  href="/help"
                  className="flex items-center gap-4 px-4 py-3 rounded-lg mb-1 text-gray-700 hover:bg-gray-50 active:bg-gray-100 transition-colors"
                >
                  <span className="text-2xl">❓</span>
                  <span className="text-base">Help Center</span>
                </a>
              </div>

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-4 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 active:bg-red-100 transition-colors font-semibold"
              >
                <span className="text-2xl">🚪</span>
                <span className="text-base">Logout</span>
              </button>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200 text-center text-sm text-gray-500">
              <p>Sarma Health Platform</p>
              <p className="text-xs mt-1">Version 1.0.0</p>
            </div>
          </div>
        </>
      )}

      {/* Add padding to content to account for bottom nav */}
      <style>{`
        body {
          padding-bottom: env(safe-area-inset-bottom, 0px);
        }
        .safe-area-inset-bottom {
          padding-bottom: env(safe-area-inset-bottom, 0px);
        }
        @media (max-width: 768px) {
          main, .main-content {
            padding-bottom: 5rem !important;
          }
        }
      `}</style>
    </>
  );
}
