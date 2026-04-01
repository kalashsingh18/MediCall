import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Droplet, Thermometer, HeartPulse, Activity as ActivityIcon, Activity, User, Scale } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function OPDForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [doctors, setDoctors] = useState([]);
  
  // Form State
  const [doctorId, setDoctorId] = useState('');
  const [vitals, setVitals] = useState({
    bp_systolic: '', bp_diastolic: '', weight_kg: '', temperature_f: '', spo2: '', pulse: ''
  });
  const [clinical, setClinical] = useState({ chief_complaint: '', diagnosis: '', clinical_notes: '' });
  const [medicines, setMedicines] = useState([]);
  const [newMed, setNewMed] = useState({ name: '', dosage: '', duration: '', notes: '' });

  useEffect(() => {
    fetchPatientAndDoctors();
  }, [id]);

  const fetchPatientAndDoctors = async () => {
    try {
      const [patRes, docRes] = await Promise.all([
        api.get(`/patients/${id}`),
        api.get('/doctors')
      ]);
      setPatient(patRes.data);
      setDoctors(docRes.data);
      if (docRes.data.length > 0) setDoctorId(docRes.data[0].id);
    } catch (err) {
      toast.error('Failed to load data');
    }
  };

  const addMedicine = () => {
    if (!newMed.name || !newMed.dosage) return toast.error('Name and dosage required');
    setMedicines([...medicines, newMed]);
    setNewMed({ name: '', dosage: '', duration: '', notes: '' });
  };

  const submitOPD = async (e) => {
    e.preventDefault();
    if (!doctorId) return toast.error('Please select a doctor');

    try {
      // Create Visit
      const visitPayload = {
        patient_id: id,
        doctor_id: doctorId,
        bp_systolic: vitals.bp_systolic || null,
        bp_diastolic: vitals.bp_diastolic || null,
        weight_kg: vitals.weight_kg || null,
        temperature_f: vitals.temperature_f || null,
        spo2: vitals.spo2 || null,
        pulse: vitals.pulse || null,
        ...clinical
      };
      
      const visitRes = await api.post('/visits', visitPayload);
      
      // Create Prescription if any
      if (medicines.length > 0) {
        await api.post('/prescriptions', {
          visit_id: visitRes.data.id,
          patient_id: id,
          doctor_id: doctorId,
          medicines
        });
      }

      toast.success('OPD Visit Recorded');
      navigate(`/patients/${id}`);
    } catch (err) {
      toast.error('Failed to save visit');
    }
  };

  if (!patient) return <div className="spinner"></div>;

  return (
    <div>
      <div className="page-header" style={{ marginBottom: 16 }}>
        <div>
          <button className="btn btn-ghost" style={{ marginBottom: 16, padding: 0 }} onClick={() => navigate(`/patients/${id}`)}>
             <ArrowLeft /> Back to Profile
          </button>
          <h1 className="page-title">New OPD Visit</h1>
          <p className="page-subtitle">Recording visit for {patient.name} ({patient.phone})</p>
        </div>
        <button className="btn btn-primary" onClick={submitOPD}>
          <Save /> Save Visit
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 340px', gap: 24, alignItems: 'start' }}>
        
        {/* Left Col - Clinical & Prescription */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: 16 }}>Consultation Details</h2>
            <div className="form-group">
              <label className="form-label">Consulting Doctor</label>
              <select className="form-select" value={doctorId} onChange={e=>setDoctorId(e.target.value)}>
                {doctors.map(d => <option key={d.id} value={d.id}>{d.name} ({d.specialization || 'GP'})</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Chief Complaint (Reason for visit)</label>
              <textarea className="form-textarea" rows="2" value={clinical.chief_complaint} onChange={e=>setClinical({...clinical, chief_complaint:e.target.value})} placeholder="e.g., Persistent cough for 3 days..."></textarea>
            </div>
            <div className="form-group">
              <label className="form-label">Diagnosis</label>
              <input type="text" className="form-input" value={clinical.diagnosis} onChange={e=>setClinical({...clinical, diagnosis:e.target.value})} placeholder="e.g., Viral Pharyngitis" />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Clinical Notes</label>
              <textarea className="form-textarea" rows="4" value={clinical.clinical_notes} onChange={e=>setClinical({...clinical, clinical_notes:e.target.value})} placeholder="Observations, next steps..."></textarea>
            </div>
          </div>

          <div className="card">
            <h2 className="card-title" style={{ marginBottom: 16 }}>Prescription (Rx)</h2>
            <div style={{ background: 'var(--bg-hover)', padding: '16px', borderRadius: 'var(--radius)', marginBottom: 20 }}>
              <div className="form-row" style={{ gridTemplateColumns: '2fr 1fr 1fr 1fr' }}>
                <div>
                  <label className="form-label" style={{fontSize:11}}>Medicine</label>
                  <input type="text" className="form-input" placeholder="Paracetamol 500mg" value={newMed.name} onChange={e=>setNewMed({...newMed, name:e.target.value})} />
                </div>
                <div>
                  <label className="form-label" style={{fontSize:11}}>Dosage</label>
                  <input type="text" className="form-input" placeholder="1-0-1" value={newMed.dosage} onChange={e=>setNewMed({...newMed, dosage:e.target.value})} />
                </div>
                <div>
                  <label className="form-label" style={{fontSize:11}}>Duration</label>
                  <input type="text" className="form-input" placeholder="5 days" value={newMed.duration} onChange={e=>setNewMed({...newMed, duration:e.target.value})} />
                </div>
                <div>
                  <label className="form-label" style={{fontSize:11}}>&nbsp;</label>
                  <button className="btn btn-secondary" style={{width:'100%', justifyContent:'center'}} onClick={addMedicine}>Add</button>
                </div>
              </div>
            </div>

            {medicines.length === 0 ? <div className="empty-state">No medicines added</div> : (
              <table style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
                <thead>
                  <tr><th>Medicine</th><th>Dosage</th><th>Duration</th><th style={{width: 50}}></th></tr>
                </thead>
                <tbody>
                  {medicines.map((m, i) => (
                    <tr key={i}>
                      <td style={{fontWeight:600}}>{m.name}</td>
                      <td>{m.dosage}</td>
                      <td>{m.duration}</td>
                      <td><button style={{color:'var(--danger)', background:'none', border:'none', cursor:'pointer'}} onClick={() => setMedicines(medicines.filter((_,idx)=>idx!==i))}>✕</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

        </div>

        {/* Right Col - Vitals */}
        <div className="card" style={{ position: 'sticky', top: 88 }}>
          <h2 className="card-title" style={{ marginBottom: 20 }}>Vitals Entry</h2>
          
          <div className="form-group">
            <label className="form-label" style={{display:'flex', gap:6, alignItems:'center'}}><HeartPulse size={14}/> Blood Pressure</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input type="number" className="form-input" placeholder="Sys" value={vitals.bp_systolic} onChange={e=>setVitals({...vitals, bp_systolic:e.target.value})} />
              <span style={{color:'var(--text-muted)'}}>/</span>
              <input type="number" className="form-input" placeholder="Dia" value={vitals.bp_diastolic} onChange={e=>setVitals({...vitals, bp_diastolic:e.target.value})} />
              <span style={{fontSize:12, color:'var(--text-muted)'}}>mmHg</span>
            </div>
          </div>
          
          <div className="form-group">
            <label className="form-label" style={{display:'flex', gap:6, alignItems:'center'}}><Scale size={14}/> Weight</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input type="number" step="0.1" className="form-input" placeholder="0.0" value={vitals.weight_kg} onChange={e=>setVitals({...vitals, weight_kg:e.target.value})} />
              <span style={{fontSize:12, color:'var(--text-muted)'}}>kg</span>
            </div>
          </div>

          <div className="form-group">
           <label className="form-label" style={{display:'flex', gap:6, alignItems:'center'}}><Thermometer size={14}/> Temperature</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input type="number" step="0.1" className="form-input" placeholder="98.6" value={vitals.temperature_f} onChange={e=>setVitals({...vitals, temperature_f:e.target.value})} />
              <span style={{fontSize:12, color:'var(--text-muted)'}}>°F</span>
            </div>
          </div>

          <div className="form-group">
           <label className="form-label" style={{display:'flex', gap:6, alignItems:'center'}}><Droplet size={14}/> SpO2</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input type="number" className="form-input" placeholder="98" value={vitals.spo2} onChange={e=>setVitals({...vitals, spo2:e.target.value})} />
              <span style={{fontSize:12, color:'var(--text-muted)'}}>%</span>
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
           <label className="form-label" style={{display:'flex', gap:6, alignItems:'center'}}><ActivityIcon size={14}/> Pulse Rate</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input type="number" className="form-input" placeholder="72" value={vitals.pulse} onChange={e=>setVitals({...vitals, pulse:e.target.value})} />
              <span style={{fontSize:12, color:'var(--text-muted)'}}>bpm</span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
