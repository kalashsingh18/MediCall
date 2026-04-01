import React, { useEffect, useState } from 'react';
import { Building2, Phone, Save, Mail } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function Settings() {
  const [formData, setFormData] = useState({
    name: 'MediCall Central Clinic',
    address: '123 Health Ave, Mumbai, 400001',
    phone: '+91 9876543210',
    gstin: '22AAAAA0000A1Z5',
    working_hours: { open: '09:00', close: '21:00' }
  });

  const [loading, setLoading] = useState(false);

  // In a real app, this would fetch the clinic ID 1
  useEffect(() => {
    // Mock fetch for now, or could fetch from real GET /clinic/1
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Mock save or real PUT
      await new Promise(r => setTimeout(r, 600)); 
      toast.success('Clinic profile updated successfully');
    } catch (err) {
      toast.error('Failed to update settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Clinic Settings</h1>
          <p className="page-subtitle">Manage clinic profile, branding, and operational details.</p>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title" style={{ marginBottom: 20 }}>General Profile</h2>
        <form onSubmit={handleSave}>
          <div className="form-group">
            <label className="form-label">Clinic Name</label>
            <div className="search-box">
              <Building2 />
              <input type="text" className="form-input" style={{width:'100%'}} value={formData.name} onChange={e=>setFormData({...formData, name:e.target.value})} required/>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Address</label>
            <textarea className="form-textarea" rows="2" value={formData.address} onChange={e=>setFormData({...formData, address:e.target.value})}></textarea>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Contact Number</label>
              <div className="search-box">
                <Phone />
                <input type="text" className="form-input" style={{width:'100%'}} value={formData.phone} onChange={e=>setFormData({...formData, phone:e.target.value})} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">GSTIN / Tax ID</label>
               <div className="search-box">
                <Mail />
                <input type="text" className="form-input" style={{width:'100%'}} value={formData.gstin} onChange={e=>setFormData({...formData, gstin:e.target.value})} />
              </div>
            </div>
          </div>

          <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginTop: 24, marginBottom: 16, textTransform: 'uppercase' }}>Operating Hours</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Opening Time</label>
              <input type="time" className="form-input" value={formData.working_hours.open} onChange={e=>setFormData({...formData, working_hours: {...formData.working_hours, open: e.target.value}})} />
            </div>
             <div className="form-group">
              <label className="form-label">Closing Time</label>
              <input type="time" className="form-input" value={formData.working_hours.close} onChange={e=>setFormData({...formData, working_hours: {...formData.working_hours, close: e.target.value}})} />
            </div>
          </div>

          <div style={{ marginTop: 32, paddingTop: 20, borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <Save /> {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
