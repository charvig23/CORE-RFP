import React, { useState, useEffect } from 'react';
import RfpUpload from './RfpUpload';
import { deleteRfp } from '../services/api';
import './AgentWorkflow.css';

const AgentWorkflow = () => {
  const [rfps, setRfps] = useState([]);
  const [selectedRfp, setSelectedRfp] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [executionResults, setExecutionResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState({});
  const [pipeline, setPipeline] = useState([]);
  const [showApproval, setShowApproval] = useState(false);
  const [lastOutput, setLastOutput] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [showProposalApproval, setShowProposalApproval] = useState(false);
  const [editedProposal, setEditedProposal] = useState('');
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [finalProposal, setFinalProposal] = useState(null); // Stores proposal text + PDF link
  const [showFinalOutput, setShowFinalOutput] = useState(false);

  // Fetch RFPs on mount
  useEffect(() => {
    fetchRfps();
    fetchPipeline();
  }, []);

  const fetchRfps = async () => {
    try {
      const response = await fetch('http://localhost:8000/rfp/list');
      const data = await response.json();
      setRfps(data);
    } catch (error) {
      console.error('Error fetching RFPs:', error);
    }
  };

  const fetchPipeline = async () => {
    try {
      const response = await fetch('http://localhost:8000/workflow/pipeline');
      const data = await response.json();
      setPipeline(data.pipeline);
    } catch (error) {
      console.error('Error fetching pipeline:', error);
    }
  };

  const selectRfp = async (rfp) => {
    setSelectedRfp(rfp);
    setExecutionResults([]);
    setCurrentStep(0);
    setContext({});
    setShowApproval(false);
    setLastOutput(null);

    // Fetch current state
    try {
      const response = await fetch(`http://localhost:8000/workflow/${rfp.id}/current-state`);
      const data = await response.json();
      setCurrentStep(data.current_step);
      
      // Load existing outputs
      const results = [];
      if (data.outputs.sales_summary) {
        results.push({ step: 0, agent: 'Sales Agent', output: data.outputs.sales_summary });
      }
      if (data.outputs.technical_matches) {
        results.push({ step: 1, agent: 'Technical Agent', output: data.outputs.technical_matches });
      }
      if (data.outputs.pricing_data) {
        results.push({ step: 2, agent: 'Pricing Agent', output: data.outputs.pricing_data });
      }
      if (data.outputs.final_proposal) {
        results.push({ step: 3, agent: 'Proposal Assembly Agent', output: data.outputs.final_proposal });
      }
      setExecutionResults(results);
    } catch (error) {
      console.error('Error fetching workflow state:', error);
    }
  };

  const executeStep = async () => {
    if (!selectedRfp || currentStep >= pipeline.length) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/workflow/execute-step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rfp_id: selectedRfp.id,
          step_index: currentStep,
          context: context
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Add result to execution history
      setExecutionResults([...executionResults, {
        step: currentStep,
        agent: data.agent_name,
        output: data.output,
        timestamp: new Date().toLocaleTimeString()
      }]);

      // Update context for next agent
      setContext(data.current_context);
      setLastOutput(data);
      
      // Check if this is the proposal agent (step 3)
      if (currentStep === 3) {
        // Proposal agent completed - show HITL approval for PDF generation
        const proposalText = data.output.agent_response || '';
        setEditedProposal(proposalText);
        setShowProposalApproval(true);
        setShowApproval(false);
      } else if (data.has_next_step) {
        // Show approval dialog for next agent
        setShowApproval(true);
      } else {
        // Workflow complete
        alert('✅ Workflow completed! All agents have processed the RFP.');
      }
      
    } catch (error) {
      console.error('Error executing agent:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const approveNextStep = () => {
    setCurrentStep(currentStep + 1);
    setShowApproval(false);
    setLastOutput(null);
  };

  const rejectNextStep = () => {
    setShowApproval(false);
    alert('⛔ Workflow stopped. You can review the results so far.');
  };

  const resetWorkflow = () => {
    setSelectedRfp(null);
    setCurrentStep(0);
    setExecutionResults([]);
    setContext({});
    setShowApproval(false);
    setLastOutput(null);
    setShowProposalApproval(false);
    setEditedProposal('');
    setFinalProposal(null);
    setShowFinalOutput(false);
  };

  const handleUploadSuccess = (data) => {
    // Refresh RFP list
    fetchRfps();
    setShowUpload(false);
  };

  const handleApproveProposal = async () => {
    if (!selectedRfp) return;

    setGeneratingPdf(true);
    try {
      const response = await fetch(`http://localhost:8000/workflow/${selectedRfp.id}/approve-proposal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved: true,
          edited_proposal: editedProposal
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Store final proposal data
      setFinalProposal({
        proposalText: data.proposal_text,
        pdfFilename: data.pdf_filename,
        pdfUrl: data.pdf_download_link,
        message: data.message
      });
      
      // Hide approval dialog and show final output
      setShowProposalApproval(false);
      setShowFinalOutput(true);
      setCurrentStep(4); // Mark as completed
      
    } catch (error) {
      console.error('Error approving proposal:', error);
      alert(`Error generating PDF: ${error.message}`);
    } finally {
      setGeneratingPdf(false);
    }
  };

  const handleRejectProposal = () => {
    setShowProposalApproval(false);
    alert('⛔ Proposal rejected. You can re-execute the proposal agent or make manual edits.');
  };

  const handleDeleteRfp = async (rfpId, rfpTitle, event) => {
    event.stopPropagation(); // Prevent card click when clicking delete
    
    if (!window.confirm(`Are you sure you want to delete "${rfpTitle}"?\n\nThis will permanently remove:\n• RFP document\n• All analysis results\n• Generated proposals\n\nThis action cannot be undone.`)) {
      return;
    }

    try {
      await deleteRfp(rfpId);
      
      // Remove from local state
      setRfps(rfps.filter(rfp => rfp.id !== rfpId));
      
      // If deleted RFP was selected, reset workflow
      if (selectedRfp?.id === rfpId) {
        resetWorkflow();
      }
      
      alert(`✅ "${rfpTitle}" has been deleted successfully.`);
    } catch (err) {
      console.error('Delete error:', err);
      alert(`Failed to delete RFP: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div className="agent-workflow">
      <h2> Agent Workflow - Step-by-Step Execution</h2>

      {/* RFP Selection */}
      {!selectedRfp ? (
        <div className="rfp-selection">
          <div className="selection-header">
            <h3>Select an RFP to Process</h3>
            <button 
              className="btn-primary btn-upload"
              onClick={() => setShowUpload(!showUpload)}
            >
              {showUpload ? '📋 View RFPs' : '📤 Upload New RFP'}
            </button>
          </div>

          {/* Upload Component */}
          {showUpload && (
            <RfpUpload onUploadSuccess={handleUploadSuccess} />
          )}

          {/* RFP List */}
          {!showUpload && (
            <div className="rfp-list">
              {rfps.length === 0 ? (
                <div className="no-rfps">
                  <p>No RFPs available.</p>
                  <button 
                    className="btn-primary"
                    onClick={() => setShowUpload(true)}
                  >
                    Upload Your First RFP
                  </button>
                </div>
              ) : (
                rfps.map((rfp) => (
                  <div key={rfp.id} className="rfp-card" onClick={() => selectRfp(rfp)}>
                    <div className="rfp-card-header">
                      <h4>{rfp.title}</h4>
                      <button
                        className="btn-delete-rfp"
                        onClick={(e) => handleDeleteRfp(rfp.id, rfp.title, e)}
                        title="Delete RFP"
                      >
                        🗑️
                      </button>
                    </div>
                    <div className="rfp-card-content">
                      <span className={`status-badge ${rfp.status}`}>
                        {rfp.status === 'completed' ? '✅ COMPLETED' : 
                         rfp.status === 'processing' ? '🔄 PROCESSING' :
                         rfp.status === 'pending' ? '⏳ PENDING' : 
                         rfp.status.toUpperCase()}
                      </span>
                      <p className="rfp-meta">
                        Uploaded: {new Date(rfp.created_at || Date.now()).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Selected RFP Header */}
          <div className="selected-rfp-header">
            <div className="rfp-info">
              <h3>📄 {selectedRfp.title}</h3>
              <button className="btn-secondary" onClick={resetWorkflow}>
                ← Select Different RFP
              </button>
            </div>
          </div>

          {/* Pipeline Progress */}
          <div className="pipeline-progress">
            <h4>Agent Pipeline Progress</h4>
            <div className="progress-bar">
              {pipeline.map((agent, index) => (
                <div
                  key={index}
                  className={`progress-step ${
                    index < currentStep ? 'completed' : 
                    index === currentStep ? 'active' : 
                    'pending'
                  }`}
                >
                  <div className="step-number">{index + 1}</div>
                  <div className="step-name">{agent.display}</div>
                  <div className="step-description">{agent.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Current Step Execution */}
          {currentStep < pipeline.length && !showApproval && (
            <div className="execution-panel">
              <h4>
                Current Step: {pipeline[currentStep]?.display}
              </h4>
              <p className="step-description">
                {pipeline[currentStep]?.description}
              </p>
              <button
                className="btn-primary btn-execute"
                onClick={executeStep}
                disabled={loading}
              >
                {loading ? '⏳ Executing Agent...' : `▶️ Execute ${pipeline[currentStep]?.display}`}
              </button>
            </div>
          )}

          {/* Human-in-the-Loop Approval */}
          {showApproval && lastOutput && (
            <div className="approval-dialog">
              <h3>Agent Execution Complete!</h3>
              <div className="output-preview">
                <h4>Output from {lastOutput.agent_name}:</h4>
                <pre>{JSON.stringify(lastOutput.output, null, 2)}</pre>
              </div>
              
              {lastOutput.has_next_step && (
                <>
                  <h4>Next Agent: {lastOutput.next_agent?.display}</h4>
                  <p>{lastOutput.next_agent?.description}</p>
                  
                  <div className="approval-buttons">
                    <button className="btn-success" onClick={approveNextStep}>
                      ✓ Approve & Continue to Next Agent
                    </button>
                    <button className="btn-danger" onClick={rejectNextStep}>
                      ✗ Stop Here
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Proposal HITL Approval for PDF Generation */}
          {showProposalApproval && !showFinalOutput && (
            <div className="proposal-approval-dialog">
              <h3>📄 Proposal Draft Ready for Review</h3>
              <p className="approval-instruction">
                Review the proposal below. You can edit the text before generating the PDF.
                Click "Generate PDF" to approve, or "Reject" to stop.
              </p>

              <div className="proposal-editor">
                <label>
                  <strong>Proposal Content (Editable):</strong>
                </label>
                <textarea
                  value={editedProposal}
                  onChange={(e) => setEditedProposal(e.target.value)}
                  rows={20}
                  className="proposal-text-editor"
                  placeholder="Edit the proposal here..."
                />
              </div>

              <div className="approval-buttons">
                <button 
                  className="btn-success btn-generate-pdf"
                  onClick={handleApproveProposal}
                  disabled={generatingPdf}
                >
                  {generatingPdf ? ' Generating PDF...' : '✓ Generate PDF'}
                </button>
                <button 
                  className="btn-danger" 
                  onClick={handleRejectProposal}
                  disabled={generatingPdf}
                >
                  ✗ Reject
                </button>
              </div>
            </div>
          )}

          {/* Final Proposal Output - Email-like display with PDF download */}
          {showFinalOutput && finalProposal && (
            <div className="final-proposal-output">
              <div className="output-header">
                <h3>✅ Proposal Generated Successfully</h3>
                <p className="success-message">{finalProposal.message}</p>
              </div>

              <div className="proposal-email-view">
                <div className="email-header">
                  <h4>📧 Final Proposal (Email Format)</h4>
                  <button 
                    className="btn-copy"
                    onClick={() => {
                      navigator.clipboard.writeText(finalProposal.proposalText);
                      alert('Proposal text copied to clipboard!');
                    }}
                  >
                    📋 Copy Text
                  </button>
                </div>
                <pre className="proposal-email-text">{finalProposal.proposalText}</pre>
              </div>

              <div className="pdf-download-section">
                <h4>📄 Download PDF Version</h4>
                <div className="pdf-info">
                  <span className="pdf-filename">📎 {finalProposal.pdfFilename}</span>
                  <a 
                    href={finalProposal.pdfUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-download-pdf"
                  >
                    ⬇️ Download PDF
                  </a>
                </div>
              </div>

              <div className="action-buttons">
                <button className="btn-primary" onClick={resetWorkflow}>
                  📝 Process Another RFP
                </button>
              </div>
            </div>
          )}

          {/* Execution History */}
          {executionResults.length > 0 && (
            <div className="execution-history">
              <h4>Execution History</h4>
              {executionResults.map((result, index) => (
                <div key={index} className="result-card">
                  <div className="result-header">
                    <span className="result-agent">
                      {result.agent}
                    </span>
                    <span className="result-time">{result.timestamp}</span>
                  </div>
                  <div className="result-output">
                    <strong>Output:</strong>
                    <pre>{JSON.stringify(result.output, null, 2)}</pre>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Completion Message */}
          {currentStep >= pipeline.length && executionResults.length > 0 && (
            <div className="completion-message">
              <h3>Workflow Complete!</h3>
              <p>All agents have successfully processed the RFP.</p>
              <button className="btn-primary" onClick={resetWorkflow}>
                Process Another RFP
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AgentWorkflow;
