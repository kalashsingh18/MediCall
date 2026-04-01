import React, { useEffect, useState } from 'react';
import { Plus, Search, Receipt } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

export default function Billing() {
  const [bills, setBills] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ patient_id: '', discount: 0, payment_mode: 'cash', gst_percent: 0 });
  const [items, setItems] = useState([{ description: 'Consultation Fee', amount: 500 }]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [bRes, pRes] = await Promise.all([
        api.get('/billing'),
        api.get('/patients')
      ]);
      setBills(bRes.data);
      setPatients(pRes.data);
    } catch (err) {
      toast.error('Failed to load billing history');
    } finally {
      setLoading(false);
    }
  };

  const addItemRow = () => setItems([...items, { description: '', amount: 0 }]);
  
  const handleItemChange = (index, field, val) => {
    const newItems = [...items];
    newItems[index][field] = field === 'amount' ? Number(val) : val;
    setItems(newItems);
  };

  const handleCreateBill = async (e) => {
    e.preventDefault();
    try {
      if (items.some(i => !i.description || i.amount <= 0)) {
        return toast.error('Check bill items for valid description and amount');
      }

      await api.post('/billing', {
        ...formData,
        items
      });
      toast.success('Bill generated successfully');
      setShowModal(false);
      fetchData();
    } catch (err) {
      toast.error('Failed to create bill');
    }
  };

  const handlePayBill = async (billId, totalAmount, paymentMode) => {
    try {
      await api.put(`/billing/${billId}/pay`, {
        paid_amount: totalAmount,
        payment_mode: paymentMode
      });
      toast.success('Payment recorded');
      fetchData();
    } catch (err) {
      toast.error('Payment failed');
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Billing & Invoices</h1>
          <p className="page-subtitle">Track payments, missing dues, and generate receipts.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus /> Generate Bill
        </button>
      </div>

      <div className="card table-wrapper">
        {loading ? <div className="spinner"></div> : (
          <table>
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Patient</th>
                <th>Date</th>
                <th>Total Amt</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {bills.length === 0 ? (
                <tr><td colSpan="6" style={{textAlign:'center', padding:'40px', color:'var(--text-muted)'}}>No invoices found.</td></tr>
              ) : (
                bills.map(b => {
                  const p = patients.find(x => x.id === b.patient_id);
                  return (
                    <tr key={b.id}>
                      <td style={{fontWeight:600}}>{b.bill_number}</td>
                      <td>{p?.name || 'Unknown'}</td>
                      <td>{new Date(b.created_at).toLocaleDateString()}</td>
                      <td style={{fontWeight:700}}>₹{b.total.toFixed(2)}</td>
                      <td>
                        <span className={`badge ${b.status === 'paid' ? 'badge-green' : b.status === 'partial' ? 'badge-yellow' : 'badge-red'}`}>
                          {b.status.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        {b.status !== 'paid' && (
                          <button 
                            className="btn btn-sm btn-secondary" 
                            onClick={() => handlePayBill(b.id, b.total, 'cash')}
                          >
                            Mark Paid
                          </button>
                        )}
                        {b.status === 'paid' && (
                          <button className="btn btn-sm btn-ghost"><Receipt size={14}/> Receipt</button>
                        )}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal modal-lg">
            <div className="modal-header">
              <h2 className="modal-title">Generate Bill</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateBill}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Select Patient</label>
                  <select className="form-select" required value={formData.patient_id} onChange={e => setFormData({...formData, patient_id: e.target.value})}>
                    <option value="">-- Choose --</option>
                    {patients.map(p => <option key={p.id} value={p.id}>{p.name} ({p.phone})</option>)}
                  </select>
                </div>

                <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 16, marginBottom: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>Bill Items</div>
                    <button type="button" className="btn btn-sm btn-secondary" onClick={addItemRow}>+ Add Item</button>
                  </div>
                  
                  {items.map((it, idx) => (
                    <div key={idx} style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                      <input type="text" className="form-input" style={{flex: 1}} placeholder="Description" value={it.description} onChange={e => handleItemChange(idx, 'description', e.target.value)} required />
                      <input type="number" className="form-input" style={{width: 140}} placeholder="Amount" value={it.amount} onChange={e => handleItemChange(idx, 'amount', e.target.value)} required min="0" />
                      <button type="button" style={{color:'var(--danger)', background:'none', border:'none', cursor:'pointer', padding:'0 8px'}} onClick={() => setItems(items.filter((_,i)=>i!==idx))}>✕</button>
                    </div>
                  ))}
                  <div style={{ textAlign: 'right', fontWeight: 700, marginTop: 16 }}>
                    Subtotal: ₹{items.reduce((s,i)=>s+(Number(i.amount)||0), 0)}
                  </div>
                </div>

                <div className="form-row-3">
                  <div className="form-group">
                    <label className="form-label">Discount (₹)</label>
                    <input type="number" className="form-input" value={formData.discount} onChange={e => setFormData({...formData, discount: Number(e.target.value)})} min="0" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">GST Tax (%)</label>
                    <input type="number" className="form-input" value={formData.gst_percent} onChange={e => setFormData({...formData, gst_percent: Number(e.target.value)})} min="0" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Wait! Has the patient paid?</label>
                    <select className="form-select" value={formData.payment_mode} onChange={e => setFormData({...formData, payment_mode: e.target.value})}>
                      <option value="pending">No, add to dues (Unpaid)</option>
                      <option value="cash">Yes, Cash</option>
                      <option value="upi">Yes, UPI</option>
                      <option value="card">Yes, Card</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Invoice</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
