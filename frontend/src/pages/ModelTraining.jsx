import React, { useState, useEffect } from 'react';
import './ModelTraining.css';

const ModelTraining = () => {
  const [trainingStatus, setTrainingStatus] = useState('idle');
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [selectedDataset, setSelectedDataset] = useState('');
  const [datasets, setDatasets] = useState([]);
  const [trainingHistory, setTrainingHistory] = useState([]);
  const [currentTraining, setCurrentTraining] = useState(null);
  const [modelConfig, setModelConfig] = useState({
    algorithm: 'random-forest',
    epochs: 10,
    batchSize: 32,
    learningRate: 0.001,
    testSize: 0.2,
    validationSplit: 0.1
  });

  const API_BASE_URL = 'http://localhost:8000/api/v1';

  // Fetch available datasets
  useEffect(() => {
    fetchDatasets();
    fetchTrainingHistory();
  }, []);

  const fetchDatasets = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/datasets/`);
      const data = await response.json();
      
      if (data.success) {
        const formattedDatasets = data.datasets.flatMap(dataset => 
          dataset.files.map(file => ({
            id: `${dataset.id}_${file.name}`,
            name: `${dataset.name} - ${file.name.replace('.tsv', '').replace('.csv', '')}`,
            datasetId: dataset.id,
            fileName: file.name,
            size: file.size,
            records: file.samples,
            type: dataset.type
          }))
        );
        setDatasets(formattedDatasets);
      }
    } catch (error) {
      console.error('Error fetching datasets:', error);
      alert('Failed to load datasets');
    }
  };

  const fetchTrainingHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/models/history`);
      const data = await response.json();
      
      if (data.success) {
        setTrainingHistory(data.models || []);
      }
    } catch (error) {
      console.error('Error fetching training history:', error);
    }
  };

  const startTraining = async () => {
    if (!selectedDataset) {
      alert('Please select a dataset first!');
      return;
    }

    const selectedDatasetInfo = datasets.find(ds => ds.id === selectedDataset);
    if (!selectedDatasetInfo) {
      alert('Invalid dataset selected');
      return;
    }

    setTrainingStatus('training');
    setTrainingProgress(0);

    try {
      const trainingPayload = {
        dataset_id: selectedDatasetInfo.datasetId,
        source_file: selectedDatasetInfo.fileName,
        algorithm: modelConfig.algorithm,
        epochs: modelConfig.epochs,
        batch_size: modelConfig.batchSize,
        learning_rate: modelConfig.learningRate,
        test_size: modelConfig.testSize,
        validation_split: modelConfig.validationSplit
      };

      const response = await fetch(`${API_BASE_URL}/models/train`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(trainingPayload)
      });

      const data = await response.json();

      if (data.success) {
        setCurrentTraining(data.training_job);
        
        // Start polling for progress
        pollTrainingProgress(data.training_job.id);
      } else {
        throw new Error(data.error || 'Training failed to start');
      }
    } catch (error) {
      console.error('Error starting training:', error);
      setTrainingStatus('error');
      alert(`Training failed: ${error.message}`);
    }
  };

  const pollTrainingProgress = async (trainingId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/models/training/${trainingId}/progress`);
        const data = await response.json();

        if (data.success) {
          setTrainingProgress(data.progress.percentage);
          
          if (data.progress.status === 'completed') {
            clearInterval(pollInterval);
            setTrainingStatus('completed');
            fetchTrainingHistory(); // Refresh history
          } else if (data.progress.status === 'failed') {
            clearInterval(pollInterval);
            setTrainingStatus('error');
            alert(`Training failed: ${data.progress.error}`);
          }
        }
      } catch (error) {
        console.error('Error polling progress:', error);
        clearInterval(pollInterval);
        setTrainingStatus('error');
      }
    }, 2000); // Poll every 2 seconds
  };

  const stopTraining = async () => {
    if (!currentTraining) return;

    try {
      const response = await fetch(`${API_BASE_URL}/models/training/${currentTraining.id}/stop`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        setTrainingStatus('stopped');
        setTrainingProgress(0);
      }
    } catch (error) {
      console.error('Error stopping training:', error);
      alert('Failed to stop training');
    }
  };

  const deployModel = async (modelId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/models/${modelId}/deploy`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        alert('Model deployed successfully!');
        fetchTrainingHistory(); // Refresh to update status
      } else {
        alert(`Deployment failed: ${data.error}`);
      }
    } catch (error) {
      console.error('Error deploying model:', error);
      alert('Deployment failed');
    }
  };

  const downloadModel = async (modelId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/models/${modelId}/download`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `model-${modelId}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Error downloading model:', error);
      alert('Download failed');
    }
  };

  const testModel = async (modelId) => {
    // Redirect to testing page or open testing modal
    window.location.href = `/model-testing?model=${modelId}`;
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'deployed': { class: 'deployed', text: 'Deployed' },
      'trained': { class: 'trained', text: 'Trained' },
      'training': { class: 'training', text: 'Training' },
      'failed': { class: 'failed', text: 'Failed' },
      'archived': { class: 'archived', text: 'Archived' }
    };
    
    const config = statusConfig[status] || { class: 'default', text: status };
    return <span className={`status-badge ${config.class}`}>{config.text}</span>;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="model-training">
      <div className="training-header">
        <h1>Model Training</h1>
        <p>Train and optimize fake news detection models</p>
      </div>

      <div className="training-container">
        {/* Configuration Panel */}
        <div className="config-panel">
          <h2>Training Configuration</h2>
          
          <div className="config-section">
            <label>Select Dataset</label>
            <select 
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              disabled={trainingStatus === 'training'}
            >
              <option value="">Choose a dataset...</option>
              {datasets.map(dataset => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.name} ({dataset.records} records)
                </option>
              ))}
            </select>
          </div>

          <div className="config-section">
            <label>Algorithm</label>
            <select 
              value={modelConfig.algorithm}
              onChange={(e) => setModelConfig({...modelConfig, algorithm: e.target.value})}
              disabled={trainingStatus === 'training'}
            >
              <option value="random-forest">Random Forest</option>
              <option value="logistic-regression">Logistic Regression</option>
              <option value="neural-network">Neural Network</option>
              <option value="svm">Support Vector Machine</option>
              <option value="bert">BERT Transformer</option>
              <option value="lstm">LSTM Network</option>
            </select>
          </div>

          <div className="config-grid">
            <div className="config-item">
              <label>Epochs</label>
              <input 
                type="number" 
                value={modelConfig.epochs}
                onChange={(e) => setModelConfig({...modelConfig, epochs: parseInt(e.target.value)})}
                min="1"
                max="100"
                disabled={trainingStatus === 'training'}
              />
            </div>
            <div className="config-item">
              <label>Batch Size</label>
              <input 
                type="number" 
                value={modelConfig.batchSize}
                onChange={(e) => setModelConfig({...modelConfig, batchSize: parseInt(e.target.value)})}
                min="1"
                max="128"
                disabled={trainingStatus === 'training'}
              />
            </div>
            <div className="config-item">
              <label>Learning Rate</label>
              <input 
                type="number" 
                step="0.001"
                value={modelConfig.learningRate}
                onChange={(e) => setModelConfig({...modelConfig, learningRate: parseFloat(e.target.value)})}
                min="0.0001"
                max="0.1"
                disabled={trainingStatus === 'training'}
              />
            </div>
            <div className="config-item">
              <label>Test Size</label>
              <input 
                type="number" 
                step="0.05"
                value={modelConfig.testSize}
                onChange={(e) => setModelConfig({...modelConfig, testSize: parseFloat(e.target.value)})}
                min="0.1"
                max="0.5"
                disabled={trainingStatus === 'training'}
              />
            </div>
          </div>

          <div className="training-actions">
            <button 
              className="train-btn"
              onClick={startTraining}
              disabled={trainingStatus === 'training' || !selectedDataset}
            >
              🚀 Start Training
            </button>
            <button 
              className="stop-btn"
              onClick={stopTraining}
              disabled={trainingStatus !== 'training'}
            >
              ⏹️ Stop Training
            </button>
          </div>
        </div>

        {/* Training Progress */}
        <div className="progress-panel">
          <h2>Training Progress</h2>
          
          <div className={`progress-container ${trainingStatus}`}>
            <div className="progress-header">
              <span className="status-indicator">
                {trainingStatus === 'idle' && '🟡 Ready to Train'}
                {trainingStatus === 'training' && '🟢 Training in Progress'}
                {trainingStatus === 'completed' && '✅ Training Completed'}
                {trainingStatus === 'stopped' && '🔴 Training Stopped'}
                {trainingStatus === 'error' && '❌ Training Failed'}
              </span>
              <span className="progress-percent">{trainingProgress}%</span>
            </div>

            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${trainingProgress}%` }}
              ></div>
            </div>

            {trainingStatus === 'training' && currentTraining && (
              <div className="training-metrics">
                <div className="metric">
                  <span>Training ID:</span>
                  <span>{currentTraining.id}</span>
                </div>
                <div className="metric">
                  <span>Algorithm:</span>
                  <span>{modelConfig.algorithm}</span>
                </div>
                <div className="metric">
                  <span>Dataset:</span>
                  <span>{selectedDataset}</span>
                </div>
              </div>
            )}

            {trainingStatus === 'completed' && currentTraining && (
              <div className="training-results">
                <h3>🎉 Training Completed Successfully!</h3>
                <div className="result-stats">
                  <div className="stat">
                    <span>Model ID</span>
                    <span className="value">{currentTraining.id}</span>
                  </div>
                  <div className="stat">
                    <span>Accuracy</span>
                    <span className="value">{currentTraining.accuracy || 'N/A'}%</span>
                  </div>
                  <div className="stat">
                    <span>Training Time</span>
                    <span className="value">{currentTraining.training_time || 'N/A'}</span>
                  </div>
                </div>
                <div className="result-actions">
                  <button 
                    className="deploy-btn"
                    onClick={() => deployModel(currentTraining.id)}
                  >
                    🚀 Deploy Model
                  </button>
                  <button 
                    className="export-btn"
                    onClick={() => downloadModel(currentTraining.id)}
                  >
                    📥 Export Model
                  </button>
                  <button 
                    className="test-btn"
                    onClick={() => testModel(currentTraining.id)}
                  >
                    🧪 Test Model
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Training History */}
      <div className="training-history">
        <h2>Training History</h2>
        <div className="history-table">
          <table>
            <thead>
              <tr>
                <th>Model Name</th>
                <th>Dataset</th>
                <th>Algorithm</th>
                <th>Accuracy</th>
                <th>Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {trainingHistory.length === 0 ? (
                <tr>
                  <td colSpan="7" className="no-data">
                    No training history available
                  </td>
                </tr>
              ) : (
                trainingHistory.map(model => (
                  <tr key={model.id}>
                    <td>{model.name || `Model-${model.id}`}</td>
                    <td>{model.dataset}</td>
                    <td>{model.algorithm}</td>
                    <td>{model.accuracy ? `${model.accuracy}%` : 'N/A'}</td>
                    <td>{formatDate(model.created_at)}</td>
                    <td>{getStatusBadge(model.status)}</td>
                    <td>
                      <button 
                        className="table-btn"
                        onClick={() => testModel(model.id)}
                      >
                        🧪 Test
                      </button>
                      <button 
                        className="table-btn"
                        onClick={() => downloadModel(model.id)}
                      >
                        📥 Export
                      </button>
                      {model.status !== 'deployed' && (
                        <button 
                          className="table-btn"
                          onClick={() => deployModel(model.id)}
                        >
                          🚀 Deploy
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ModelTraining;