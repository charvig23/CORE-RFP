import { useState } from "react";

function MasterAgentChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (!input) return;

    setMessages([
      ...messages,
      { role: "user", text: input },
      { role: "agent", text: "✅ Master Agent received your instruction." },
    ]);
    setInput("");
  };

  return (
    <div className="card">
      <h3>🧠 Master Agent Chat</h3>

      <div className="chat-box">
        {messages.map((m, i) => (
          <div key={i} className={m.role}>
            {m.text}
          </div>
        ))}
      </div>

      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}

export default MasterAgentChat;
