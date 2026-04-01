import React, { useEffect, useState } from 'react';
import { Bot, PhoneCall, MessageSquare, Clock } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function AgentAnalytics() {
  const [interactions, setInteractions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInteractions();
  }, []);

  const fetchInteractions = async () => {
    try {
      const res = await api.get('/dashboard/ai-interactions');
      setInteractions(res.data);
    } catch (err) {
      toast.error('Failed to load AI analytics');
    } finally {
      setLoading(false);
    }
  };

  const calculateTotalDuration = () => {
    return interactions.reduce((acc, curr) => acc + (curr.duration || 0), 0);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">AI Agent Hub</h1>
          <p className="page-subtitle">Transcripts & Analytics for Voice and WhatsApp AI</p>
        </div>
        <button className="btn btn-primary" onClick={fetchInteractions}>
          Refresh Logs
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '32px' }}>
        <div className="stat-card">
          <div className="stat-icon" style={{background: 'var(--primary-light)', color: 'var(--primary)'}}>
            <Bot size={24} />
          </div>
          <div className="stat-info">
            <div className="stat-label">Total Interactions</div>
            <div className="stat-value">{interactions.length}</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#e0f2fe', color: '#0284c7'}}>
            <PhoneCall size={24} />
          </div>
          <div className="stat-info">
            <div className="stat-label">Voice Calls</div>
            <div className="stat-value">{interactions.filter(i => i.channel === 'VOICE').length}</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#dcfce7', color: '#16a34a'}}>
            <MessageSquare size={24} />
          </div>
          <div className="stat-info">
            <div className="stat-label">WhatsApp Chats</div>
            <div className="stat-value">{interactions.filter(i => i.channel === 'WHATSAPP').length}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{background: '#f3e8ff', color: '#9333ea'}}>
            <Clock size={24} />
          </div>
          <div className="stat-info">
            <div className="stat-label">Total Talk Time (Secs)</div>
            <div className="stat-value">{calculateTotalDuration()}</div>
          </div>
        </div>
      </div>

      <div className="card table-wrapper">
        <h2 style={{ padding: '20px 24px', margin: 0, fontSize: 18, borderBottom: '1px solid var(--border)' }}>Recent Agent Transcripts</h2>
        {loading ? <div className="spinner"></div> : (
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Channel</th>
                <th>Patient Phone</th>
                <th>Transcript Preview</th>
                <th>Duration</th>
              </tr>
            </thead>
            <tbody>
              {interactions.length === 0 ? (
                <tr><td colSpan="5" style={{textAlign:'center', padding:'30px', color:'var(--text-muted)'}}>No AI interactions recorded yet.</td></tr>
              ) : (
                interactions.map(inter => (
                  <tr key={inter.id}>
                    <td style={{whiteSpace:'nowrap'}}>{new Date(inter.created_at).toLocaleString()}</td>
                    <td>
                      <span className={`badge ${inter.channel === 'VOICE' ? 'badge-blue' : 'badge-green'}`}>
                        {inter.channel}
                      </span>
                    </td>
                    <td style={{fontWeight: 600}}>{inter.patient_ph}</td>
                    <td style={{maxWidth: '400px'}}>
                      <div style={{fontSize: 12, color: 'var(--text-muted)', marginBottom: 4}}>User: {inter.transcript?.user || '-'}</div>
                      <div style={{fontSize: 13, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>
                        <b>AI:</b> {inter.transcript?.ai || '-'}
                      </div>
                    </td>
                    <td>{inter.duration ? `${inter.duration}s` : '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
