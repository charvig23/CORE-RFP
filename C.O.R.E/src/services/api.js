import axios from "axios";

export const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

const SKU_API = axios.create({
  baseURL: (process.env.REACT_APP_TOOLS_BASE || "http://127.0.0.1:8080"),
  timeout: 30000,
});

// RFPs
export const fetchRfps = () => API.get("/rfp/list");
export const uploadRfpFile = (formData) => API.post("/rfp/upload-file", formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const deleteRfp = (rfp_id) => API.delete(`/rfp/${rfp_id}`);
export const analyzeRfp = (rfp_id) => API.post(`/rfp/${rfp_id}/analyze`);
export const getRfpStatus = (rfp_id) => API.get(`/rfp/${rfp_id}/status`);
export const getRfp = (rfp_id) => API.get(`/rfp/${rfp_id}`);
export const getProposalDraft = (rfp_id) => API.get(`/rfp/${rfp_id}/proposal-draft`);
export const approveProposal = (rfp_id, editedProposal) => 
  API.post(`/rfp/${rfp_id}/approve-proposal`, editedProposal);
export const getFinalProposal = (rfp_id) => API.get(`/rfp/${rfp_id}/proposal`);

// Agent Chat
export function executeAgent(agentId, payload) {
  if (typeof agentId === "object" && payload === undefined) {
    const body = agentId;
    const resolvedAgentId = body.agent_id;
    if (!resolvedAgentId) {
      throw new Error("agent_id is required");
    }
    return API.post(`/agents/${resolvedAgentId}/execute`, body);
  }

  const body = {
    agent_id: agentId,
    ...(payload || {}),
  };

  return API.post(`/agents/${agentId}/execute`, body);
}

// SKU Matching
export const matchSku = (payload) => SKU_API.post("/api/match-sku", payload);
export const validateSku = (sku_code) => SKU_API.post("/api/validate-sku", { sku_code });
export const checkSkuHealth = () => SKU_API.get("/api/health");

// Workflow - Step-by-step agent execution
export const executeWorkflowStep = (payload) => API.post("/workflow/execute-step", payload);
export const getWorkflowPipeline = () => API.get("/workflow/pipeline");
export const getWorkflowState = (rfp_id) => API.get(`/workflow/${rfp_id}/current-state`);

export default API;
