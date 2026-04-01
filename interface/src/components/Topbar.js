import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon, Bell, LogOut } from 'lucide-react';

export default function Topbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="topbar-title">Welcome back, {user?.name?.split(' ')[0] || 'Doc'}</div>
        <div className="topbar-sub">{new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</div>
      </div>

      <div className="topbar-right">
        <button className="topbar-icon-btn" onClick={toggleTheme} title="Toggle Dark Mode">
          {theme === 'dark' ? <Sun /> : <Moon />}
        </button>
        <button className="topbar-icon-btn" title="Notifications">
          <Bell />
        </button>
        <button className="topbar-icon-btn" onClick={logout} title="Logout" style={{ color: 'var(--danger)' }}>
          <LogOut />
        </button>
        <div className="user-avatar">
          {user?.name?.charAt(0).toUpperCase() || 'U'}
        </div>
      </div>
    </header>
  );
}
