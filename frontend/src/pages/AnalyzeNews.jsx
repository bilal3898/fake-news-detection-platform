import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './AnalyzeNews.css';

const AnalyzeNews = () => {
  const { user } = useAuth();
  const [analysisType, setAnalysisType] = useState('text');
  const [inputText, setInputText] = useState('');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [pollingInterval, setPollingInterval] = useState(null);

  const clearPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };

  const analyzeContent = async () => {
    if (!inputText && !url && !file) {
      alert('Please provide content to analyze');
      return;
    }

    setIsLoading(true);

    try {
      let response;
      if (analysisType === 'text') {
        response = await fetch('http://localhost:8000/api/v1/news/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: inputText }),
        });
      } else if (analysisType === 'url') {
        response = await fetch('http://localhost:8000/api/v1/news/predict-url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'API request failed');
      }

      const data = await response.json();

      if (analysisType === 'text') {
        const textResult = {
          prediction: (data.prediction || 'UNKNOWN').toString().toUpperCase(),
          confidence: data.confidence,
          probabilities: data.probabilities,
          features: {
            sentiment: data.features?.sentiment || 'N/A',
            subjectivity: data.features?.subjectivity || 0,
            complexity: data.features?.complexity || 0,
          },
          contentPreview: inputText.substring(0, 100) + '...',
          timestamp: new Date().toISOString(),
        };
        setResult(textResult);
        setHistory(prev => [textResult, ...prev.slice(0, 9)]);
        setIsLoading(false);
      } else if (analysisType === 'url') {
        // Initialize result
        setResult({
          prediction: 'Processing',
          contentPreview: url,
          message: data.message,
          task_id: data.task_id,
          features: {},
          timestamp: new Date().toISOString(),
        });

        clearPolling(); // Clear previous polling if any

        const interval = setInterval(async () => {
          try {
            const taskRes = await fetch(`http://localhost:8000/api/v1/news/task-status/${data.task_id}`);
            const taskData = await taskRes.json();

            if (taskData.status === 'COMPLETED' || taskData.status === 'SUCCESS') {
              const res = taskData.result;
              const urlResult = {
                prediction: (res.prediction?.prediction || 'UNKNOWN').toString().toUpperCase(),
                confidence: res.prediction?.confidence,
                probabilities: res.prediction?.probabilities,
                features: res.prediction?.features || {},
                contentPreview: res.content_preview || url,
                timestamp: new Date().toISOString(),
              };
              setResult(urlResult);
              setHistory(prev => [urlResult, ...prev.slice(0, 9)]);
              clearPolling();
              setIsLoading(false);
            } else if (taskData.status === 'FAILED' || taskData.status === 'FAILURE') {
              setResult({
                prediction: 'Failed',
                contentPreview: url,
                message: taskData.result?.error || 'URL processing failed',
                timestamp: new Date().toISOString(),
              });
              clearPolling();
              setIsLoading(false);
            }
            // else still PROCESSING, spinner keeps spinning
          } catch (err) {
            console.error('Task polling error:', err);
            clearPolling();
            setIsLoading(false);
          }
        }, 2000);

        setPollingInterval(interval);
      }

    } catch (error) {
      console.error('Analysis failed:', error);
      alert(`Error: ${error.message}`);
      setIsLoading(false);
    }
  };

  const clearAnalysis = () => {
    setResult(null);
    setInputText('');
    setUrl('');
    setFile(null);
    clearPolling();
    setIsLoading(false);
  };

  return (
    <div className="analyze-news">
      <div className="analyze-header">
        <h1>Analyze News Content</h1>
        <p>Detect fake news using our AI models</p>
      </div>

      <div className="analyze-container">
        <div className="input-section">
          <div className="analysis-type-selector">
            <button className={`type-btn ${analysisType==='text'?'active':''}`} onClick={()=>setAnalysisType('text')}>📝 Text Analysis</button>
            <button className={`type-btn ${analysisType==='url'?'active':''}`} onClick={()=>setAnalysisType('url')}>🔗 URL Analysis</button>
          </div>

          <div className="input-area">
            {analysisType==='text' && (
              <textarea
                value={inputText}
                onChange={(e)=>setInputText(e.target.value)}
                placeholder="Paste news text..."
                rows="8"
              />
            )}
            {analysisType==='url' && (
              <input
                type="url"
                value={url}
                onChange={(e)=>setUrl(e.target.value)}
                placeholder="https://example.com/news"
              />
            )}
          </div>

          <div className="action-buttons">
            <button className="analyze-btn" onClick={analyzeContent} disabled={isLoading}>
              {isLoading ? '🔍 Analyzing...' : '🚀 Analyze Content'}
            </button>
            <button className="clear-btn" onClick={clearAnalysis}>🗑️ Clear</button>
          </div>
        </div>

        <div className="results-section">
          {isLoading && <div className="loading-state"><div className="spinner"></div><p>Analyzing...</p></div>}

          {result && !isLoading && (
            <div className="result-card">
              <div className={`result-header ${result.prediction==='REAL'?'real':result.prediction==='FAKE'?'fake':'processing'}`}>
                <h3>Result: {result.prediction}</h3>
                {result.confidence && <span className="confidence">Confidence: {(result.confidence*100).toFixed(1)}%</span>}
              </div>

              {result.probabilities && (
                <div className="probability-breakdown">
                  <h4>Probability Breakdown</h4>
                  <div className="probability-bars">
                    <div className="probability-bar">
                      <span>Real</span>
                      <div className="bar-container">
                        <div className="bar real" style={{width:`${result.probabilities.real*100}%`}}></div>
                        <span>{(result.probabilities.real*100).toFixed(1)}%</span>
                      </div>
                    </div>
                    <div className="probability-bar">
                      <span>Fake</span>
                      <div className="bar-container">
                        <div className="bar fake" style={{width:`${result.probabilities.fake*100}%`}}></div>
                        <span>{(result.probabilities.fake*100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {result.message && <p>{result.message} {result.task_id && `(Task ID: ${result.task_id})`}</p>}

              <div className="feature-analysis">
                <h4>Content Analysis</h4>
                <div className="features-grid">
                  <div className="feature-item"><span>Sentiment</span><span>{result.features?.sentiment}</span></div>
                  <div className="feature-item"><span>Subjectivity</span><span>{(result.features?.subjectivity*100).toFixed(1)}%</span></div>
                  <div className="feature-item"><span>Complexity</span><span>{(result.features?.complexity*100).toFixed(1)}%</span></div>
                </div>
              </div>
            </div>
          )}

          {history.length > 0 && (
            <div className="history-section">
              <h4>Recent Analyses</h4>
              <div className="history-list">
                {history.map(item=>(
                  <div key={item.timestamp} className="history-item">
                    <div className="history-prediction">
                      <span className={`badge ${item.prediction==='REAL'?'real':item.prediction==='FAKE'?'fake':'processing'}`}>{item.prediction}</span>
                    </div>
                    <div className="history-preview">{item.contentPreview}</div>
                    <div className="history-time">{new Date(item.timestamp).toLocaleTimeString()}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyzeNews;
