function HitlApproval({ onApprove }) {
  return (
    <div className="card">
      <h3>✅ Human Review Required</h3>
      <button onClick={onApprove}>Generate Proposal</button>
    </div>
  );
}

export default HitlApproval;
