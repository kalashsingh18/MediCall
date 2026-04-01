import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  CalendarDays, 
  Users, 
  Stethoscope, 
  Pill, 
  ReceiptIndianRupee, 
  Activity, 
  Settings,
  Bot 
} from 'lucide-react';

export default function Sidebar() {
  const menuItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { name: 'Appointments', icon: CalendarDays, path: '/appointments' },
    { name: 'Live Queue', icon: Activity, path: '/queue' },
    { name: 'Patients', icon: Users, path: '/patients' },
    { name: 'Doctors', icon: Stethoscope, path: '/doctors' },
    { name: 'Billing', icon: ReceiptIndianRupee, path: '/billing' },
    { name: 'Reports', icon: Pill, path: '/reports' },
    { name: 'AI Logs', icon: Bot, path: '/ai-logs' },
    { name: 'Settings', icon: Settings, path: '/settings' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-text">Medi<span>Call</span></div>
        <div className="logo-sub">Clinic Management</div>
      </div>
      
      <div className="sidebar-nav">
        <div className="sidebar-section-label">Main Menu</div>
        {menuItems.map((item) => (
          <NavLink 
            key={item.name}
            to={item.path} 
            className={({ isActive }) => `sidebar-item ${isActive ? 'active' : ''}`}
          >
            <item.icon strokeWidth={2.5} />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </div>
    </aside>
  );
}
