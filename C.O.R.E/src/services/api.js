import axios from 'axios';

const API = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

const SKU_API = axios.create({
  baseURL: 'http://127.0.0.1:8080',
});

// RFP endpoints
export const uploadRFP = (formData) => API.post('/rfp/upload', formData);
export const getRFPStatus = (rfpId) => API.get(`/rfp/${rfpId}/status`);
export const getRFP = (rfpId) => API.get(`/rfp/${rfpId}`);
export const listRFPs = () => API.get('/rfp/list/all');
export const approveProposal = (rfpId, data) => API.post(`/rfp/${rfpId}/approve-proposal`, data);

// Agent endpoints
export const listAgents = () => API.get('/agents/list');

// SKU endpoints
export const matchSKU = (query) => SKU_API.post('/api/match-sku', { query, top_n: 5 });
export const getPricing = (skus) => SKU_API.post('/api/get-pricing', { skus });