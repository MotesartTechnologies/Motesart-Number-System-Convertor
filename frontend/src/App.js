import { useEffect, useRef, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import LandingPage from "@/pages/LandingPage";
import Dashboard from "@/pages/Dashboard";
import LoginPage from "@/pages/LoginPage";
import LearnPage from "@/pages/LearnPage";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Auth callback handler - processes session_id from URL fragment
const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = window.location.hash;
      const sessionId = new URLSearchParams(hash.slice(1)).get("session_id");

      if (!sessionId) {
        navigate("/", { replace: true });
        return;
      }

      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (!response.ok) {
          throw new Error("Auth failed");
        }

        const user = await response.json();
        navigate("/converter", { replace: true, state: { user } });
      } catch (error) {
        console.error("Auth error:", error);
        navigate("/", { replace: true });
      }
    };

    processAuth();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-sonic-void flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-neon-indigo border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-400">Authenticating...</p>
      </div>
    </div>
  );
};

// Protected route wrapper
const ProtectedRoute = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(
    location.state?.user ? true : null
  );
  const [user, setUser] = useState(location.state?.user || null);

  useEffect(() => {
    if (location.state?.user) {
      setIsAuthenticated(true);
      setUser(location.state.user);
      return;
    }

    const checkAuth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
          credentials: "include",
        });

        if (!response.ok) throw new Error("Not authenticated");

        const userData = await response.json();
        setIsAuthenticated(true);
        setUser(userData);
      } catch (error) {
        setIsAuthenticated(false);
        navigate("/login", { replace: true });
      }
    };

    checkAuth();
  }, [navigate, location.state]);

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-sonic-void flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-neon-indigo border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return children({ user });
};

// Main router with session_id detection
const AppRouter = () => {
  const location = useLocation();

  // Check URL fragment for session_id synchronously during render
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/learn" element={<LearnPage />} />
      <Route
        path="/converter"
        element={
          <ProtectedRoute>
            {({ user }) => <Dashboard user={user} />}
          </ProtectedRoute>
        }
      />
      {/* Keep /dashboard as alias for /converter */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            {({ user }) => <Dashboard user={user} />}
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

function App() {
  return (
    <div className="min-h-screen bg-sonic-void">
      <div className="noise-overlay" />
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
