import React, { useState, useEffect } from 'react';
import { listRFPs } from '../services/api';

function History({ user, onSelect }) {
  const [rfps, setRfps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await listRFPs();
        // Filter only this user's RFPs
        const myRfps = res.data.rfps.filter(r => r.user_id === user.id);
        setRfps(myRfps);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [user]);

  const statusColor = (status) => {
    if (status === 'awaiting_approval') return '#f59e0b';
    if (status === 'approved') return '#2e7d32';
    if (status === 'processing') return '#1976d2';
    if (status === 'error') return '#cc0000';
    return '#888';
  };

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '48px', color: '#888' }}>
      Loading your RFPs...
    </div>
  );

  if (rfps.length === 0) return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '48px',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
      <h3 style={{ color: '#888' }}>No RFPs yet</h3>
      <p style={{ color: '#aaa' }}>Upload your first RFP to get started</p>
    </div>
  );

  return (
    <div>
      <h2 style={{ marginBottom: '8px' }}>My RFPs</h2>
      <p style={{ color: '#666', marginBottom: '24px' }}>
        {rfps.length} RFP{rfps.length !== 1 ? 's' : ''} found
      </p>

      {rfps.map(rfp => (
        <div
          key={rfp.id}
          style={{
            background: 'white',
            border: '1px solid #eee',
            borderRadius: '12px',
            padding: '20px 24px',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            transition: 'box-shadow 0.2s'
          }}
          onClick={() => onSelect(rfp.id)}
          onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'}
          onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ fontSize: '32px' }}>📄</div>
            <div>
              <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                {rfp.filename || 'Unnamed RFP'}
              </div>
              <div style={{ color: '#888', fontSize: '13px' }}>
                {new Date(rfp.created_at).toLocaleDateString('en-US', {
                  year: 'numeric', month: 'short', day: 'numeric',
                  hour: '2-digit', minute: '2-digit'
                })}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{
              background: statusColor(rfp.status) + '20',
              color: statusColor(rfp.status),
              padding: '4px 12px',
              borderRadius: '99px',
              fontSize: '13px',
              fontWeight: '500'
            }}>
              {rfp.status}
            </span>
            <span style={{ color: '#ccc', fontSize: '20px' }}>→</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default History;