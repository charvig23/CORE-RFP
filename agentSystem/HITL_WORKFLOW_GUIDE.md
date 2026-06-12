# Human-in-the-Loop (HITL) Proposal Approval Workflow

## Overview
The system now requires human approval before generating the final PDF. This ensures the proposal is reviewed and edited before sending to the client.

## Workflow Steps

### Step 1: Process RFP (Generates Draft)
**Endpoint:** `POST http://localhost:8000/rfp/{rfp_id}/analyze`

This will process the RFP through all agents and stop at proposal generation WITHOUT creating a PDF.

**Response:**
```json
{
  "status": "RFP processed successfully",
  "rfp_id": 1,
  "rfp_summary": {
    "rfp_title": "Retail Paint Procurement",
    "rfp_id": 1,
    "sales_insights": "Customer requires high-quality paint products...",
    "technical_solution": "Matched SKUs: SKU001, SKU002...",
    "pricing_summary": "Total cost: ₹150,000...",
    "status": "pricing_completed"
  },
  "proposal_draft": {
    "title": "Response Proposal for Retail Paint Procurement",
    "sections": {
      "Executive Summary": "We are pleased to submit our proposal...",
      "Understanding of Requirements": "• Client needs durable paint\n• Budget: ₹200,000\n• Timeline: 2 weeks",
      "Proposed Solution": "• Asian Paints Premium Interior\n• Weather resistant coating\n• Professional grade finish",
      "Pricing Details": "• SKU001 - Asian Paints Royale - Qty: 50 - Price: ₹2,400\n• SKU002 - Weather Coat - Qty: 30 - Price: ₹1,800\n• Total: ₹150,000",
      "Payment Terms": "• 30% advance\n• 40% on delivery\n• 30% post installation",
      "Implementation Timeline": "• Week 1: Procurement\n• Week 2: Delivery and installation",
      "Terms and Conditions": "• Warranty: 2 years\n• Validity: 30 days"
    },
    "metadata": {
      "generated_at": "2025-12-13T10:30:00",
      "status": "draft",
      "editable": true
    }
  },
  "requires_approval": true
}
```

---

### Step 2: Get Editable Draft
**Endpoint:** `GET http://localhost:8000/rfp/{rfp_id}/proposal-draft`

Retrieve the proposal draft for review and editing.

**Response:**
```json
{
  "rfp_id": 1,
  "title": "Retail Paint Procurement",
  "proposal_draft": {
    "title": "Response Proposal for Retail Paint Procurement",
    "sections": {
      "Executive Summary": "We are pleased to submit our proposal...",
      "Understanding of Requirements": "• Client needs durable paint\n• Budget: ₹200,000\n• Timeline: 2 weeks",
      "Proposed Solution": "• Asian Paints Premium Interior\n• Weather resistant coating\n• Professional grade finish",
      "Pricing Details": "• SKU001 - Asian Paints Royale - Qty: 50 - Price: ₹2,400\n• SKU002 - Weather Coat - Qty: 30 - Price: ₹1,800\n• Total: ₹150,000",
      "Payment Terms": "• 30% advance\n• 40% on delivery\n• 30% post installation",
      "Implementation Timeline": "• Week 1: Procurement\n• Week 2: Delivery and installation",
      "Terms and Conditions": "• Warranty: 2 years\n• Validity: 30 days"
    },
    "metadata": {
      "generated_at": "2025-12-13T10:30:00",
      "status": "draft",
      "editable": true
    }
  },
  "approval_status": "pending",
  "status": "awaiting_approval",
  "instructions": "Edit the sections as needed, then POST to /rfp/1/approve-proposal with the edited content"
}
```

---

### Step 3: Edit and Approve (Generates PDF)
**Endpoint:** `POST http://localhost:8000/rfp/{rfp_id}/approve-proposal`

**Headers:**
```
Content-Type: application/json
```

