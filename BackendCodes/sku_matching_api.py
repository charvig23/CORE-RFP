from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from difflib import SequenceMatcher
import re
import os

app = Flask(__name__)
CORS(app)

# Load CSVs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sku_df = pd.read_csv(os.path.join(BASE_DIR, "sku_master.csv"))
pricing_df = pd.read_csv(os.path.join(BASE_DIR, "pricing.csv"))

# Merge pricing into SKU dataframe
df = sku_df.merge(pricing_df, on="sku", how="left")
df["unit_price"] = df["unit_price"].fillna(0)

# Build search text column
df["search_text"] = (
    df["product_name"] + " " +
    df["description"] + " " +
    df["category"] + " " +
    df["tags"]
).str.lower()

print(f"✓ Loaded {len(df)} SKU records from CSV")
print(f"✓ Loaded pricing for {len(pricing_df)} SKUs")


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()


def score_match(query: str, search_text: str) -> float:
    query_tokens = set(normalize(query).split())
    text_tokens = set(normalize(search_text).split())

    if not query_tokens:
        return 0.0

    common = query_tokens & text_tokens
    token_score = len(common) / len(query_tokens)
    fuzzy_score = SequenceMatcher(None, normalize(query), normalize(search_text)).ratio()

    return (token_score * 0.7) + (fuzzy_score * 0.3)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "skus_loaded": len(df)})


@app.route("/api/match-sku", methods=["POST"])
def match_sku():
    data = request.get_json()
    query = data.get("query", "")
    top_n = data.get("top_n", 3)
    threshold = data.get("threshold", 0.1)

    if not query:
        return jsonify({"error": "query is required"}), 400

    scores = []
    for _, row in df.iterrows():
        score = score_match(query, row["search_text"])
        if score >= threshold:
            scores.append({
                "sku": row["sku"],
                "product_name": row["product_name"],
                "category": row["category"],
                "price": row["unit_price"],
                "confidence": round(score * 100, 1)
            })

    scores.sort(key=lambda x: x["confidence"], reverse=True)
    results = scores[:top_n]

    return jsonify({
        "query": query,
        "matches": results,
        "total_found": len(results)
    })


@app.route("/api/get-pricing", methods=["POST"])
def get_pricing():
    data = request.get_json()
    skus = data.get("skus", [])

    if not skus:
        return jsonify({"error": "skus list is required"}), 400

    line_items = []
    subtotal = 0

    for sku_code in skus:
        match = df[df["sku"] == sku_code]
        if not match.empty:
            row = match.iloc[0]
            quantity = 1
            unit_price = row["unit_price"]
            total = quantity * unit_price
            subtotal += total
            line_items.append({
                "sku": sku_code,
                "product_name": row["product_name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total
            })

    tax = round(subtotal * 0.18, 2)
    grand_total = round(subtotal + tax, 2)

    return jsonify({
        "line_items": line_items,
        "subtotal": subtotal,
        "tax": tax,
        "total": grand_total
    })


@app.route("/api/generate-pdf", methods=["POST"])
def generate_pdf():
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import io

    data = request.get_json()
    proposal = data.get("proposal", {})
    rfp_id = data.get("rfp_id", "unknown")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("BUSINESS PROPOSAL", styles["Title"]))
    story.append(Spacer(1, 20))

    sections = [
        ("Executive Summary", "executive_summary"),
        ("Understanding of Requirements", "understanding_of_requirements"),
        ("Proposed Solution", "proposed_solution"),
        ("Technical Approach", "technical_approach"),
        ("Pricing Summary", "pricing_summary"),
        ("Timeline", "timeline"),
        ("Terms and Conditions", "terms_and_conditions"),
        ("Conclusion", "conclusion"),
    ]

    for title, key in sections:
        content = proposal.get(key, "")
        if content:
            story.append(Paragraph(title, styles["Heading1"]))
            story.append(Paragraph(str(content), styles["Normal"]))
            story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)

    output_path = f"proposal_{rfp_id}.pdf"
    with open(output_path, "wb") as f:
        f.write(buffer.read())

    return jsonify({
        "message": "PDF generated successfully",
        "path": output_path
    })


if __name__ == "__main__":
    print("Starting Flask SKU service on port 8080...")
    app.run(host="127.0.0.1", port=8080, debug=True)