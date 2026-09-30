import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Datasets.css';
import { datasetAPI, apiUtils } from '../services/api';

const Datasets = () => {
  const [activeTab, setActiveTab] = useState('my-datasets');
  const [myDatasets, setMyDatasets] = useState([]);
  const [publicDatasets, setPublicDatasets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [previewData, setPreviewData] = useState(null);
  const { user, logout } = useAuth();

  // Fetch datasets
  useEffect(() => {
    fetchMyDatasets();
    fetchPublicDatasets();
  }, []);

  const fetchMyDatasets = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await datasetAPI.getMy();
      if (data && data.datasets) {
        setMyDatasets(data.datasets);
      } else {
        setMyDatasets([]);
      }
    } catch (error) {
      console.error('Error fetching datasets:', error);
      if (error.status === 401) {
        // Token expired, logout user
        logout();
        setError('Session expired. Please login again.');
      } else {
        setError(apiUtils.getErrorMessage(error) || 'Failed to load datasets');
      }
      setMyDatasets([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchPublicDatasets = async () => {
    try {
      const data = await datasetAPI.getPublic();
      if (data && data.datasets) {
        setPublicDatasets(data.datasets);
      } else {
        setPublicDatasets([]);
      }
    } catch (error) {
      console.error('Error fetching public datasets:', error);
      setPublicDatasets([]);
    }
  };

  const handleFileUpload = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    const fileInput = event.target.file;
    const nameInput = event.target.name;
    const descriptionInput = event.target.description;
    const datasetTypeInput = event.target.dataset_type;
    const isPublicInput = event.target.is_public;

    if (!fileInput.files[0]) {
      setError('Please select a file to upload');
      return;
    }

    formData.append('file', fileInput.files[0]);
    formData.append('name', nameInput.value);
    formData.append('description', descriptionInput.value);
    formData.append('dataset_type', datasetTypeInput.value);
    formData.append('is_public', isPublicInput.checked);

    try {
      setUploading(true);
      setError('');
      setSuccess('');

      const data = await datasetAPI.upload(formData);

      if (data.success) {
        setSuccess('Dataset uploaded successfully!');
        event.target.reset();
        fetchMyDatasets();
        setActiveTab('my-datasets');
      } else {
        setError(data.detail || data.message || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      if (error.status === 401) {
        logout();
        setError('Session expired. Please login again.');
      } else {
        setError(apiUtils.getErrorMessage(error) || 'Upload failed. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (datasetId, isPublic = false) => {
    try {
      const blob = await datasetAPI.download(datasetId);
      apiUtils.downloadFile(blob, `dataset_${datasetId}.csv`);
      
      // Refresh public datasets to update download count
      if (isPublic) {
        fetchPublicDatasets();
      }
    } catch (error) {
      console.error('Download error:', error);
      if (error.status === 401) {
        logout();
        setError('Session expired. Please login again.');
      } else {
        setError('Download failed');
      }
    }
  };

  const handlePreview = async (datasetId) => {
    try {
      const data = await datasetAPI.preview(datasetId, 5);
      if (data.success) {
        setPreviewData(data);
      } else {
        setError('Preview failed');
      }
    } catch (error) {
      console.error('Preview error:', error);
      if (error.status === 401) {
        logout();
        setError('Session expired. Please login again.');
      } else {
        setError('Preview failed');
      }
    }
  };

  const handleDelete = async (datasetId) => {
    if (!window.confirm('Are you sure you want to delete this dataset?')) {
      return;
    }

    try {
      const data = await datasetAPI.delete(datasetId);
      if (data.success) {
        setSuccess('Dataset deleted successfully');
        fetchMyDatasets();
      } else {
        setError('Delete failed');
      }
    } catch (error) {
      console.error('Delete error:', error);
      if (error.status === 401) {
        logout();
        setError('Session expired. Please login again.');
      } else {
        setError('Delete failed');
      }
    }
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return 'Unknown date';
    }
  };

  const clearNotifications = () => {
    setError('');
    setSuccess('');
  };

  // Auto-clear notifications after 5 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(clearNotifications, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  return (
    <div className="datasets-page">
      <div className="datasets-header">
        <h1>News Datasets</h1>
        <p>Manage and explore datasets for fake news detection</p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="notification error">
          <span>⚠</span>
          {error}
          <button className="close-notification" onClick={clearNotifications}>×</button>
        </div>
      )}
      {success && (
        <div className="notification success">
          <span>✅</span>
          {success}
          <button className="close-notification" onClick={clearNotifications}>×</button>
        </div>
      )}

      <div className="datasets-container">
        {/* Tabs */}
        <div className="datasets-tabs">
          <button 
            className={`tab-btn ${activeTab === 'my-datasets' ? 'active' : ''}`}
            onClick={() => setActiveTab('my-datasets')}
          >
            📁 My Datasets
          </button>
          <button 
            className={`tab-btn ${activeTab === 'public' ? 'active' : ''}`}
            onClick={() => setActiveTab('public')}
          >
            🌐 Public Datasets
          </button>
          <button 
            className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            ⬆️ Upload Dataset
          </button>
        </div>

        {/* Content Area */}
        <div className="datasets-content">
          {activeTab === 'my-datasets' && (
            <div className="my-datasets">
              <div className="section-header">
                <h2>My Datasets</h2>
                <button 
                  className="upload-btn" 
                  onClick={() => setActiveTab('upload')}
                >
                  + Upload New Dataset
                </button>
              </div>

              {loading ? (
                <div className="loading-state">
                  <div className="spinner"></div>
                  <p>Loading datasets...</p>
                </div>
              ) : myDatasets.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">📁</div>
                  <h3>No datasets yet</h3>
                  <p>Upload your first dataset to get started</p>
                  <button 
                    className="upload-btn" 
                    onClick={() => setActiveTab('upload')}
                  >
                    Upload Dataset
                  </button>
                </div>
              ) : (
                <div className="datasets-grid">
                  {myDatasets.map(dataset => (
                    <div key={dataset.id} className="dataset-card">
                      <div className="dataset-header">
                        <h3>{dataset.name}</h3>
                        <span className={`status ${dataset.status || 'active'}`}>
                          {dataset.status || 'active'}
                        </span>
                      </div>
                      <p className="dataset-description">{dataset.description || 'No description available'}</p>
                      <div className="dataset-meta">
                        <div className="meta-item">
                          <span>Type:</span>
                          <span>{dataset.dataset_type || 'text'}</span>
                        </div>
                        <div className="meta-item">
                          <span>Size:</span>
                          <span>{dataset.size || 'Unknown'}</span>
                        </div>
                        <div className="meta-item">
                          <span>Records:</span>
                          <span>{(dataset.records || 0).toLocaleString()}</span>
                        </div>
                        <div className="meta-item">
                          <span>Created:</span>
                          <span>{formatDate(dataset.created)}</span>
                        </div>
                      </div>
                      <div className="dataset-actions">
                        <button 
                          className="action-btn primary"
                          onClick={() => handlePreview(dataset.id)}
                        >
                          👁️ Preview
                        </button>
                        <button 
                          className="action-btn"
                          onClick={() => handleDownload(dataset.id)}
                        >
                          📥 Download
                        </button>
                        <button 
                          className="action-btn danger"
                          onClick={() => handleDelete(dataset.id)}
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'public' && (
            <div className="public-datasets">
              <h2>Public Datasets</h2>
              
              {publicDatasets.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">🌐</div>
                  <h3>No public datasets available</h3>
                  <p>Check back later for public datasets</p>
                </div>
              ) : (
                <div className="datasets-list">
                  {publicDatasets.map(dataset => (
                    <div key={dataset.id} className="public-dataset-card">
                      <div className="public-dataset-info">
                        <h3>{dataset.name}</h3>
                        <p className="dataset-description">{dataset.description}</p>
                        <div className="dataset-stats">
                          <span>⭐ {dataset.rating || 'N/A'}</span>
                          <span>📥 {(dataset.downloads || 0).toLocaleString()} downloads</span>
                          <span>📚 {dataset.source || 'Unknown'}</span>
                        </div>
                        <div className="dataset-details">
                          <span>Type: {dataset.dataset_type || 'text'}</span>
                          <span>Size: {dataset.size || 'Unknown'}</span>
                          <span>Records: {(dataset.records || 0).toLocaleString()}</span>
                        </div>
                      </div>
                      <div className="public-dataset-actions">
                        <button 
                          className="download-btn"
                          onClick={() => handleDownload(dataset.id, true)}
                        >
                          📥 Download
                        </button>
                        <button 
                          className="preview-btn"
                          onClick={() => handlePreview(dataset.id)}
                        >
                          👁️ Preview
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'upload' && (
            <div className="upload-dataset">
              <h2>Upload New Dataset</h2>
              <form onSubmit={handleFileUpload}>
                <div className="upload-area">
                  <div className="upload-box">
                    <div className="upload-icon">📁</div>
                    <h3>Drop your dataset file here</h3>
                    <p>Supported formats: CSV, JSON, TXT, TSV (Max 100MB)</p>
                    <input 
                      type="file" 
                      name="file"
                      className="file-input" 
                      accept=".csv,.json,.txt,.tsv"
                      required
                    />
                  </div>
                </div>

                <div className="upload-form">
                  <div className="form-group">
                    <label>Dataset Name *</label>
                    <input 
                      type="text" 
                      name="name"
                      placeholder="Enter dataset name" 
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea 
                      name="description"
                      placeholder="Describe your dataset..."
                      rows="3"
                    ></textarea>
                  </div>
                  <div className="form-group">
                    <label>Dataset Type</label>
                    <select name="dataset_type" defaultValue="text">
                      <option value="text">Text Data</option>
                      <option value="url">URL Links</option>
                      <option value="mixed">Mixed Content</option>
                    </select>
                  </div>
                  <div className="form-group checkbox-group">
                    <label>
                      <input type="checkbox" name="is_public" />
                      Make this dataset public
                    </label>
                    <small>Public datasets can be downloaded by other users</small>
                  </div>
                  <button 
                    type="submit" 
                    className={`upload-submit-btn ${uploading ? 'loading' : ''}`}
                    disabled={uploading}
                  >
                    {uploading ? (
                      <>
                        <span className="spinner"></span>
                        Uploading...
                      </>
                    ) : (
                      '🚀 Upload Dataset'
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>

      {/* Preview Modal */}
      {previewData && (
        <div className="modal-overlay">
          <div className="preview-modal">
            <div className="modal-header">
              <h3>Dataset Preview: {previewData.dataset?.name || 'Unknown Dataset'}</h3>
              <button 
                className="close-btn"
                onClick={() => setPreviewData(null)}
              >
                ×
              </button>
            </div>
            <div className="preview-content">
              <div className="preview-info">
                <p><strong>Records:</strong> {(previewData.total_records || 0).toLocaleString()}</p>
                <p><strong>Showing:</strong> First 5 records</p>
              </div>
              {previewData.preview && previewData.preview.length > 0 ? (
                <div className="preview-table">
                  <table>
                    <thead>
                      <tr>
                        {Object.keys(previewData.preview[0]).map(key => (
                          <th key={key}>{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.preview.map((row, index) => (
                        <tr key={index}>
                          {Object.values(row).map((value, cellIndex) => (
                            <td key={cellIndex}>{String(value)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="no-preview-data">
                  <p>No preview data available</p>
                </div>
              )}
            </div>
            <div className="modal-actions">
              <button 
                className="download-btn"
                onClick={() => handleDownload(previewData.dataset?.id)}
              >
                📥 Download Full Dataset
              </button>
              <button 
                className="close-btn"
                onClick={() => setPreviewData(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Datasets;