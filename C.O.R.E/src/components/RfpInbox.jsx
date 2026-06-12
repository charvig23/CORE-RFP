function RfpInbox({ rfps, onSelect }) {
  return (
    <div className="card">
      <h3>📥 Detected RFPs (Sales Agent)</h3>
      {rfps.map((rfp) => (
        <div key={rfp.id} className="rfp-item" onClick={() => onSelect(rfp)}>
          {rfp.title}
        </div>
      ))}
    </div>
  );
}

export default RfpInbox;
