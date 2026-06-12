import React, { useState, useEffect } from 'react';
import { 
  fetchRfps, 
  uploadRfpFile, 
  deleteRfp,
  analyzeRfp, 
  getProposalDraft, 
  approveProposal 
} from '../services/api';
import './IntegratedWorkflow.css';

const IntegratedWorkflow = () => {
  const [rfps, setRfps] = useState([]);
  const [selectedRfp, setSelectedRfp] = useState(null);
  const [workflowState, setWorkflowState] = useState('idle'); // idle, analyzing, awaiting_approval, generating_pdf, complete
  const [agentProgress, setAgentProgress] = useState([]);
  const [rfpSummary, setRfpSummary] = useState(null);
  const [proposalDraft, setProposalDraft] = useState(null);
  const [editedSections, setEditedSections] = useState({});
  const [pdfInfo, setPdfInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);

  useEffect(() => {
    loadRfps();
  }, []);

  const loadRfps = async () => {
    try {
      const response = await fetchRfps();
      setRfps(response.data);
    } catch (err) {
      console.error('Error loading RFPs:', err);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      
      const response = await uploadRfpFile(formData);
      console.log('Upload response:', response.data);
      
      alert(`✅ RFP uploaded successfully! ID: ${response.data.rfp_id}`);
      setUploadFile(null);
      setShowUpload(false);
      loadRfps();
    } catch (err) {
      setError(`Upload failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const startWorkflow = async (rfp) => {
    setSelectedRfp(rfp);
    setWorkflowState('analyzing');
    setAgentProgress([]);
    setRfpSummary(null);
    setProposalDraft(null);
    setPdfInfo(null);
    setError(null);
    setLoading(true);

    // Initialize agent progress tracking
    const agents = [
      { name: 'Sales Agent', status: 'pending', icon: '💼' },
      { name: 'Technical Agent', status: 'pending', icon: '🔧' },
      { name: 'Pricing Agent', status: 'pending', icon: '💰' },
      { name: 'Proposal Agent', status: 'pending', icon: '📄' }
    ];
    setAgentProgress(agents);

    try {
      // Update progress: Sales Agent
      updateAgentStatus(0, 'running');
      
      // Call analyze endpoint - this runs all agents sequentially
      const response = await analyzeRfp(rfp.id);
      console.log('Analyze response:', response.data);

      // Update all agents to completed
      updateAgentStatus(0, 'completed');
      updateAgentStatus(1, 'completed');
      updateAgentStatus(2, 'completed');
      updateAgentStatus(3, 'completed');

      // Extract summary and draft
      if (response.data.rfp_summary) {
        setRfpSummary(response.data.rfp_summary);
      }

      if (response.data.proposal_draft) {
        setProposalDraft(response.data.proposal_draft);
        setEditedSections(response.data.proposal_draft.sections || {});
        setWorkflowState('awaiting_approval');
      } else if (response.data.pdf_generated) {
        // Old workflow - PDF already generated
        setPdfInfo(response.data.pdf_generated);
        setWorkflowState('complete');
      }

    } catch (err) {
      console.error('Workflow error:', err);
      setError(`Workflow failed: ${err.response?.data?.detail || err.message}`);
      setWorkflowState('idle');
    } finally {
      setLoading(false);
    }
  };

  const updateAgentStatus = (index, status) => {
    setAgentProgress(prev => {
      const updated = [...prev];
      if (updated[index]) {
        updated[index].status = status;
      }
      return updated;
    });
  };

  const handleSectionEdit = (sectionName, value) => {
    setEditedSections(prev => ({
      ...prev,
      [sectionName]: value
    }));
  };

  const handleApprove = async () => {
    if (!selectedRfp || !proposalDraft) return;

    setLoading(true);
    setWorkflowState('generating_pdf');
    setError(null);

    try {
      const approvalPayload = {
        title: proposalDraft.title || `Response Proposal for ${selectedRfp.title}`,
        sections: editedSections,
        approved: true
      };

      const response = await approveProposal(selectedRfp.id, approvalPayload);
      console.log('Approval response:', response.data);

      if (response.data.pdf_info) {
        setPdfInfo(response.data.pdf_info);
        setWorkflowState('complete');
        alert('✅ Proposal approved and PDF generated successfully!');
      }
    } catch (err) {
      console.error('Approval error:', err);
      setError(`Approval failed: ${err.response?.data?.detail || err.message}`);
      setWorkflowState('awaiting_approval');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = () => {
    if (window.confirm('Are you sure you want to reject this proposal? You will need to regenerate it.')) {
      setWorkflowState('idle');
      setProposalDraft(null);
      setEditedSections({});
    }
  };

  const resetWorkflow = () => {
    setSelectedRfp(null);
    setWorkflowState('idle');
    setAgentProgress([]);
    setRfpSummary(null);
    setProposalDraft(null);
    setEditedSections({});
    setPdfInfo(null);
    setError(null);
  };

  const handleDeleteRfp = async (rfpId, rfpTitle, event) => {
    // Stop propagation to prevent card click
    event.stopPropagation();
    
    if (!window.confirm(`Are you sure you want to delete "${rfpTitle}"? This action cannot be undone.`)) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await deleteRfp(rfpId);
      alert(`✅ RFP "${rfpTitle}" deleted successfully!`);
      
      // Reload RFP list
      loadRfps();
    } catch (err) {
      console.error('Delete error:', err);
      setError(`Failed to delete RFP: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="integrated-workflow">
      <div className="workflow-header">
        <h1> C.O.R.E - Integrated Agent Workflow</h1>
        <p>Complete RFP Processing: Upload → Analyze → Review → Approve → Generate PDF</p>
      </div>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      {/* RFP Selection or Upload */}
      {!selectedRfp && (
        <div className="rfp-selection-panel">
          <div className="panel-header">
            <h2>Step 1: Select or Upload RFP</h2>
            <button 
              className="btn-toggle"
              onClick={() => setShowUpload(!showUpload)}
            >
              {showUpload ? '📋 View Existing RFPs' : '📤 Upload New RFP'}
            </button>
          </div>

          {showUpload ? (
            <div className="upload-section">
              <h3>Upload RFP Document</h3>
              <div className="upload-area">
                <input 
                  type="file" 
                  accept=".pdf,.txt"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  disabled={loading}
                />
                {uploadFile && (
                  <div className="file-info">
                    <span>📄 {uploadFile.name}</span>
                    <button 
                      className="btn-primary"
                      onClick={handleFileUpload}
                      disabled={loading}
                    >
                      {loading ? 'Uploading...' : 'Upload'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="rfp-grid">
              {rfps.length === 0 ? (
                <div className="no-rfps">
                  <p>No RFPs found. Upload your first RFP to get started!</p>
                  <button 
                    className="btn-primary"
                    onClick={() => setShowUpload(true)}
                  >
                    Upload RFP
                  </button>
                </div>
              ) : (
                rfps.map(rfp => (
                  <div 
                    key={rfp.id} 
                    className="rfp-card"
                  >
                    <div className="rfp-card-header">
                      <h3>{rfp.title}</h3>
                      <div className="header-actions">
                        <span className={`badge badge-${rfp.status}`}>
                          {rfp.status}
                        </span>
                        <button 
                          className="btn-delete-small"
                          onClick={(e) => handleDeleteRfp(rfp.id, rfp.title, e)}
                          disabled={loading}
                          title="Delete RFP"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                    <p className="rfp-preview">
                      {rfp.content?.substring(0, 150)}...
                    </p>
                    <button 
                      className="btn-start"
                      onClick={() => startWorkflow(rfp)}
                      disabled={loading}
                    >
                      Start Processing →
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Workflow Progress */}
      {selectedRfp && (
        <div className="workflow-progress">
          <div className="progress-header">
            <h2>Processing: {selectedRfp.title}</h2>
            <button className="btn-reset" onClick={resetWorkflow}>
              ← Back to RFP List
            </button>
          </div>

          {/* Agent Progress Pipeline */}
          <div className="agent-pipeline">
            {agentProgress.map((agent, index) => (
              <div key={index} className={`agent-step agent-${agent.status}`}>
                <div className="agent-icon">{agent.icon}</div>
                <div className="agent-name">{agent.name}</div>
                <div className="agent-status-indicator">
                  {agent.status === 'pending' && '⏳'}
                  {agent.status === 'running' && '🔄'}
                  {agent.status === 'completed' && '✅'}
                </div>
              </div>
            ))}
          </div>

          {/* RFP Summary Display */}
          {rfpSummary && (
            <div className="summary-panel">
              <h3> RFP Summary (After Pricing)</h3>
              <div className="summary-grid">
                <div className="summary-card">
                  <h4> Sales Insights</h4>
                  <p>{rfpSummary.sales_insights?.substring(0, 200)}...</p>
                </div>
                <div className="summary-card">
                  <h4> Technical Solution</h4>
                  <p>{rfpSummary.technical_solution?.substring(0, 200)}...</p>
                </div>
                <div className="summary-card">
                  <h4> Pricing Summary</h4>
                  <p>{rfpSummary.pricing_summary?.substring(0, 200)}...</p>
                </div>
              </div>
            </div>
          )}

          {/* Proposal Draft Editor (HITL) */}
          {workflowState === 'awaiting_approval' && proposalDraft && (
            <div className="proposal-editor">
              <h3>✏️ Review & Edit Proposal Draft</h3>
              <p className="editor-instructions">
                Review the generated proposal below. You can edit any section before approving.
              </p>

              {Object.entries(editedSections).map(([sectionName, content]) => (
                <div key={sectionName} className="section-editor">
                  <label>{sectionName}</label>
                  <textarea
                    value={content}
                    onChange={(e) => handleSectionEdit(sectionName, e.target.value)}
                    rows={8}
                    placeholder={`Enter ${sectionName} content...`}
                  />
                </div>
              ))}

              <div className="approval-actions">
                <button 
                  className="btn-approve"
                  onClick={handleApprove}
                  disabled={loading}
                >
                  {loading ? 'Generating PDF...' : '✅ Approve & Generate PDF'}
                </button>
                <button 
                  className="btn-reject"
                  onClick={handleReject}
                  disabled={loading}
                >
                  ❌ Reject & Regenerate
                </button>
              </div>
            </div>
          )}

          {/* PDF Generated */}
          {workflowState === 'complete' && pdfInfo && (
            <div className="completion-panel">
              <div className="success-message">
                <h2>Workflow Complete!</h2>
                <p>Response proposal PDF has been generated and is ready to send to the client.</p>
              </div>

              <div className="pdf-info-card">
                <h3>📄 Generated PDF</h3>
                <div className="pdf-details">
                  <p><strong>Filename:</strong> {pdfInfo.filename}</p>
                  <p><strong>Size:</strong> {(pdfInfo.file_size / 1024).toFixed(2)} KB</p>
                  <p><strong>Status:</strong> {pdfInfo.message}</p>
                </div>
                <a 
                  href={pdfInfo.download_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="btn-download"
                >
                  📥 Download PDF
                </a>
              </div>

              <button 
                className="btn-new-rfp"
                onClick={resetWorkflow}
              >
                Process Another RFP
              </button>
            </div>
          )}

          {/* Loading State */}
          {loading && workflowState === 'analyzing' && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <p>Processing RFP through agent pipeline...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default IntegratedWorkflow;
