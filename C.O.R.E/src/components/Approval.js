import React, { useState, useEffect } from 'react';
import { getRFP, approveProposal } from '../services/api';

function Approval({ rfpId, onReset }) {
  const [rfp, setRfp] = useState(null);
  const [proposal, setProposal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRFP = async () => {
      try {
        const res = await getRFP(rfpId);
        setRfp(res.data);
        setProposal(res.data.proposal_draft || {});
      } catch (err) {
        setError('Could not load proposal.');
      } finally {
        setLoading(false);
      }
    };
    fetchRFP();
  }, [rfpId]);

  const handleApprove = async () => {
    setApproving(true);
    try {
      await approveProposal(rfpId, { edited_proposal: proposal });
      setApproved(true);
    } catch (err) {
      setError('Approval failed. Try again.');
    } finally {
      setApproving(false);
    }
  };

  const handleEdit = (key, value) => {
    setProposal(prev => ({ ...prev, [key]: value }));
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '48px', color: '#888' }}>Loading proposal...</div>;

  if (approved) return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '48px',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '64px', marginBottom: '16px' }}>🎉</div>
      <h2 style={{ marginBottom: '8px' }}>Proposal Approved!</h2>
      <p style={{ color: '#666', marginBottom: '32px' }}>
        Your proposal has been approved and saved successfully.
      </p>
      <button
        onClick={onReset}
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
        Start New RFP
      </button>
    </div>
  );

  const sections = [
    { key: 'executive_summary', label: 'Executive Summary' },
    { key: 'understanding_of_requirements', label: 'Understanding of Requirements' },
    { key: 'proposed_solution', label: 'Proposed Solution' },
    { key: 'technical_approach', label: 'Technical Approach' },
    { key: 'pricing_summary', label: 'Pricing Summary' },
    { key: 'timeline', label: 'Timeline' },
    { key: 'terms_and_conditions', label: 'Terms and Conditions' },
    { key: 'conclusion', label: 'Conclusion' },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: '8px' }}>Review Proposal Draft</h2>
      <p style={{ color: '#666', marginBottom: '32px' }}>
        Edit any section below before approving.
      </p>

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

      {sections.map(({ key, label }) => (
        <div key={key} style={{
          background: 'white',
          border: '1px solid #eee',
          borderRadius: '12px',
          padding: '20px 24px',
          marginBottom: '16px'
        }}>
          <label style={{
            display: 'block',
            fontWeight: '600',
            marginBottom: '8px',
            color: '#1a1a2e'
          }}>
            {label}
          </label>
          <textarea
            value={proposal?.[key] || ''}
            onChange={(e) => handleEdit(key, e.target.value)}
            rows={4}
            style={{
              width: '100%',
              border: '1px solid #ddd',
              borderRadius: '8px',
              padding: '10px',
              fontSize: '14px',
              fontFamily: 'inherit',
              resize: 'vertical',
              boxSizing: 'border-box'
            }}
          />
        </div>
      ))}

      <button
        onClick={handleApprove}
        disabled={approving}
        style={{
          background: approving ? '#888' : '#1a1a2e',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          padding: '14px 32px',
          fontSize: '16px',
          cursor: approving ? 'not-allowed' : 'pointer',
          width: '100%',
          marginTop: '8px'
        }}
      >
        {approving ? 'Approving...' : '✓ Approve & Save Proposal'}
      </button>
    </div>
  );
}

export default Approval;