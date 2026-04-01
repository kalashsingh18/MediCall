import React, { useEffect, useState } from 'react';
import { Users, CalendarDays, Activity, ReceiptIndianRupee } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data } = await api.get('/dashboard/stats');
        setStats(data);
      } catch (err) {
        toast.error('Failed to load dashboard stats');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading || !stats) return <div className="spinner"></div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Overview of today's clinic performance.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
        <div className="stat-card">
          <div className="stat-icon blue"><CalendarDays /></div>
          <div>
            <div className="stat-value">{stats.today.total_appointments}</div>
            <div className="stat-label">Appointments Today</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green"><Users /></div>
          <div>
            <div className="stat-value">{stats.today.patients_seen}</div>
            <div className="stat-label">Patients Seen</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon yellow"><Activity /></div>
          <div>
            <div className="stat-value">{stats.today.pending}</div>
            <div className="stat-label">Waiting in Queue</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple"><ReceiptIndianRupee /></div>
          <div>
            <div className="stat-value">₹{stats.today.revenue.toLocaleString('en-IN')}</div>
            <div className="stat-label">Today's Revenue</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Weekly Revenue Trend</h2>
        </div>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <AreaChart data={stats.weekly} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis tickFormatter={(val) => `₹${val}`} stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <Tooltip 
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px' }}
                itemStyle={{ color: 'var(--primary)' }}
                formatter={(value) => [`₹${value}`, 'Revenue']}
              />
              <Area type="monotone" dataKey="revenue" stroke="var(--primary)" strokeWidth={3} fillOpacity={1} fill="url(#colorRev)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
