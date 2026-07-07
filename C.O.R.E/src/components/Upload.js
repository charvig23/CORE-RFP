import React, { useState } from 'react';
import { uploadRFP } from '../services/api';

function Upload({ onSuccess ,user}) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', user.id);
      const response = await uploadRFP(formData);
      onSuccess(response.data.rfp_id);
    } catch (err) {
      setError('Upload failed. Make sure FastAPI is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: '8px' }}>Upload RFP Document</h2>
      <p style={{ color: '#666', marginBottom: '32px' }}>
        Upload a PDF or text file to start the AI analysis pipeline.
      </p>

      <div style={{
        background: 'white',
        border: '2px dashed #ddd',
        borderRadius: '12px',
        padding: '48px',
        textAlign: 'center',
        marginBottom: '24px'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📄</div>
        <p style={{ color: '#666', marginBottom: '16px' }}>
          Select a PDF or TXT file
        </p>
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={handleFileChange}
          style={{ marginBottom: '16px' }}
        />
        {file && (
          <p style={{ color: '#1a1a2e', fontWeight: '500' }}>
            Selected: {file.name}
          </p>
        )}
      </div>

      {error && (
        <div style={{
          background: '#fff0f0',
          border: '1px solid #ffcccc',
          borderRadius: '8px',
          padding: '12px 16px',
          color: '#cc0000',
          marginBottom: '16px'
        }}>
          {error}
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={loading || !file}
        style={{
          background: loading ? '#888' : '#1a1a2e',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          padding: '12px 32px',
          fontSize: '16px',
          cursor: loading ? 'not-allowed' : 'pointer',
          width: '100%'
        }}
      >
        {loading ? 'Uploading...' : 'Upload & Start Analysis'}
      </button>
    </div>
  );
}

export default Upload;