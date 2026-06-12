import React, { useState, useEffect } from 'react';
import { 
  fetchRfps, 
  analyzeRfp, 
  getProposalDraft, 
  approveProposal,
  getRfp,
  API_BASE
} from '../services/api';
import './IntegratedWorkflowNew.css';

const IntegratedWorkflowNew = () => {
  const [rfps, setRfps] = useState([]);
  const [selectedRfp, setSelectedRfp] = useState(null);
  const [agentStatus, setAgentStatus] = useState({
    sales: 'pending',
    technical: 'pending',
    pricing: 'pending',
    proposal: 'pending'
  });
  const [rfpSummary, setRfpSummary] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [proposalDraft, setProposalDraft] = useState(null);
  const [editedSections, setEditedSections] = useState({});
  const [pdfInfo, setPdfInfo] = useState(null);
  const [showHumanReview, setShowHumanReview] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentProgress, setCurrentProgress] = useState(null);
  const [progressPollInterval, setProgressPollInterval] = useState(null);

  useEffect(() => {
    loadRfps();
    
    // Cleanup polling on unmount
    return () => {
      if (progressPollInterval) {
        clearInterval(progressPollInterval);
      }
    };
  }, [progressPollInterval]);

  const loadRfps = async () => {
    try {
      const response = await fetchRfps();
      setRfps(response.data);
    } catch (err) {
      console.error('Error loading RFPs:', err);
      // Retry briefly in case backend is still booting
      setTimeout(() => {
        fetchRfps().then(r => setRfps(r.data)).catch(() => {});
      }, 2000);
    }
  };

  const handleRfpSelect = (rfp) => {
    setSelectedRfp(rfp);
    setRfpSummary(null);
    setAgentStatus({
      sales: 'pending',
      technical: 'pending',
      pricing: 'pending',
      proposal: 'pending'
    });
    setShowHumanReview(false);
    setPdfInfo(null);
    setChatMessages([
      { type: 'system', text: 'Master Agent received your instruction.' }
    ]);
  };

  // Poll for progress updates
  const pollProgress = async (rfpId) => {
    try {
      const response = await fetch(`${API_BASE}/rfp/${rfpId}/progress`);
      const data = await response.json();
      
      if (data.current_progress) {
        setCurrentProgress(data.current_progress);
        
        // Update agent status based on progress
        const { agent, status } = data.current_progress;
        if (agent && status) {
          const agentMap = {
            'Sales Agent': 'sales',
            'Technical Agent': 'technical',
            'Pricing Agent': 'pricing',
            'Proposal Agent': 'proposal'
          };
          
          const agentKey = agentMap[agent];
          if (agentKey) {
            // Prevent regression: don't move completed back to running
            setAgentStatus(prev => {
              const next = { ...prev };
              const incoming = status === 'completed' ? 'completed' : 'running';
              const current = next[agentKey];
              if (current !== 'completed') {
                next[agentKey] = incoming;
              }
              // Enforce sequential progression
              if (agentKey === 'technical' && next.sales !== 'completed') next.sales = 'completed';
              if (agentKey === 'pricing' && next.technical !== 'completed') next.technical = 'completed';
              if (agentKey === 'proposal' && next.pricing !== 'completed') next.pricing = 'completed';
              return next;
            });
          }
        }

        // When pricing completes, fetch RFP to compose a proper summary
        if (agent === 'Pricing Agent' && status === 'completed') {
          try {
            const r = await getRfp(rfpId);
            const rfp = r?.data || {};
            const summary = {
              client: rfp?.title || selectedRfp?.title,
              sales_insights: rfp?.sales_summary?.response || '',
              technical_solution: rfp?.technical_matches?.response || '',
              pricing_summary: rfp?.pricing_data?.response || '',
            };
            setRfpSummary(summary);
          } catch (e) {
            console.warn('Failed to fetch RFP for summary:', e?.message || e);
          }
        }

        // When proposal is completed, stop polling and fetch the draft (only once)
        if (status === 'completed' && data.current_progress.agent === 'Proposal Agent') {
          if (progressPollInterval) {
            clearInterval(progressPollInterval);
            setProgressPollInterval(null);
          }
          // Only fetch draft if we haven't already
          if (!proposalDraft) {
            try {
              const draftResp = await getProposalDraft(rfpId);
              if (draftResp?.data?.proposal_draft) {
                setProposalDraft(draftResp.data.proposal_draft);
                const sections = draftResp.data.proposal_draft.sections || {};
                setEditedSections(sections);
                setShowHumanReview(true);
                setChatMessages(prev => {
                  // Only add message if it doesn't already exist
                  const hasApprovalMessage = prev.some(msg => msg.text?.includes('ready for review'));
                  if (hasApprovalMessage) return prev;
                  return [...prev, { 
                    type: 'system', 
                    text: 'Proposal draft ready for review and approval.' 
                  }];
                });
                // Ensure final status shows completed
                setAgentStatus(prev => ({ ...prev, proposal: 'completed' }));
              }
            } catch (e) {
              console.error('Failed to fetch proposal draft:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error polling progress:', error);
      // Stop polling on network errors to avoid spam
      if (progressPollInterval) {
        clearInterval(progressPollInterval);
        setProgressPollInterval(null);
      }
    }
  };

  const startWorkflow = async () => {
    if (!selectedRfp) return;

    setLoading(true);
    setCurrentProgress(null);
    setChatMessages(prev => [...prev, { type: 'system', text: 'Processing RFP...' }]);

    // Start polling for progress (store interval in state for cleanup)
    const intervalId = setInterval(() => pollProgress(selectedRfp.id), 2000);
    setProgressPollInterval(intervalId);

    try {
      // Fire analyze endpoint but rely on polling for updates
      analyzeRfp(selectedRfp.id)
        .then((response) => {
          // If backend returns quickly with summary, set it; otherwise polling handles progression
          if (response?.data?.rfp_summary) {
            setRfpSummary(response.data.rfp_summary);
          }
        })
        .catch((err) => {
          // Ignore timeout here; polling will continue updating the UI
          console.warn('Analyze call warning (continuing with polling):', err?.message || err);
        });

    } catch (error) {
      console.error('Workflow error:', error);
      setChatMessages(prev => [...prev, { 
        type: 'error', 
        text: `Error: ${error.message}` 
      }]);
    } finally {
      // Keep loading state until polling determines completion stages
      setLoading(false);
    }
  };

  const handleSendMessage = () => {
    if (!userMessage.trim()) return;
    
    setChatMessages(prev => [...prev, { type: 'user', text: userMessage }]);
    
    // Simple responses
    if (userMessage.toLowerCase().includes('hi') || userMessage.toLowerCase().includes('hello')) {
      setTimeout(() => {
        setChatMessages(prev => [...prev, { 
          type: 'system', 
          text: 'Master Agent received your instruction.' 
        }]);
      }, 500);
    }
    
    setUserMessage('');
  };

  const handleGenerateProposal = async () => {
    if (!selectedRfp) return;

    setLoading(true);
    try {
      const payload = {
        approved: true,
        title: proposalDraft?.title || `Response Proposal for ${selectedRfp.title}`,
        sections: editedSections
      };
      const response = await approveProposal(selectedRfp.id, payload);

      setPdfInfo({
        proposalText: Object.values(editedSections || {}).join('\n\n'),
        pdfUrl: response?.data?.pdf_info?.download_url,
        pdfFilename: response?.data?.pdf_info?.filename
      });

      setShowHumanReview(false);
      setChatMessages(prev => [...prev, { 
        type: 'system', 
        text: 'Proposal PDF generated successfully!' 
      }]);

    } catch (error) {
      console.error('Error generating proposal:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSectionEdit = (sectionKey, value) => {
    setEditedSections(prev => ({
      ...prev,
      [sectionKey]: value
    }));
  };

  return (
    <div className="integrated-workflow-new">
      <div className="workflow-grid">
        {/* Left Column */}
        <div className="left-column">
          {/* Detected RFPs */}
          <section className="card">
            <h3 className="card-title">
              <span className="icon"></span>
              Detected RFPs (Sales Agent)
            </h3>
            <div className="rfp-list">
              {rfps.map(rfp => (
                <div 
                  key={rfp.id} 
                  className={`rfp-item ${selectedRfp?.id === rfp.id ? 'active' : ''}`}
                  onClick={() => handleRfpSelect(rfp)}
                >
                  {rfp.title}
                </div>
              ))}
            </div>
          </section>

          {/* Master Agent Chat */}
          <section className="card master-chat">
            <h3 className="card-title">
              <span className="icon">💬</span>
              Master Agent Chat
            </h3>
            <div className="chat-messages">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`chat-message ${msg.type}`}>
                  {msg.type === 'system' && <span className="check-icon">✅</span>}
                  <span className="message-text">{msg.text}</span>
                  {msg.type === 'user' && <span className="user-badge">{msg.text}</span>}
                </div>
              ))}
            </div>
            <div className="chat-input-area">
              <input 
                type="text" 
                placeholder="Type message..."
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                className="chat-input"
              />
              <button onClick={handleSendMessage} className="btn-send">Send</button>
            </div>
          </section>
        </div>

        {/* Right Column */}
        <div className="right-column">
          {/* Agent Processing Status */}
          <section className="card">
            <h3 className="card-title">
              <span className="icon">⚙️</span>
              Agent Processing
            </h3>
            {currentProgress && (
              <div className="progress-indicator">
                <strong>Current:</strong> {currentProgress.agent}
                {currentProgress.tool && ` - Tool: ${currentProgress.tool}`}
                <span className="progress-status"> ({currentProgress.status})</span>
              </div>
            )}
            <div className="agent-status-list">
              <div className="agent-status-item">
                <span>Sales Agent</span>
                <span className={`status-badge ${agentStatus.sales}`}>
                  {agentStatus.sales === 'completed' ? '✓ Completed' : '→ ' + agentStatus.sales}
                </span>
              </div>
              <div className="agent-status-item">
                <span>Technical Agent</span>
                <span className={`status-badge ${agentStatus.technical}`}>
                  {agentStatus.technical === 'completed' ? '✓ Completed' : '→ ' + agentStatus.technical}
                </span>
              </div>
              <div className="agent-status-item">
                <span>Pricing Agent</span>
                <span className={`status-badge ${agentStatus.pricing}`}>
                  {agentStatus.pricing === 'completed' ? '✓ Completed' : '→ ' + agentStatus.pricing}
                </span>
              </div>
              <div className="agent-status-item">
                <span>Proposal Agent</span>
                <span className={`status-badge ${agentStatus.proposal}`}>
                  {agentStatus.proposal === 'completed' ? '✓ Completed' : '→ ' + agentStatus.proposal}
                </span>
              </div>
            </div>
            {selectedRfp && agentStatus.sales === 'pending' && (
              <button 
                onClick={startWorkflow} 
                className="btn-start-workflow"
                disabled={loading}
              >
                {loading ? '⏳ Processing...' : '▶️ Start Processing'}
              </button>
            )}
          </section>

          {/* RFP Summary */}
          {rfpSummary && (
            <section className="card">
              <h3 className="card-title">
                <span className="icon">📊</span>
                RFP Summary
              </h3>
              <div className="summary-content">
                <p><strong>Client:</strong> {rfpSummary.client || selectedRfp?.title}</p>
                <ul>
                  {rfpSummary.key_points?.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  )) || (
                    <>
                      <li>Bulk paint procurement</li>
                      <li>Cost optimization</li>
                      <li>Fast delivery timeline</li>
                    </>
                  )}
                </ul>
              </div>
            </section>
          )}

          {/* Human Review Required */}
          {showHumanReview && (
            <section className="card">
              <h3 className="card-title">
                <span className="icon">✅</span>
                Human Review Required
              </h3>
              {proposalDraft && (
                <div className="draft-editor">
                  {Object.entries(editedSections || {}).map(([key, value]) => (
                    <div key={key} className="draft-section">
                      <label className="draft-label">{key}</label>
                      <textarea
                        className="draft-textarea"
                        value={value || ''}
                        onChange={(e) => handleSectionEdit(key, e.target.value)}
                        rows={6}
                      />
                    </div>
                  ))}
                </div>
              )}
              <button 
                onClick={handleGenerateProposal}
                className="btn-generate-proposal"
                disabled={loading}
              >
                {loading ? '⏳ Generating...' : 'Generate Proposal'}
              </button>
            </section>
          )}

          {/* Final Proposal */}
          {pdfInfo && (
            <section className="card">
              <h3 className="card-title">
                <span className="icon">📄</span>
                Final Proposal
              </h3>
              <div className="proposal-output">
                <div className="proposal-text-preview">
                  <pre>{pdfInfo.proposalText.substring(0, 500)}...</pre>
                </div>
                <div className="pdf-download-area">
                  <p className="pdf-filename">📎 {pdfInfo.pdfFilename}</p>
                  <a 
                    href={pdfInfo.pdfUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn-download"
                  >
                    ⬇️ Download PDF
                  </a>
                </div>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
};

export default IntegratedWorkflowNew;
