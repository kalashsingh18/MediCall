import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { success, message } = await login(email, password);
    if (success) {
      toast.success('Welcome to MediCall!');
      navigate('/dashboard');
    } else {
      toast.error(message || 'Login failed');
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
      <div className="card" style={{ maxWidth: 420, width: '100%', padding: 40 }}>
        
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div className="logo-text" style={{ fontSize: 32, fontWeight: 800, color: 'var(--text)' }}>
            Medi<span style={{ color: 'var(--primary)' }}>Call</span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Clinic Management System</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input 
              type="email" 
              className="form-input" 
              placeholder="doc@clinic.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
          </div>
          
          <div className="form-group" style={{ marginBottom: 28 }}>
            <label className="form-label">Password</label>
            <input 
              type="password" 
              className="form-input" 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: 32, background: 'var(--bg-hover)', padding: '16px', borderRadius: 'var(--radius)', fontSize: 13, color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <CheckCircle2 size={16} color="var(--accent)" /> Smart Appointment Booking
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
             <CheckCircle2 size={16} color="var(--accent)" /> Live Token Queue
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
             <CheckCircle2 size={16} color="var(--accent)" /> GST Billing & EMR
          </div>
        </div>

      </div>
    </div>
  );
}
