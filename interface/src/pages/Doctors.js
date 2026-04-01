import React, { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function Doctors() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [currentDoctorId, setCurrentDoctorId] = useState(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '', email: '', password: '', 
    specialization: '', degree: 'MBBS', consultation_fee: 500
  });

  useEffect(() => {
    fetchDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      const res = await api.get('/doctors');
      setDoctors(res.data);
    } catch (err) {
      toast.error('Failed to load doctors');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (doc) => {
    setIsEditing(true);
    setCurrentDoctorId(doc.id);
    setFormData({
      name: doc.name,
      email: '', // Don't show password or email change in this simple edit
      password: '',
      specialization: doc.specialization,
      degree: doc.degree,
      consultation_fee: doc.consultation_fee
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to deactivate this doctor? They will no longer appear in the booking list.')) return;
    try {
      await api.delete(`/doctors/${id}`);
      toast.success('Doctor deactivated');
      fetchDoctors();
    } catch (err) {
      toast.error('Failed to deactivate doctor');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEditing) {
        // Only update specific doctor fields, not the user account in this simplified version
        const { email, password, ...updateData } = formData;
        await api.put(`/doctors/${currentDoctorId}`, updateData);
        toast.success('Doctor profile updated');
      } else {
        await api.post('/doctors', formData);
        toast.success('Doctor added successfully');
      }
      setShowModal(false);
      setIsEditing(false);
      setCurrentDoctorId(null);
      fetchDoctors();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Operation failed');
    }
  };

  const openNewModal = () => {
    setIsEditing(false);
    setFormData({ name: '', email: '', password: '', specialization: '', degree: 'MBBS', consultation_fee: 500 });
    setShowModal(true);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Clinic Doctors</h1>
          <p className="page-subtitle">Manage doctor profiles and consultation fees</p>
        </div>
        <button className="btn btn-primary" onClick={openNewModal}>
          <Plus /> Add Doctor
        </button>
      </div>

      {loading ? <div className="spinner"></div> : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
          {doctors.map(doc => (
            <div key={doc.id} className="doctor-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div className="doctor-avatar">{doc.name.charAt(0)}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text)' }}>Dr. {doc.name}</div>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button className="btn-icon" style={{ padding: 4 }} title="Edit" onClick={() => handleEdit(doc)}>
                        <Edit2 size={14} />
                      </button>
                      <button className="btn-icon" style={{ padding: 4, color: 'var(--danger)' }} title="Deactivate" onClick={() => handleDelete(doc.id)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--primary)', fontWeight: 600 }}>{doc.specialization} • {doc.degree}</div>
                </div>
              </div>
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Consultation Fee</div>
                  <div style={{ fontWeight: 600 }}>₹{doc.consultation_fee?.toFixed(2) || '0.00'}</div>
                </div>
              </div>
            </div>
          ))}
          {doctors.length === 0 && <div className="empty-state" style={{gridColumn:'1/-1'}}>No doctors registered yet.</div>}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">{isEditing ? 'Edit Doctor Profile' : 'Add New Doctor'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                {!isEditing && (
                  <div className="form-group" style={{background:'var(--primary-light)', padding: 12, borderRadius: 'var(--radius)'}}>
                    <p style={{fontSize:12, color:'var(--primary-dark)', margin:0}}>Note: This creates a login account for the doctor.</p>
                  </div>
                )}

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input type="text" className="form-input" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="e.g. Rahul Sharma" />
                  </div>
                  {!isEditing && (
                    <div className="form-group">
                      <label className="form-label">Login Email</label>
                      <input type="email" className="form-input" required value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                    </div>
                  )}
                </div>
                
                {!isEditing && (
                  <div className="form-group">
                    <label className="form-label">Temporary Password</label>
                    <input type="password" className="form-input" required value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
                  </div>
                )}

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Specialization</label>
                    <input type="text" className="form-input" required value={formData.specialization} onChange={e => setFormData({...formData, specialization: e.target.value})} placeholder="e.g. Cardiologist" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Consultation Fee (₹)</label>
                    <input type="number" className="form-input" required value={formData.consultation_fee} onChange={e => setFormData({...formData, consultation_fee: Number(e.target.value)})} min="0" />
                  </div>
                </div>

                <div className="form-group" style={{marginBottom:0}}>
                  <label className="form-label">Degrees</label>
                  <input type="text" className="form-input" required value={formData.degree} onChange={e => setFormData({...formData, degree: e.target.value})} placeholder="MBBS, MD" />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">{isEditing ? 'Update Profile' : 'Create Account'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
