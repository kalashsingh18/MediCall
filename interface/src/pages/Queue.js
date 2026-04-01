import React, { useEffect, useState } from 'react';
import { Play, CheckCircle2, UserCheck, Stethoscope } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function Queue() {
  const [queue, setQueue] = useState([]);
  const [patients, setPatients] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      const qs = await api.get('/queue/today');
      setQueue(qs.data);
      
      // Fetch related patients in one go if not already fetched
      // Just fetching all for simplicity in demo
      const patRes = await api.get('/patients');
      const pMap = {};
      patRes.data.forEach(p => pMap[p.id] = p);
      setPatients(pMap);
    } catch (err) {
      toast.error('Failed to load queue');
    } finally {
      setLoading(false);
    }
  };

  const actionMap = {
    scheduled: { label: 'Mark Arrived', icon: UserCheck, endpoint: '/arrive', class: 'btn-secondary' },
    arrived: { label: 'Call Next', icon: Play, endpoint: '/call', class: 'btn-primary' },
    in_consultation: { label: 'Mark Done', icon: CheckCircle2, endpoint: '/done', class: 'btn-primary', style: {background: 'var(--accent)'} }
  };

  const handleAction = async (appt, actStr) => {
    const act = actionMap[actStr];
    if (!act) return;
    try {
      await api.put(`/queue/${appt.id}${act.endpoint}`);
      toast.success(`Patient ${act.label.toLowerCase()}`);
      fetchQueue();
    } catch (err) {
      toast.error('Action failed');
    }
  };

  if (loading) return <div className="spinner"></div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Live Queue Board</h1>
          <p className="page-subtitle">Real-time token tracking for today</p>
        </div>
      </div>

      <div className="token-grid">
        {queue.length === 0 ? (
          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
            <Stethoscope />
            <h3>No appointments today</h3>
            <p>You can add walk-ins from the Appointments tab.</p>
          </div>
        ) : (
          queue.map(appt => {
            const statusCardClass = appt.status === 'in_consultation' ? 'in-consultation' : 
                                    appt.status === 'arrived' ? 'active' : '';
            const p = patients[appt.patient_id];
            
            return (
              <div key={appt.id} className={`token-card ${statusCardClass}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>Token No.</div>
                    <div className="token-number">{appt.token_number}</div>
                  </div>
                  <span className={`badge ${appt.status === 'in_consultation' ? 'badge-purple' : appt.status === 'arrived' ? 'badge-yellow' : 'badge-blue'}`}>
                    {appt.status.replace('_', ' ')}
                  </span>
                </div>
                
                <div style={{ marginTop: 8 }}>
                  <div className="token-patient-name">{p?.name || 'Unknown Patient'}</div>
                  <div className="token-info">{appt.reason || 'General Consultation'} {appt.is_walk_in && '• Walk-in'}</div>
                </div>

                {appt.status !== 'done' && actionMap[appt.status] && (
                  <button 
                    className={`btn ${actionMap[appt.status].class}`} 
                    style={{ width: '100%', justifyContent: 'center', marginTop: 'auto', paddingTop: 8, ...actionMap[appt.status].style }}
                    onClick={() => handleAction(appt, appt.status)}
                  >
                    {React.createElement(actionMap[appt.status].icon)} {actionMap[appt.status].label}
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
