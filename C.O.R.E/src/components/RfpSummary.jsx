function RfpSummary({ summary }) {
  if (!summary) return null;

  return (
    <div className="card">
      <h3>📄 RFP Summary</h3>
      <p>
        <b>Client:</b> {summary.client}
      </p>
      <ul>
        {summary.objectives.map((o, i) => (
          <li key={i}>{o}</li>
        ))}
      </ul>
    </div>
  );
}

export default RfpSummary;
