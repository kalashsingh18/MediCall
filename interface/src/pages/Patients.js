import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Phone, Droplet, User as UserIcon, Edit2, Trash2 } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentPatientId, setCurrentPatientId] = useState(null);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '', phone: '', age: '', gender: 'male', blood_group: 'unknown', address: ''
  });

  const fetchPatients = useCallback(async () => {
    try {
      const res = await api.get(`/patients${search ? `?search=${search}` : ''}`);
      setPatients(res.data);
    } catch (err) {
      toast.error('Failed to load patients');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  const handleEdit = (p, e) => {
    e.stopPropagation();
    setIsEditing(true);
    setCurrentPatientId(p.id);
    setFormData({
      name: p.name,
      phone: p.phone,
      gender: p.gender || 'male',
      blood_group: p.blood_group || 'unknown',
      address: p.address || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this patient? This will also remove all their medical records.')) return;
    
    try {
      await api.delete(`/patients/${id}`);
      toast.success('Patient deleted');
      fetchPatients();
    } catch (err) {
      toast.error('Failed to delete patient');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isEditing) {
        await api.put(`/patients/${currentPatientId}`, formData);
        toast.success('Patient details updated');
      } else {
        const res = await api.post('/patients', formData);
        toast.success('Patient registered');
        navigate(`/patients/${res.data.id}`);
      }
      setShowModal(false);
      setIsEditing(false);
      setCurrentPatientId(null);
      fetchPatients();
    } catch (err) {
      toast.error(isEditing ? 'Failed to update patient' : 'Failed to register patient');
    }
  };

  const openNewModal = () => {
    setIsEditing(false);
    setFormData({ name: '', phone: '', age: '', gender: 'male', blood_group: 'unknown', address: '' });
    setShowModal(true);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Patients Directory</h1>
          <p className="page-subtitle">Search, view, and register clinic patients</p>
        </div>
        <button className="btn btn-primary" onClick={openNewModal}>
          <Plus /> New Patient
        </button>
      </div>

      <div className="card" style={{ marginBottom: 24, padding: '16px 24px' }}>
        <div className="search-box">
          <Search />
          <input 
            type="text" 
            className="form-input" 
            placeholder="Search by name or phone number..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="card table-wrapper">
        {loading ? <div className="spinner"></div> : (
          <table>
            <thead>
              <tr>
                <th>Patient Name</th>
                <th>Contact</th>
                <th>Gender / Blood</th>
                <th>Registered On</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.length === 0 ? (
                <tr><td colSpan="5" style={{textAlign:'center', padding:'40px', color:'var(--text-muted)'}}>No patients found.</td></tr>
              ) : (
                patients.map(p => (
                  <tr key={p.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/patients/${p.id}`)}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                          <UserIcon size={20} />
                        </div>
                        <span style={{ fontWeight: 600 }}>{p.name}</span>
                      </div>
                    </td>
                    <td>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Phone size={14} color="var(--text-muted)" /> {p.phone}</span>
                    </td>
                    <td>
                      <div>{p.gender ? p.gender.charAt(0).toUpperCase() + p.gender.slice(1) : '-'}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                        <Droplet size={12} color="var(--danger)" /> {p.blood_group !== 'unknown' ? p.blood_group : 'Not specified'}
                      </div>
                    </td>
                    <td>{new Date(p.created_at).toLocaleDateString('en-IN')}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button className="btn-icon" title="Edit" onClick={(e) => handleEdit(p, e)}>
                          <Edit2 size={16} />
                        </button>
                        <button className="btn-icon" title="Delete" style={{ color: 'var(--danger)' }} onClick={(e) => handleDelete(p.id, e)}>
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">{isEditing ? 'Edit Patient Details' : 'Register New Patient'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input type="text" className="form-input" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Phone Number</label>
                  <input type="tel" className="form-input" required value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} />
                </div>
                <div className="form-row" style={{ gridTemplateColumns: '1fr 1fr' }}>
                  <div className="form-group">
                    <label className="form-label">Gender</label>
                    <select className="form-select" value={formData.gender} onChange={e => setFormData({...formData, gender: e.target.value})}>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Blood Group</label>
                    <select className="form-select" value={formData.blood_group} onChange={e => setFormData({...formData, blood_group: e.target.value})}>
                      <option value="unknown">Unknown</option>
                      <option value="A+">A+</option><option value="A-">A-</option>
                      <option value="B+">B+</option><option value="B-">B-</option>
                      <option value="O+">O+</option><option value="O-">O-</option>
                      <option value="AB+">AB+</option><option value="AB-">AB-</option>
                    </select>
                  </div>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Address</label>
                  <textarea className="form-textarea" rows="2" value={formData.address} onChange={e => setFormData({...formData, address: e.target.value})}></textarea>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">{isEditing ? 'Update Patient' : 'Save Patient'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
