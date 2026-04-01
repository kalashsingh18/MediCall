import React, { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function Appointments() {
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [currentAppointmentId, setCurrentAppointmentId] = useState(null);

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [formData, setFormData] = useState({ patient_id: '', doctor_id: '', appointment_date: new Date().toISOString().split('T')[0], slot_time: '', reason: '', is_walk_in: false });
  
  // Block Slot state
  const [showBlockModal, setShowBlockModal] = useState(false);
  const [blockData, setBlockData] = useState({ doctor_id: '', date: new Date().toISOString().split('T')[0], slot_time: '', reason: '' });

  // New Patient state
  const [newPatient, setNewPatient] = useState({ name: '', phone: '', dob: '', gender: 'M', blood_group: 'O+' });

  const predefinedSlots = [
    '09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM', 
    '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM',
    '04:00 PM', '04:30 PM', '05:00 PM', '05:30 PM',
    '06:00 PM', '06:30 PM', '07:00 PM', '07:30 PM'
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [apptRes, patsRes, docsRes] = await Promise.all([
        api.get('/appointments'),
        api.get('/patients'),
        api.get('/doctors')
      ]);
      setAppointments(apptRes.data);
      setPatients(patsRes.data);
      setDoctors(docsRes.data);
    } catch (err) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (appt) => {
    setIsEditing(true);
    setCurrentAppointmentId(appt.id);
    setFormData({
      patient_id: appt.patient_id,
      doctor_id: appt.doctor_id,
      appointment_date: appt.appointment_date,
      slot_time: appt.slot_time || '',
      reason: appt.reason || '',
      is_walk_in: appt.is_walk_in
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) return;
    try {
      await api.delete(`/appointments/${id}`);
      toast.success('Appointment cancelled');
      fetchData();
    } catch (err) {
      toast.error('Failed to cancel appointment');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.is_walk_in && !formData.slot_time) {
      toast.error('Please select a time slot or mark as Walk-in');
      return;
    }
    
    const payload = { ...formData, slot_time: formData.slot_time || null };
    
    try {
      if (isEditing) {
        await api.put(`/appointments/${currentAppointmentId}`, payload);
        toast.success('Appointment updated');
      } else {
        await api.post('/appointments', payload);
        toast.success('Appointment booked');
      }
      setShowModal(false);
      setIsEditing(false);
      setCurrentAppointmentId(null);
      fetchData();
    } catch (err) {
      toast.error(isEditing ? 'Failed to update appointment' : 'Failed to book appointment');
    }
  };

  const openNewModal = () => {
    setIsEditing(false);
    setFormData({ patient_id: '', doctor_id: '', appointment_date: new Date().toISOString().split('T')[0], slot_time: '', reason: '', is_walk_in: false });
    setShowModal(true);
  };

  const [availableSlots, setAvailableSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  useEffect(() => {
    if (formData.doctor_id && formData.appointment_date) {
      fetchAvailableSlots();
    }
  }, [formData.doctor_id, formData.appointment_date]);

  const fetchAvailableSlots = async () => {
    setLoadingSlots(true);
    try {
      const res = await api.get(`/doctors/${formData.doctor_id}/available-slots`, {
        params: { date: formData.appointment_date }
      });
      setAvailableSlots(res.data);
    } catch (err) {
      toast.error('Failed to fetch available slots');
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleBlockSlot = async () => {
    if (!blockData.doctor_id || !blockData.date || !blockData.slot_time) {
      toast.error('Please fill all fields');
      return;
    }
    try {
      await api.post(`/doctors/${blockData.doctor_id}/block-slot`, blockData);
      toast.success('Slot blocked successfully');
      setShowBlockModal(false);
      setBlockData({ doctor_id: '', date: new Date().toISOString().split('T')[0], slot_time: '', reason: '' });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to block slot');
    }
  };

  const handleCreatePatient = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/patients', newPatient);
      toast.success('Patient registered successfully');
      setPatients([...patients, res.data]);
      setFormData({...formData, patient_id: res.data.id});
      setShowPatientModal(false);
    } catch (err) {
      toast.error('Failed to create patient');
    }
  };

  const getStatusBadge = (status) => {
    const map = {
      scheduled: { cls: 'badge-blue', label: 'Scheduled' },
      arrived: { cls: 'badge-yellow', label: 'Waiting' },
      in_consultation: { cls: 'badge-purple', label: 'In Consult' },
      done: { cls: 'badge-green', label: 'Done' },
      no_show: { cls: 'badge-gray', label: 'No Show' },
      cancelled: { cls: 'badge-red', label: 'Cancelled' }
    };
    const s = map[status] || map.scheduled;
    return <span className={`badge ${s.cls}`}>{s.label}</span>;
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Appointments</h1>
          <p className="page-subtitle">Manage all active and upcoming appointments</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-secondary" onClick={() => setShowBlockModal(true)}>
            Block Slot
          </button>
          <button className="btn btn-primary" onClick={openNewModal}>
            <Plus /> Book Appointment
          </button>
        </div>
      </div>

      {showBlockModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">Block Doctor Slot</h2>
              <button className="modal-close" onClick={() => setShowBlockModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Doctor</label>
                <select className="form-select" value={blockData.doctor_id} onChange={e => setBlockData({...blockData, doctor_id: e.target.value})}>
                  <option value="">-- Select Doctor --</option>
                  {doctors.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input type="date" className="form-input" value={blockData.date} onChange={e => setBlockData({...blockData, date: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Time Slot</label>
                  <select className="form-select" value={blockData.slot_time} onChange={e => setBlockData({...blockData, slot_time: e.target.value})}>
                    <option value="">-- Select Slot --</option>
                    {predefinedSlots.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Reason (Optional)</label>
                <input type="text" className="form-input" placeholder="e.g. Lunch or Personal Leave" value={blockData.reason} onChange={e => setBlockData({...blockData, reason: e.target.value})} />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowBlockModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleBlockSlot}>Block Now</button>
            </div>
          </div>
        </div>
      )}

      <div className="card table-wrapper">
        {loading ? <div className="spinner"></div> : (
          <table>
            <thead>
              <tr>
                <th>Token</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Date / Time</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {appointments.length === 0 ? (
                <tr><td colSpan="7" style={{textAlign:'center', padding:'30px', color:'var(--text-muted)'}}>No appointments found.</td></tr>
              ) : (
                appointments.map(appt => {
                  const p = patients.find(x => x.id === appt.patient_id);
                  const d = doctors.find(x => x.id === appt.doctor_id);
                  return (
                    <tr key={appt.id}>
                      <td><span style={{fontWeight:700,color:'var(--text)'}}>#{appt.token_number}</span></td>
                      <td>
                        <div style={{fontWeight:600}}>{p?.name || 'Unknown'}</div>
                        <div style={{fontSize:12, color:'var(--text-muted)'}}>{p?.phone} • {appt.is_walk_in ? 'Walk-in' : 'Booked'}</div>
                      </td>
                      <td>{d?.name || 'Unknown'}</td>
                      <td>
                        <div>{appt.appointment_date}</div>
                        <div style={{fontSize:12, color:'var(--text-muted)'}}>{appt.slot_time || 'Queue'}</div>
                      </td>
                      <td>{appt.reason || '-'}</td>
                      <td>{getStatusBadge(appt.status)}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 8 }}>
                          <button className="btn-icon" title="Edit/Reschedule" onClick={() => handleEdit(appt)}>
                            <Edit2 size={16} />
                          </button>
                          <button className="btn-icon" title="Cancel Appointment" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(appt.id)}>
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">{isEditing ? 'Edit Appointment' : 'Book Appointment'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <label className="form-label" style={{marginBottom:0}}>Select Patient</label>
                    <button type="button" onClick={() => setShowPatientModal(true)} style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}><Plus size={14}/> New Patient</button>
                  </div>
                  <select className="form-select" required value={formData.patient_id} onChange={e => setFormData({...formData, patient_id: e.target.value})} disabled={isEditing}>
                    <option value="">-- Search Patient --</option>
                    {patients.map(p => <option key={p.id} value={p.id}>{p.name} ({p.phone})</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Select Doctor</label>
                  <select className="form-select" required value={formData.doctor_id} onChange={e => setFormData({...formData, doctor_id: e.target.value})}>
                    <option value="">-- Select Doctor --</option>
                    {doctors.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Date</label>
                    <input type="date" className="form-input" required value={formData.appointment_date} onChange={e => setFormData({...formData, appointment_date: e.target.value})} />
                  </div>
                  <div className="form-group" style={{ display: 'flex', alignItems: 'center', paddingTop: '28px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                      <input type="checkbox" checked={formData.is_walk_in} onChange={e => {
                        setFormData({...formData, is_walk_in: e.target.checked, slot_time: e.target.checked ? '' : formData.slot_time})
                      }} />
                      <span>Walk-in Patient</span>
                    </label>
                  </div>
                </div>

                {!formData.is_walk_in && (
                  <div className="form-group">
                    <label className="form-label">Available Slots</label>
                    {loadingSlots ? (
                      <div className="spinner-small">Loading slots...</div>
                    ) : (
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {availableSlots.length === 0 ? (
                          <p style={{fontSize:12, color:'var(--danger)'}}>No slots available for this date/doctor.</p>
                        ) : (
                          availableSlots.map(slot => (
                            <div 
                              key={slot} 
                              onClick={() => setFormData({...formData, slot_time: slot})}
                              style={{
                                padding: '6px 12px', 
                                borderRadius: '20px', 
                                fontSize: 12, 
                                fontWeight: 600,
                                cursor: 'pointer',
                                background: formData.slot_time === slot ? 'var(--primary)' : 'var(--bg)',
                                color: formData.slot_time === slot ? 'white' : 'var(--text-secondary)',
                                border: formData.slot_time === slot ? '1px solid var(--primary)' : '1px solid var(--border)'
                              }}
                            >
                              {slot}
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                )}
                <div className="form-group" style={{marginBottom:0}}>
                  <label className="form-label">Reason for visit</label>
                  <input type="text" className="form-input" placeholder="e.g. Fever and cough" value={formData.reason} onChange={e => setFormData({...formData, reason: e.target.value})} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">{isEditing ? 'Update Appointment' : 'Book Now'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
      {showPatientModal && (
        <div className="modal-overlay" style={{ zIndex: 1100 }}>
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">Quick Register Patient</h2>
              <button className="modal-close" onClick={() => setShowPatientModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreatePatient}>
              <div className="modal-body">
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input type="text" className="form-input" required value={newPatient.name} onChange={e => setNewPatient({...newPatient, name: e.target.value})} placeholder="e.g. Ramesh Kumar" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Phone Number</label>
                    <input type="text" className="form-input" required value={newPatient.phone} onChange={e => setNewPatient({...newPatient, phone: e.target.value})} placeholder="10-digit number" />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Date of Birth</label>
                    <input type="date" className="form-input" required value={newPatient.dob} onChange={e => setNewPatient({...newPatient, dob: e.target.value})} />
                  </div>
                  <div className="form-group" style={{ display: 'flex', gap: 12, paddingTop: 24 }}>
                    <label style={{display: 'flex', alignItems: 'center', gap: 4}}><input type="radio" checked={newPatient.gender==='M'} onChange={() => setNewPatient({...newPatient, gender: 'M'})} /> Male</label>
                    <label style={{display: 'flex', alignItems: 'center', gap: 4}}><input type="radio" checked={newPatient.gender==='F'} onChange={() => setNewPatient({...newPatient, gender: 'F'})} /> Female</label>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowPatientModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save & Select</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
