import React, { useState, useEffect } from 'react';
import { getRFPStatus, getRFP } from '../services/api';

const AGENTS = [
  { key: 'sales', name: 'Sales Agent', desc: 'Extracting objectives, scope and requirements' },
  { key: 'technical', name: 'Technical Agent', desc: 'Matching requirements to products/SKUs' },
  { key: 'pricing', name: 'Pricing Agent', desc: 'Building cost breakdown table' },
  { key: 'proposal', name: 'Proposal Assembly Agent', desc: 'Writing full proposal draft' },
];

function StatusBadge({ status }) {
  const colors = {
    pending:   { bg: '#f5f5f5', color: '#888' },
    running:   { bg: '#fff8e1', color: '#f59e0b' },
    completed: { bg: '#e8f5e9', color: '#2e7d32' },
    error:     { bg: '#fff0f0', color: '#cc0000' },
  };
  const style = colors[status] || colors.pending;
  return (
    <span style={{
      background: style.bg,
      color: style.color,
      padding: '4px 12px',
      borderRadius: '99px',
      fontSize: '13px',
      fontWeight: '500'
    }}>
      {status === 'running' ? '⟳ Running...' : status}
    </span>
  );
}

function Pipeline({ rfpId, onApprove }) {
  const [progress, setProgress] = useState({});
  const [rfpStatus, setRfpStatus] = useState('processing');
  const [rfpData, setRfpData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!rfpId) return;

    const poll = setInterval(async () => {
      try {
        const res = await getRFPStatus(rfpId);
        const data = res.data;
        setProgress(data.current_progress || {});
        setRfpStatus(data.status);

        if (data.status === 'awaiting_approval') {
          clearInterval(poll);
          const rfpRes = await getRFP(rfpId);
          setRfpData(rfpRes.data);
        }

        if (data.status === 'error') {
          clearInterval(poll);
          setError('Pipeline encountered an error.');
        }
      } catch (err) {
        setError('Could not connect to FastAPI. Make sure it is running.');
        clearInterval(poll);
      }
    }, 2000);

    return () => clearInterval(poll);
  }, [rfpId]);

  return (
    <div>
      <h2 style={{ marginBottom: '8px' }}>AI Pipeline Running</h2>
      <p style={{ color: '#666', marginBottom: '32px' }}>
        RFP ID: <code style={{ background: '#f5f5f5', padding: '2px 8px', borderRadius: '4px' }}>{rfpId}</code>
      </p>

      {/* Agent steps */}
      <div style={{ marginBottom: '32px' }}>
        {AGENTS.map((agent, i) => {
          const status = progress[agent.key] || 'pending';
          return (
            <div key={agent.key} style={{
              background: 'white',
              border: '1px solid #eee',
              borderRadius: '12px',
              padding: '20px 24px',
              marginBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: status === 'completed' ? '#1a1a2e' : '#f5f5f5',
                  color: status === 'completed' ? 'white' : '#888',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '600'
                }}>{status === 'completed' ? '✓' : i + 1}</div>
                <div>
                  <div style={{ fontWeight: '600', marginBottom: '2px' }}>{agent.name}</div>
                  <div style={{ color: '#888', fontSize: '13px' }}>{agent.desc}</div>
                </div>
              </div>
              <StatusBadge status={status} />
            </div>
          );
        })}
      </div>

      {error && (
        <div style={{
          background: '#fff0f0',
          border: '1px solid #ffcccc',
          borderRadius: '8px',
          padding: '12px 16px',
          color: '#cc0000',
          marginBottom: '16px'
        }}>
          {error}
        </div>
      )}

      {rfpStatus === 'awaiting_approval' && (
        <div style={{
          background: '#e8f5e9',
          border: '1px solid #a5d6a7',
          borderRadius: '12px',
          padding: '24px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>✅</div>
          <h3 style={{ margin: '0 0 8px' }}>Pipeline Complete!</h3>
          <p style={{ color: '#666', marginBottom: '16px' }}>
            All agents finished. Proposal draft is ready for your review.
          </p>
          <button
            onClick={onApprove}
            style={{
              background: '#1a1a2e',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 32px',
              fontSize: '16px',
              cursor: 'pointer'
            }}
          >
            Review & Approve Proposal
          </button>
        </div>
      )}

      {rfpStatus === 'processing' && (
        <div style={{ textAlign: 'center', color: '#888', padding: '16px' }}>
          Pipeline is running... this page updates automatically every 2 seconds.
        </div>
      )}
    </div>
  );
}

export default Pipeline;