from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import pandas as pd
import re
from difflib import SequenceMatcher
import os
import io
from datetime import datetime

# PDF generation support using xhtml2pdf
try:
    from xhtml2pdf import pisa
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠ Warning: xhtml2pdf not installed. PDF generation disabled. Run: pip install xhtml2pdf")

# ReportLab for direct PDF generation (no HTML)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠ Warning: reportlab not installed. Direct PDF generation disabled. Run: pip install reportlab")

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Config: paths to your CSVs
# Update these paths to your actual CSV file locations
SKU_CSV = os.getenv("SKU_CSV_PATH", "sku_master.csv")
PRICING_CSV = os.getenv("PRICING_CSV_PATH", "pricing.csv")

# Load CSVs at startup
try:
    skus_df = pd.read_csv(SKU_CSV)
    pricing_df = pd.read_csv(PRICING_CSV)
    print(f"✓ Loaded SKU data: {len(skus_df)} records")
    print(f"✓ Loaded pricing data: {len(pricing_df)} records")
except FileNotFoundError as e:
    print(f"⚠ Warning: CSV file not found - {e}")
    skus_df = pd.DataFrame()
    pricing_df = pd.DataFrame()

def normalize(text):
    """Normalize text for comparison"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def token_set(text):
    """Convert text to set of tokens"""
    return set(normalize(text).split())

def fuzzy_ratio(a, b):
    """Calculate fuzzy similarity ratio between two strings"""
    return SequenceMatcher(None, a, b).ratio()

def build_search_text(row):
    """Build searchable text from SKU row"""
    parts = []
    for c in ['product_name', 'description', 'category', 'type', 'tags']:
        if c in row and pd.notna(row[c]):
            parts.append(str(row[c]))
    return normalize(" ".join(parts))

# Precompute search_text & ensure SKU identifier exists
if not skus_df.empty:
    if 'search_text' not in skus_df.columns:
        skus_df['search_text'] = skus_df.apply(build_search_text, axis=1)
    if 'sku_code' not in skus_df.columns:
        # Use first column as SKU code if not explicitly named
        skus_df['sku_code'] = skus_df.iloc[:, 0]

# Find pricing SKU column
pricing_key = None
if not pricing_df.empty:
    for c in pricing_df.columns:
        if 'sku' in c.lower():
            pricing_key = c
            break

def score_match(requirement, row):
    """
    Score how well a SKU row matches a requirement.
    Returns: (normalized_score, raw_score, similarity)
    """
    req_norm = normalize(requirement)
    req_tokens = token_set(req_norm)
    text = row['search_text']
    text_tokens = token_set(text)
    score = 0.0
    max_score = 12.0

    # Category heuristics
    if 'interior' in req_tokens and 'interior' in text_tokens:
        score += 3
    if 'exterior' in req_tokens and 'exterior' in text_tokens:
        score += 3
    if 'outer' in req_tokens and 'exterior' in text_tokens:
        score += 2

    # Type heuristics - paint-specific keywords
    types = ['primer', 'emulsion', 'enamel', 'sealer', 'undercoat', 'paint', 'varnish']
    for t in types:
        if t in req_tokens and t in text_tokens:
            score += 4
        elif t in req_tokens:
            if fuzzy_ratio(t, text) > 0.75:
                score += 2

    # Token overlap scoring
    overlap = req_tokens.intersection(text_tokens)
    score += min(len(overlap) * 1.0, 3.0)

    # Fuzzy whole-string similarity
    sim = fuzzy_ratio(req_norm, text)
    score += sim * 2.0

    # Normalize score
    if score > max_score:
        score = max_score
    normalized = score / max_score
    
    return normalized, score, sim

@app.route("/api/match-sku", methods=["POST"])
def match_sku():
    """
    Match SKUs based on requirements.
    
    Request body:
    {
        "requirements": ["requirement1", "requirement2"],
        "top_k": 3,  // optional, defaults to 3
        "include_pricing": true  // optional, defaults to true
    }
    """
    data = request.get_json()
    
    if not data or 'requirements' not in data:
        return jsonify({"error": "Payload must include 'requirements' list"}), 400
    
    if skus_df.empty:
        return jsonify({"error": "SKU data not loaded. Please configure CSV paths."}), 500
    
    requirements = data['requirements']
    top_k = data.get('top_k', 3)
    include_pricing = data.get('include_pricing', True)
    
    output = []
    
    for req in requirements:
        candidates = []
        
        # Score each SKU against the requirement
        for _, row in skus_df.iterrows():
            norm_score, raw, sim = score_match(req, row)
            
            candidate = {
                "sku": str(row['sku_code']),
                "product_name": str(row.get('product_name', '')),
                "description": str(row.get('description', '')),
                "score": round(norm_score, 4),
                "raw_score": round(raw, 2),
                "similarity": round(sim, 4),
            }
            
            # Attach pricing if available and requested
            if include_pricing and not pricing_df.empty and pricing_key:
                prows = pricing_df[pricing_df[pricing_key] == row['sku_code']]
                if len(prows) > 0:
                    p = prows.iloc[0]
                    
                    # Detect price column
                    price_col = next((c for c in pricing_df.columns 
                                     if 'price' in c.lower() or 'amount' in c.lower()), None)
                    if price_col:
                        candidate['price'] = float(p[price_col])
                    
                    # Detect GST column
                    gst_col = next((c for c in pricing_df.columns 
                                   if 'gst' in c.lower()), None)
                    if gst_col:
                        candidate['gst'] = float(p[gst_col])
            
            candidates.append(candidate)
        
        # Sort by score and similarity, take top_k
        candidates = sorted(candidates, 
                          key=lambda x: (x['score'], x['similarity']), 
                          reverse=True)[:top_k]
        
        output.append({
            "requirement": req,
            "matches": candidates
        })
    
    return jsonify({"matches": output})

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "sku_records": len(skus_df),
        "pricing_records": len(pricing_df),
        "sku_csv": SKU_CSV,
        "pricing_csv": PRICING_CSV
    })

@app.route("/api/validate-sku", methods=["POST"])
def validate_sku():
    """
    Validate if a SKU exists and return its details.
    
    Request body:
    {
        "sku_code": "SKU123"
    }
    """
    data = request.get_json()
    
    if not data or 'sku_code' not in data:
        return jsonify({"error": "Payload must include 'sku_code'"}), 400
    
    if skus_df.empty:
        return jsonify({"error": "SKU data not loaded"}), 500
    
    sku_code = data['sku_code']
    sku_row = skus_df[skus_df['sku_code'] == sku_code]
    
    if len(sku_row) == 0:
        return jsonify({"valid": False, "error": "SKU not found"}), 404
    
    sku_info = sku_row.iloc[0].to_dict()
    
    # Add pricing if available
    if not pricing_df.empty and pricing_key:
        prows = pricing_df[pricing_df[pricing_key] == sku_code]
        if len(prows) > 0:
            sku_info['pricing'] = prows.iloc[0].to_dict()
    
    return jsonify({"valid": True, "sku": sku_info})

@app.route("/api/extract-sales-objectives", methods=["POST"])
def extract_sales_objectives():
    """
    Extract sales objectives and requirements from RFP text.
    
    Request body:
    {
        "rfp_text": "The complete RFP content..."
    }
    """
    data = request.get_json()
    
    if not data or 'rfp_text' not in data:
        return jsonify({"error": "Payload must include 'rfp_text'"}), 400
    
    rfp_text = data['rfp_text']
    
    result = {
        "objectives": [],
        "requirements": [],
        "extracted_requirements": [],
        "scope": "",
        "budget_info": "",
        "timeline": "",
        "stakeholders": [],
        "compliance": [],
        "key_terms": []
    }
    
    lines = rfp_text.split('\n')
    current_section = None
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Detect sections
        if 'objective' in line_lower or 'goal' in line_lower:
            current_section = 'objectives'
        elif 'requirement' in line_lower or 'specification' in line_lower:
            current_section = 'requirements'
        elif 'scope' in line_lower:
            current_section = 'scope'
        elif 'budget' in line_lower or 'cost' in line_lower or '₹' in line or '$' in line:
            current_section = 'budget'
        elif 'timeline' in line_lower or 'schedule' in line_lower or 'deadline' in line_lower:
            current_section = 'timeline'
        elif 'stakeholder' in line_lower or 'contact' in line_lower:
            current_section = 'stakeholders'
        
        # Extract content
        if line.strip() and not line_lower.startswith(('project', 'rfp', '===', '---')):
            if current_section == 'objectives' and len(line.strip()) > 20:
                result['objectives'].append(line.strip())
            elif current_section == 'requirements' and len(line.strip()) > 15:
                result['requirements'].append(line.strip())
                result['extracted_requirements'].append(line.strip())
            elif current_section == 'scope':
                result['scope'] += line.strip() + ' '
            elif current_section == 'budget':
                result['budget_info'] += line.strip() + ' '
            elif current_section == 'timeline':
                result['timeline'] += line.strip() + ' '
    
    # Extract product requirements using keywords
    product_keywords = ['paint', 'emulsion', 'primer', 'coating', 'finish', 'sealer', 'product']
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in product_keywords):
            if len(line.strip()) > 10 and line.strip() not in result['extracted_requirements']:
                result['extracted_requirements'].append(line.strip())
    
    # Clean up
    result['scope'] = result['scope'].strip()[:500]
    result['budget_info'] = result['budget_info'].strip()[:200]
    result['timeline'] = result['timeline'].strip()[:200]
    
    # If no requirements found, add a default
    if not result['extracted_requirements']:
        result['extracted_requirements'] = ["General construction/painting supplies as per RFP"]
    
    result['status'] = 'success'
    result['extracted_count'] = len(result['extracted_requirements'])
    
    return jsonify(result)

@app.route("/api/calculate-total-cost", methods=["POST"])
def calculate_total_cost():
    """
    Calculate total cost with taxes and discounts.
    
    Request body:
    {
        "items": [{"price": 100, "quantity": 2}, ...],
        "tax_rate": 0.18,  // optional, defaults to 18%
        "discount": 5  // optional, discount percentage
    }
    """
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({"error": "Payload must include 'items' list"}), 400
    
    items = data['items']
    tax_rate = data.get('tax_rate', 0.18)
    discount = data.get('discount', 0)
    
    subtotal = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
    discount_amount = subtotal * (discount / 100)
    after_discount = subtotal - discount_amount
    tax = after_discount * tax_rate
    total = after_discount + tax
    
    return jsonify({
        "subtotal": round(subtotal, 2),
        "discount": round(discount_amount, 2),
        "tax": round(tax, 2),
        "total": round(total, 2)
    })

@app.route('/api/format-proposal-html', methods=['POST'])
def format_proposal_html():
    """Format proposal sections into professional HTML document"""
    data = request.json
    title = data.get('title', 'Business Proposal')
    sections = data.get('sections', {})
    
    # Improved HTML template with better summary styling
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 40px; 
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h2 {{ 
            color: #34495e; 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        .executive-summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 25px 0;
        }}
        .executive-summary h2 {{
            color: white;
            border-bottom: 2px solid rgba(255,255,255,0.3);
        }}
        .executive-summary ul {{
            list-style: none;
            padding: 0;
            margin: 15px 0;
        }}
        .executive-summary li {{
            padding: 10px 0 10px 30px;
            position: relative;
            font-size: 16px;
        }}
        .executive-summary li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #4CAF50;
            font-weight: bold;
            font-size: 20px;
        }}
        .section {{
            margin: 25px 0;
            padding: 20px;
            background: #f9f9f9;
            border-left: 4px solid #3498db;
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #3498db; 
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 25px;
        }}
        li {{
            margin: 8px 0;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 6px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
"""
    
    # Add sections
    for section_title, content in sections.items():
        # Special styling for Executive Summary
        if "Executive Summary" in section_title or "executive summary" in section_title.lower():
            html_template += f'''
    <div class="executive-summary">
        <h2>{section_title}</h2>
        <div>{content}</div>
    </div>
'''
        else:
            html_template += f'''
    <div class="section">
        <h2>{section_title}</h2>
        <div>{content}</div>
    </div>
'''
    
    html_template += """
</body>
</html>"""
    
    return jsonify({"html": html_template})

