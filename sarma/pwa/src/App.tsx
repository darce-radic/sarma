import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import MobileNav from './components/MobileNav';
import './components/MobileOptimized.css';

// Pages
import Settings from './pages/Settings';
import Subscription from './pages/Subscription';
import Analytics from './pages/Analytics';
import Admin from './pages/Admin';
import Onboarding from './pages/Onboarding';

// Placeholder components for other pages (to be built)
const Login = () => <div className="min-h-screen flex items-center justify-center bg-gray-50"><div className="text-2xl font-bold text-gray-900">Login Page (Coming Soon)</div></div>;
const Dashboard = () => <div className="min-h-screen flex items-center justify-center bg-gray-50"><div className="text-2xl font-bold text-gray-900">Dashboard (Coming Soon)</div></div>;
const Meals = () => <div className="min-h-screen flex items-center justify-center bg-gray-50"><div className="text-2xl font-bold text-gray-900">Meals Page (Coming Soon)</div></div>;
const Recipes = () => <div className="min-h-screen flex items-center justify-center bg-gray-50"><div className="text-2xl font-bold text-gray-900">Recipes Page (Coming Soon)</div></div>;

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Layout wrapper with mobile nav
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <>
      <div className="min-h-screen bg-gray-50 mobile-content safe-bottom">
        {children}
      </div>
      <MobileNav />
    </>
  );
};

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/onboarding" element={<Onboarding />} />
      
      {/* Protected Routes with Layout */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Dashboard />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Settings />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/subscription"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Subscription />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Analytics />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/meals"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Meals />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/recipes"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Recipes />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Admin />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      
      {/* Default Route */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
