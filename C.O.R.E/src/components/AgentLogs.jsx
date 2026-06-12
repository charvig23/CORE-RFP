function AgentLogs({ logs }) {
  return (
    <div className="card">
      <h3>⚙️ Agent Processing</h3>
      {logs.map((log, i) => (
        <p key={i}>
          {log.agent} → <b>{log.status}</b>
        </p>
      ))}
    </div>
  );
}

export default AgentLogs;