**Request Body (EDITABLE SAMPLE):**
```json
{
  "title": "Response Proposal for Retail Paint Procurement",
  "sections": {
    "Executive Summary": "We are pleased to submit our comprehensive proposal for your paint procurement needs. Our solution offers premium quality products with competitive pricing and reliable delivery.",
    "Understanding of Requirements": "• Client requires high-quality, durable paint products\n• Budget allocation: ₹200,000\n• Delivery timeline: 2 weeks\n• Focus on weather-resistant solutions\n• Professional-grade finish required",
    "Proposed Solution": "• Asian Paints Royale Premium Interior - Superior finish and durability\n• Weather Shield Exterior Coating - 10-year protection guarantee\n• Professional-grade application tools included\n• Color consultation service provided\n• Technical support throughout installation",
    "Pricing Details": "• SKU001 - Asian Paints Royale (Premium) - Qty: 50 units - Unit Price: ₹2,400 - Subtotal: ₹120,000\n• SKU002 - Weather Shield Coating - Qty: 30 units - Unit Price: ₹1,800 - Subtotal: ₹54,000\n• Application Tools & Accessories - ₹8,000\n• Technical Consultation - Complimentary\n• Subtotal: ₹182,000\n• GST (18%): ₹32,760\n• Grand Total: ₹214,760",
    "Payment Terms": "• 30% advance payment (₹64,428) - Upon order confirmation\n• 40% on delivery (₹85,904) - Before unloading\n• 30% post-installation (₹64,428) - Within 7 days of completion\n• Payment methods: Bank transfer, Cheque, or UPI\n• Late payment penalty: 2% per month",
    "Implementation Timeline": "• Day 1-2: Order processing and quality check\n• Day 3-5: Manufacturing and packaging\n• Day 6-7: Transportation and delivery\n• Day 8-10: Installation and application support\n• Day 11-14: Quality inspection and final touches\n• Total Duration: 14 days from order confirmation",
    "Terms and Conditions": "• Product Warranty: 2 years against manufacturing defects\n• Price Validity: 30 days from proposal date\n• Delivery Terms: FOB Destination\n• Force Majeure: Standard clauses apply\n• Dispute Resolution: Arbitration in Delhi jurisdiction\n• Cancellation Policy: 10% cancellation fee if canceled after confirmation"
  },
  "approved": true
}
```

**Response (Success):**
```json
{
  "status": "Proposal approved and PDF generated",
  "rfp_id": 1,
  "pdf_info": {
    "filename": "proposal_rfp_Retail_Paint_Procurement.pdf",
    "file_path": "C:\\...\\proposals\\proposal_rfp_Retail_Paint_Procurement.pdf",
    "download_url": "http://localhost:8080/proposals/proposal_rfp_Retail_Paint_Procurement.pdf",
    "file_size": 5248
  },
  "message": "Response PDF ready to send to client"
}
```

---

## Postman Collection Setup

### Collection: RFP HITL Workflow

#### 1. Analyze RFP (Generate Draft)
- **Method:** POST
- **URL:** `http://localhost:8000/rfp/1/analyze`
- **Body:** None
- **Test Script:**
```javascript
pm.test("Draft generated", function() {
    pm.response.to.have.status(200);
    pm.expect(pm.response.json().requires_approval).to.eql(true);
});
```

#### 2. Get Draft for Review
- **Method:** GET
- **URL:** `http://localhost:8000/rfp/1/proposal-draft`
- **Body:** None

#### 3. Approve with Edits
- **Method:** POST
- **URL:** `http://localhost:8000/rfp/1/approve-proposal`
- **Headers:** `Content-Type: application/json`
- **Body:** (Copy the editable sample above)

---

## Key Features

1. **Editable Sections**: All proposal sections can be modified before PDF generation
2. **Structured Format**: Content organized in clear sections for easy editing
3. **Human Review**: Mandatory approval step ensures quality control
4. **Real-time Changes**: Edit pricing, terms, timeline, or any content
5. **PDF Generation**: Only happens after human approval

## UI Integration

For frontend integration, display the proposal draft in a form with:
- Text areas for each section
- Save draft button (optional)
- Approve & Generate PDF button
- Reject & Regenerate button

Example UI Flow:
```
[RFP Analysis] → [Draft Generated] → [Human Review & Edit] → [Approve] → [PDF Generated]
                                   ↓
                              [Reject & Regenerate]
```

## Status Transitions

```
uploaded → analyzing → awaiting_approval → approved → completed
                    ↓
               revision_needed (if rejected)
```
