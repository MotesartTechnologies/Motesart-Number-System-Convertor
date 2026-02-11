import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X, User, LogOut, Crown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Motesart Logo URL (C → 1 concept)
const MOTESART_LOGO = "https://customer-assets.emergentagent.com/job_music-to-numbers/artifacts/eqmmw6fl_2316F097-7806-4D1F-AB36-BB5FF560800D.png";

const NAV_ITEMS = [
  { name: "Home", path: "/" },
  { name: "Text Converter", path: "/converter" },
  { name: "Dashboard", path: "/dashboard" },
  { name: "Learn", path: "/learn" },
];

// Helper to get display avatar for a user
const getUserAvatar = (user) => {
  if (!user) return null;
  // Priority: computed_avatar > avatar_url > picture > fallback
  return user.computed_avatar || user.avatar_url || user.picture || null;
};

// Helper to get display name for a user
const getUserDisplayName = (user) => {
  if (!user) return "User";
  return user.display_name || user.username || user.name || "User";
};

// Helper to get initials for avatar fallback
const getUserInitials = (user) => {
  if (!user) return "U";
  const name = user.display_name || user.username || user.name || "";
  return name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase() || "U";
};

export const Navbar = ({ user, onLogout }) => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/converter';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const avatarUrl = getUserAvatar(user);
  const displayName = getUserDisplayName(user);
  const initials = getUserInitials(user);
  const isFounder = user?.is_founder || user?.username === "Motesart";

  return (
    <nav className="sticky top-0 z-50 bg-sonic-surface/80 backdrop-blur-xl border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo with Motesart image */}
          <Link to="/" className="flex items-center gap-3" data-testid="nav-logo">
            <img 
              src={MOTESART_LOGO} 
              alt="Motesart" 
              className="w-9 h-9 rounded-lg object-cover"
            />
            <span className="font-heading font-semibold text-lg">Motesart Converter</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname === item.path
                    ? "text-white bg-slate-800"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
                data-testid={`nav-${item.name.toLowerCase()}`}
              >
                {item.name}
              </Link>
            ))}
          </div>

          {/* Auth Section */}
          <div className="flex items-center gap-3">
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="gap-2 relative" data-testid="user-menu-btn">
                    <div className="relative">
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={avatarUrl} />
                        <AvatarFallback className="bg-neon-indigo/20 text-neon-indigo text-sm">
                          {initials}
                        </AvatarFallback>
                      </Avatar>
                      {/* Crown icon for founder */}
                      {isFounder && (
                        <Crown 
                          className="absolute -top-2 -right-1 w-4 h-4 text-yellow-400 fill-yellow-400" 
                          data-testid="founder-crown"
                        />
                      )}
                    </div>
                    <span className="hidden sm:inline text-sm text-slate-300">
                      {displayName}
                    </span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <div className="px-2 py-1.5">
                    <div className="flex items-center gap-2">
                      <Avatar className="w-6 h-6">
                        <AvatarImage src={avatarUrl} />
                        <AvatarFallback className="bg-neon-indigo/20 text-neon-indigo text-xs">
                          {initials}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate flex items-center gap-1">
                          {displayName}
                          {isFounder && <Crown className="w-3 h-3 text-yellow-400 fill-yellow-400" />}
                        </p>
                        <p className="text-xs text-slate-400 truncate">{user.email}</p>
                      </div>
                    </div>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/account">
                      <User className="w-4 h-4 mr-2" />
                      Account
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={onLogout} data-testid="logout-btn">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login">
                  <Button
                    variant="ghost"
                    className="text-slate-400 hover:text-white"
                    data-testid="nav-signin-btn"
                  >
                    Sign In
                  </Button>
                </Link>
                <Button
                  onClick={handleLogin}
                  className="bg-neon-indigo hover:bg-indigo-500 text-white rounded-full px-5"
                  data-testid="nav-signup-btn"
                >
                  Get Started
                </Button>
              </div>
            )}

            {/* Mobile menu button */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Nav */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-slate-800">
            <div className="flex flex-col gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-3 rounded-lg text-sm font-medium ${
                    location.pathname === item.path
                      ? "text-white bg-slate-800"
                      : "text-slate-400"
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};