@app.route("/api/generate-pricing-table", methods=["POST"])
def generate_pricing_table():
    """
    Generate pricing table for matched SKUs.
    
    Request body:
    {
        "skus": [
            {"sku_code": "SKU001", "quantity": 10},
            {"sku_code": "SKU002", "quantity": 5}
        ],
        "discount_rate": 5  // optional, percentage
    }
    """
    data = request.get_json()
    
    if not data or 'skus' not in data:
        return jsonify({"error": "Payload must include 'skus' list"}), 400
    
    if skus_df.empty or pricing_df.empty:
        return jsonify({"error": "SKU or pricing data not loaded"}), 500
    
    skus = data['skus']
    discount_rate = data.get('discount_rate', 0)
    
    pricing_items = []
    subtotal = 0
    
    for item in skus:
        sku_code = item['sku_code']
        quantity = item['quantity']
        
        # Get SKU details
        sku_row = skus_df[skus_df['sku_code'] == sku_code]
        if len(sku_row) == 0:
            continue
        
        sku_info = sku_row.iloc[0]
        
        # Get pricing
        if pricing_key:
            prows = pricing_df[pricing_df[pricing_key] == sku_code]
            if len(prows) > 0:
                price_row = prows.iloc[0]
                price_col = next((c for c in pricing_df.columns 
                                 if 'price' in c.lower() or 'amount' in c.lower()), None)
                
                if price_col:
                    unit_price = float(price_row[price_col])
                    line_total = unit_price * quantity
                    subtotal += line_total
                    
                    pricing_items.append({
                        "sku_code": sku_code,
                        "product_name": str(sku_info.get('product_name', '')),
                        "quantity": quantity,
                        "unit_price": round(unit_price, 2),
                        "line_total": round(line_total, 2)
                    })
    
    discount_amount = subtotal * (discount_rate / 100)
    after_discount = subtotal - discount_amount
    tax = after_discount * 0.18  # 18% GST
    grand_total = after_discount + tax
    
    return jsonify({
        "pricing_table": pricing_items,
        "summary": {
            "subtotal": round(subtotal, 2),
            "discount": round(discount_amount, 2),
            "tax": round(tax, 2),
            "grand_total": round(grand_total, 2)
        }
    })

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """
    Generate PDF from HTML content and save to file (OLD METHOD - kept for compatibility)
    
    Request body:
    {
        "html_content": "string (HTML content to convert)",
        "filename": "string (optional, default: 'proposal')"
    }
    
    Returns: JSON with file path and metadata
    """
    try:
        if not PDF_AVAILABLE:
            return jsonify({
                "error": "PDF generation not available. Install xhtml2pdf: pip install xhtml2pdf"
            }), 503
        
        data = request.json
        html_content = data.get('html_content')
        filename = data.get('filename', 'proposal')
        
        if not html_content:
            return jsonify({"error": "html_content is required"}), 400
        
        # Clean filename
        if not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"
        
        # Create proposals directory if it doesn't exist
        proposals_dir = os.path.join(os.path.dirname(__file__), 'proposals')
        os.makedirs(proposals_dir, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(proposals_dir, filename)
        
        # Convert HTML to PDF using xhtml2pdf
        with open(file_path, 'wb') as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
        if pisa_status.err:
            return jsonify({"error": "Failed to generate PDF"}), 500
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Return JSON response with file metadata
        return jsonify({
            "success": True,
            "message": "PDF generated successfully",
            "file_path": file_path,
            "filename": filename,
            "file_size": file_size,
            "download_url": f"http://localhost:8080/proposals/{filename}"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500


@app.route('/api/generate-proposal-pdf', methods=['POST'])
def generate_proposal_pdf():
    """
    Generate PDF proposal directly with ReportLab (no HTML conversion needed)
    
    Request body:
    {
        "title": "Proposal Title",
        "sections": {
            "Executive Summary": "• Bullet point 1\n• Bullet point 2",
            "Technical Specifications": "Content here...",
            ...
        },
        "filename": "proposal.pdf" (optional)
    }
    
    Returns: JSON with file path and metadata
    """
    try:
        if not REPORTLAB_AVAILABLE:
            return jsonify({
                "error": "ReportLab not available. Install it: pip install reportlab"
            }), 503
        
        data = request.json
        title = data.get('title', 'Business Proposal')
        sections = data.get('sections', {})
        filename = data.get('filename', f'proposal_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        
        if not sections:
            return jsonify({"error": "sections are required"}), 400
        
        # Clean filename
        if not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"
        
        # Ensure proposals directory exists
        proposals_dir = os.path.join(os.path.dirname(__file__), 'proposals')
        os.makedirs(proposals_dir, exist_ok=True)
        
        filepath = os.path.join(proposals_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Container for PDF elements
        story = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=5,
            backColor=colors.HexColor('#ecf0f1')
        )
        
        bullet_style = ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=8,
            bulletIndent=10,
            fontName='Helvetica'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        # Add Title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Add sections
        for section_title, content in sections.items():
            # Section heading
            story.append(Paragraph(section_title, heading_style))
            
            # Process content - handle bullet points
            if content.strip().startswith('•') or content.strip().startswith('-'):
                # Split into bullet points
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        # Remove bullet character if present
                        clean_line = line.lstrip('•-').strip()
                        if clean_line:
                            bullet_text = f"• {clean_line}"
                            story.append(Paragraph(bullet_text, bullet_style))
            else:
                # Regular paragraph
                # Split by double newlines for paragraphs
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(para.strip().replace('\n', '<br/>'), normal_style))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        return jsonify({
            "success": True,
            "message": "PDF generated successfully",
            "file_path": filepath,
            "filename": filename,
            "file_size": file_size,
            "download_url": f"http://localhost:8080/proposals/{filename}"
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500


@app.route('/proposals/<filename>', methods=['GET'])
def download_proposal(filename):
    """Download generated proposal PDF"""
    proposals_dir = os.path.join(os.path.dirname(__file__), 'proposals')
    return send_from_directory(proposals_dir, filename, as_attachment=True)

if __name__ == "__main__":
    print("=" * 60)
    print("Tool Execution API running on http://localhost:8080")
    print("=" * 60)
    print("\nAvailable Endpoints:")
    print("  GET  /api/health - Health check")
    print("  POST /api/match-sku - Match SKUs from requirements")
    print("  POST /api/validate-sku - Validate SKU code")
    print("  POST /api/extract-sales-objectives - Extract RFP objectives")
    print("  POST /api/calculate-total-cost - Calculate pricing totals")
    print("  POST /api/format-proposal-html - Format HTML proposal")
    print("  POST /api/generate-pricing-table - Generate pricing table")
    print("  POST /api/generate-pdf - Generate PDF from HTML (old)")
    print("  POST /api/generate-proposal-pdf - Generate PDF directly with ReportLab (NEW)")
    print("  GET  /proposals/<filename> - Download proposal PDF")
    print("=" * 60)
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
