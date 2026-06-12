import { useState } from "react";
import IntegratedWorkflowNew from "../components/IntegratedWorkflowNew";
import AgentWorkflow from "../components/AgentWorkflow";

function ControlCenter() {
  const [activeTab, setActiveTab] = useState("integrated");

  return (
    <div className="control-center">
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === "integrated" ? "active" : ""}`}
          onClick={() => setActiveTab("integrated")}
        >
          Integrated Workflow (Full Pipeline)
        </button>
        <button
          className={`tab-btn ${activeTab === "stepwise" ? "active" : ""}`}
          onClick={() => setActiveTab("stepwise")}
        >
          Step-by-Step Mode
        </button>
      </div>

      {activeTab === "integrated" ? <IntegratedWorkflowNew /> : <AgentWorkflow />}
    </div>
  );
}

export default ControlCenter;
