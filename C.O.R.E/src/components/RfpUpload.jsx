import React, { useState, useRef } from 'react';
import { API_BASE } from '../services/api';
import './RfpUpload.css';

const RfpUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      // Auto-fill title from filename
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
      }
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a title');
      return;
    }

    setUploading(true);
    setError('');
    setMessage('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/rfp/upload-file`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }

      const data = await response.json();
      
      setMessage(`✅ Successfully uploaded: ${data.filename}`);
      setFile(null);
      setTitle('');
      
      // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }

      // Notify parent component
      if (onUploadSuccess) {
        onUploadSuccess(data);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setMessage(''), 3000);

    } catch (err) {
      setError(`Upload failed: ${err.message}`);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (droppedFile.type === 'application/pdf' || droppedFile.name.endsWith('.pdf') || droppedFile.name.endsWith('.txt')) {
        setFile(droppedFile);
        if (!title) {
          setTitle(droppedFile.name.replace(/\.[^/.]+$/, ''));
        }
        setError('');
      } else {
        setError('Please upload PDF or TXT files only');
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="rfp-upload">
      <h3>📤 Upload RFP Document</h3>
      
      <div 
        className={`upload-zone ${file ? 'has-file' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        {!file ? (
          <>
            <div className="upload-icon">📄</div>
            <p className="upload-text">
              Drag & drop your RFP file here<br />
              or click to browse
            </p>
            <input
              id="file-input"
              type="file"
              accept=".pdf,.txt"
              onChange={handleFileChange}
              className="file-input"
              ref={fileInputRef}
            />
            <label htmlFor="file-input" className="browse-btn">
              Browse Files
            </label>
            <p className="file-types">Supported: PDF, TXT</p>
          </>
        ) : (
          <div className="file-selected">
            <div className="file-icon">
              {file.name.endsWith('.pdf') ? '📕' : '📄'}
            </div>
            <div className="file-info">
              <p className="file-name">{file.name}</p>
              <p className="file-size">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
            <button 
              className="remove-file-btn"
              onClick={() => {
                setFile(null);
                if (fileInputRef.current) {
                  fileInputRef.current.value = '';
                }
              }}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {file && (
        <div className="upload-form">
          <div className="form-group">
            <label>RFP Title:</label>
            <input
              type="text"
              className="title-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter RFP title"
            />
          </div>

          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? '⏳ Uploading...' : '📤 Upload RFP'}
          </button>
        </div>
      )}

      {message && (
        <div className="success-message">
          {message}
        </div>
      )}

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
};

export default RfpUpload;
