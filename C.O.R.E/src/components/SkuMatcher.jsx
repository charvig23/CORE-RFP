import React, { useState } from 'react';
import './SkuMatcher.css';

const SkuMatcher = () => {
  const [requirements, setRequirements] = useState(['']);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [topK, setTopK] = useState(3);
  const [includePricing, setIncludePricing] = useState(true);

  const addRequirement = () => {
    setRequirements([...requirements, '']);
  };

  const removeRequirement = (index) => {
    const newReqs = requirements.filter((_, i) => i !== index);
    setRequirements(newReqs.length > 0 ? newReqs : ['']);
  };

  const updateRequirement = (index, value) => {
    const newReqs = [...requirements];
    newReqs[index] = value;
    setRequirements(newReqs);
  };

  const matchSkus = async () => {
    setLoading(true);
    setError('');
    setResults(null);

    const validRequirements = requirements.filter(req => req.trim() !== '');
    
    if (validRequirements.length === 0) {
      setError('Please enter at least one requirement');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:8080/api/match-sku', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          requirements: validRequirements,
          top_k: topK,
          include_pricing: includePricing,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(`Failed to match SKUs: ${err.message}`);
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sku-matcher">
      <h2>SKU Matcher</h2>
      
      <div className="matcher-controls">
        <div className="requirements-section">
          <h3>Product Requirements</h3>
          {requirements.map((req, index) => (
            <div key={index} className="requirement-input-group">
              <input
                type="text"
                className="requirement-input"
                placeholder="e.g., Exterior emulsion for outer walls"
                value={req}
                onChange={(e) => updateRequirement(index, e.target.value)}
              />
              {requirements.length > 1 && (
                <button
                  className="remove-btn"
                  onClick={() => removeRequirement(index)}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          <button className="add-requirement-btn" onClick={addRequirement}>
            + Add Requirement
          </button>
        </div>

        <div className="options-section">
          <div className="option-group">
            <label>
              Number of Matches:
              <input
                type="number"
                min="1"
                max="10"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
              />
            </label>
          </div>
          <div className="option-group">
            <label>
              <input
                type="checkbox"
                checked={includePricing}
                onChange={(e) => setIncludePricing(e.target.checked)}
              />
              Include Pricing
            </label>
          </div>
        </div>

        <button
          className="match-btn"
          onClick={matchSkus}
          disabled={loading}
        >
          {loading ? 'Matching...' : 'Match SKUs'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {results && (
        <div className="results-section">
          <h3>Matching Results</h3>
          {results.matches.map((result, idx) => (
            <div key={idx} className="requirement-results">
              <h4 className="requirement-title">
                Requirement: {result.requirement}
              </h4>
              <div className="matches-grid">
                {result.matches.map((match, matchIdx) => (
                  <div key={matchIdx} className="match-card">
                    <div className="match-header">
                      <span className="match-rank">#{matchIdx + 1}</span>
                      <span className="match-score">
                        Score: {(match.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="match-details">
                      <div className="sku-code">{match.sku}</div>
                      <div className="product-name">{match.product_name}</div>
                      <div className="description">{match.description}</div>
                      {match.price && (
                        <div className="pricing-info">
                          <span className="price">₹{match.price.toFixed(2)}</span>
                          {match.gst && (
                            <span className="gst">GST: {match.gst}%</span>
                          )}
                        </div>
                      )}
                      <div className="match-metrics">
                        <span>Similarity: {(match.similarity * 100).toFixed(1)}%</span>
                        <span>Raw Score: {match.raw_score}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SkuMatcher;
