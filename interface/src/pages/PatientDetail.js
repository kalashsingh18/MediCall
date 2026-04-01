import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { User, Phone, Droplet, ArrowLeft, Plus } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function PatientDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [visits, setVisits] = useState([]);
  const [activeTab, setActiveTab] = useState('visits'); // visits, prescriptions, bills
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPatientData();
  }, [id]);

  const fetchPatientData = async () => {
    try {
      const [pRes, vRes] = await Promise.all([
        api.get(`/patients/${id}`),
        api.get(`/visits/patient/${id}`)
      ]);
      setPatient(pRes.data);
      setVisits(vRes.data);
    } catch (err) {
      toast.error('Failed to load patient profile');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="spinner"></div>;
  if (!patient) return <div className="empty-state">Patient not found</div>;

  return (
    <div>
      <button className="btn btn-ghost" style={{ marginBottom: 16 }} onClick={() => navigate('/patients')}>
        <ArrowLeft /> Back to Patients
      </button>

      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 24 }}>
        <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <User size={40} />
        </div>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>{patient.name}</h1>
          <div style={{ display: 'flex', gap: 20, color: 'var(--text-secondary)', fontSize: 14 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Phone size={16}/> {patient.phone}</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Droplet size={16} color="var(--danger)"/> Blood: {patient.blood_group}</span>
            <span>Gender: <span style={{ textTransform: 'capitalize' }}>{patient.gender || '-'}</span></span>
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => navigate(`/patients/${id}/opd`)}>
          <Plus /> Start New OPD Visit
        </button>
      </div>

      <div className="tabs">
        {['visits', 'prescriptions', 'bills'].map(tab => (
          <div 
            key={tab} 
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
            style={{ textTransform: 'capitalize' }}
          >
            {tab}
          </div>
        ))}
      </div>

      {activeTab === 'visits' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {visits.length === 0 ? <div className="empty-state">No visits recorded yet.</div> : visits.map((v, i) => (
            <div key={v.id} className="card" style={{ borderLeft: '4px solid var(--primary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>Visit on {new Date(v.visit_date).toLocaleDateString('en-IN', {day:'numeric', month:'short', year:'numeric'})}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Complaint: {v.chief_complaint || '-'}</div>
                </div>
                {i === 0 && <span className="badge badge-green">Latest Visit</span>}
              </div>
              
              <div className="vitals-grid">
                <div className="vital-item"><div className="vital-label">BP (mmHg)</div><div className="vital-value">{v.bp_systolic || '-'}/{v.bp_diastolic || '-'}</div></div>
                <div className="vital-item"><div className="vital-label">Weight</div><div className="vital-value">{v.weight_kg || '-'}<span className="vital-unit">kg</span></div></div>
                <div className="vital-item"><div className="vital-label">Temp</div><div className="vital-value">{v.temperature_f || '-'}<span className="vital-unit">°F</span></div></div>
                <div className="vital-item"><div className="vital-label">SpO2</div><div className="vital-value">{v.spo2 || '-'}<span className="vital-unit">%</span></div></div>
                <div className="vital-item"><div className="vital-label">Pulse</div><div className="vital-value">{v.pulse || '-'}<span className="vital-unit">bpm</span></div></div>
              </div>

              {v.diagnosis && (
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: 4 }}>Diagnosis</div>
                  <div style={{ fontWeight: 500 }}>{v.diagnosis}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'prescriptions' && (
         <div className="empty-state">Select a visit to view attached prescriptions.</div>
      )}

      {activeTab === 'bills' && (
         <div className="empty-state">Select a visit or use Billing screen to create bills.</div>
      )}

    </div>
  );
}
