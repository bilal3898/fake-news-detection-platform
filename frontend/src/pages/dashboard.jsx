import React, { useState, useEffect, useContext, useCallback } from 'react';
import { Link } from 'react-router-dom';
import AuthContext from '../contexts/AuthContext';
import NewsForm from '../components/NewsForm';
import ResultCard from '../components/ResultCard';
import ChartView from '../components/ChartView';
import storageManager from '../utils/storage';
import "./Dashboard.css";
import "../styles/Storage.css";

import { 
  BarChart3, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Zap, 
  RefreshCw, 
  Download, 
  Settings, 
  LogOut, 
  Home, 
  Search, 
  Database, 
  Brain, 
  Menu, 
  X, 
  Bell, 
  User,
  History,
  TrendingUp,
  FileText,
  Activity,
  Target,
  Cpu,
  Globe,
  ShieldCheck,
  AlertCircle,
  ChevronRight,
  Play,
  Pause,
  Filter
} from 'lucide-react';

const Dashboard = () => {
  const { user, logout } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('analyze');
  
  // User-specific storage key
  const getStorageKey = useCallback(() => {
    const userId = user?.id || user?.email || 'anonymous';
    return `newsAnalysisResults_${userId}`;
  }, [user]);

  const [results, setResults] = useState(() => {
    const storageKey = getStorageKey();
    const saved = storageManager.getItem(storageKey);
    return saved ? saved : [];
  });

  const [stats, setStats] = useState({ total: 0, fake: 0, real: 0, accuracy: 0 });
  const [loading, setLoading] = useState(false);
  const [recentNews, setRecentNews] = useState([]);
  const [error, setError] = useState(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [storageUsage, setStorageUsage] = useState({ used: 0, available: 0, percentage: 0 });

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const getAuthHeaders = useCallback((includeContentType = true) => {
    const token = localStorage.getItem('authToken') || localStorage.getItem('token') || sessionStorage.getItem('token');
    const headers = {
      'Authorization': `Bearer ${token}`
    };
    
    if (includeContentType) {
      headers['Content-Type'] = 'application/json';
    }
    
    return headers;
  }, []);

  // Save results to localStorage whenever they change - USER SPECIFIC
  useEffect(() => {
    const storageKey = getStorageKey();
    storageManager.setItem(storageKey, results.slice(0, 20)); // Reduced to 20 results
  }, [results, getStorageKey]);

  const handleError = useCallback((error, context) => {
    console.error(`Error in ${context}:`, error);
    const errorMessage = typeof error === 'string' 
      ? error 
      : error?.message || error?.detail || `Failed to ${context}`;
    
    setError(errorMessage);
    setTimeout(() => setError(null), 6000);
  }, []);

  const fetchUserStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/user/stats`, {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else if (response.status === 401) {
        logout();
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      handleError(error, 'fetch statistics');
    }
  }, [API_BASE_URL, getAuthHeaders, handleError, logout]);

  const fetchRecentNews = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/news/recent`, {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        setRecentNews(Array.isArray(data) ? data : []);
      } else if (response.status === 401) {
        logout();
      }
    } catch (error) {
      console.error('Failed to fetch recent news:', error);
    }
  }, [API_BASE_URL, getAuthHeaders, logout]);

  // Update storage usage whenever results change
  useEffect(() => {
    const usage = storageManager.getStorageUsage();
    setStorageUsage(usage);
  }, [results]);

  const initializeDashboard = useCallback(async () => {
    setIsInitialLoading(true);
    setError(null);
    
    try {
      await Promise.all([fetchUserStats(), fetchRecentNews()]);
    } catch (error) {
      handleError(error, 'initialize dashboard');
    } finally {
      setIsInitialLoading(false);
    }
  }, [fetchUserStats, fetchRecentNews, handleError]);

  useEffect(() => {
    initializeDashboard();
  }, [initializeDashboard]);

  const handleAnalysis = useCallback(async (newsData) => {
    setLoading(true);
    setError(null);

    try {
      let result;
      let textContent = '';
      let source = 'Manual Input';

      // Handle different input types
      if (newsData.type === 'file' && newsData.content instanceof File) {
        // Handle file upload (text files or images)
        try {
          // Check if it's an image file
          const fileType = newsData.content.type;
          const isImage = fileType.startsWith('image/');
          
          if (isImage) {
            // Handle image file with OCR
            console.log('🖼️ Processing image file:', newsData.content.name, 'Type:', newsData.content.type);
            
            const formData = new FormData();
            formData.append('file', newsData.content);
            
            console.log('📤 Sending FormData to:', `${API_BASE_URL}/api/v1/news/predict-image`);
            
            const response = await fetch(`${API_BASE_URL}/api/v1/news/predict-image`, {
              method: 'POST',
              headers: getAuthHeaders(false), // Don't set Content-Type for FormData
              body: formData
            });

            console.log('📥 Response status:', response.status);
            console.log('📥 Response headers:', response.headers);

            if (!response.ok) {
              const errorText = await response.text();
              console.error('❌ Error response:', errorText);
              
              if (response.status === 401) {
                logout();
                return;
              }
              
              try {
                const errorData = JSON.parse(errorText);
                throw new Error(errorData.detail || errorData.message || `Image processing failed (HTTP ${response.status})`);
              } catch {
                throw new Error(`Image processing failed (HTTP ${response.status}): ${errorText}`);
              }
            }
            
            result = await response.json();
            console.log('✅ Image processing result:', result);
            textContent = result.extracted_text || result.text_snippet || '';
            source = `Image: ${newsData.content.name}`;
            
          } else {
            // Handle text file
            const fileText = await newsData.content.text();
            if (!fileText || !fileText.trim()) {
              throw new Error('File is empty or could not be read as text');
            }
            // Remove null characters and other problematic characters
            textContent = fileText.replace(/\0/g, '').replace(/[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]/g, '').trim();
            if (!textContent || textContent.length < 10) {
              throw new Error('File does not contain enough readable text (minimum 10 characters required)');
            }
            source = `File: ${newsData.content.name}`;
            
            const response = await fetch(`${API_BASE_URL}/api/v1/news/predict`, {
              method: 'POST',
              headers: getAuthHeaders(),
              body: JSON.stringify({
                text: textContent,
                source: source,
                title: newsData.content.name || ''
              })
            });

            if (!response.ok) {
              if (response.status === 401) {
                logout();
                return;
              }
              const errorData = await response.json().catch(() => ({}));
              throw new Error(errorData.detail || errorData.message || `Prediction failed (HTTP ${response.status})`);
            }
            result = await response.json();
          }
        } catch (error) {
          if (error.message.includes('empty') || error.message.includes('readable')) {
            throw error;
          }
          throw new Error(`Failed to process file: ${error.message}. Please ensure the file is a valid text file or image.`);
        }
      } else if (newsData.type === 'url' && newsData.content) {
        // Handle URL
        const url = newsData.content.trim();
        if (!url || !url.startsWith('http')) {
          throw new Error('Please enter a valid URL starting with http:// or https://');
        }
        source = url;

        const response = await fetch(`${API_BASE_URL}/api/v1/news/predict-url`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ url: url })
        });

        if (!response.ok) {
          if (response.status === 401) {
            logout();
            return;
          }
          const errorData = await response.json().catch(() => ({}));
          const errorMessage = errorData.detail || errorData.message || `URL processing failed (HTTP ${response.status})`;
          // Provide more helpful error messages
          if (errorMessage.includes('Unable to extract') || errorMessage.includes('Could not extract')) {
            throw new Error('Unable to extract content from this URL. The page may require JavaScript, be behind a paywall, or have restricted access. Please try copying the article text directly or use a different URL.');
          }
          throw new Error(errorMessage);
        }

        const taskData = await response.json();
        
        // URL endpoint now returns result directly (synchronous)
        result = taskData;
        textContent = result.text_snippet || result.text || url;
      } else if (newsData.type === 'text' && newsData.content) {
        // Handle text input
        textContent = newsData.content.trim();
        if (!textContent || textContent.length < 10) {
          throw new Error('Please enter at least 10 characters of text to analyze.');
        }
        source = newsData.source || 'Manual Input';

        const response = await fetch(`${API_BASE_URL}/api/v1/news/predict`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            text: textContent,
            source: source,
            title: newsData.title || ''
          })
        });

        if (!response.ok) {
          if (response.status === 401) {
            logout();
            return;
          }
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || errorData.message || `Prediction failed (HTTP ${response.status})`);
        }
        result = await response.json();
      } else {
        throw new Error('Invalid input. Please provide text, URL, or file.');
      }

      if (result) {
        const enhancedResult = {
          ...result,
          id: Date.now(),
          timestamp: new Date().toISOString(),
          text: textContent || result.text_snippet || source,
          source: source
        };

        setResults(prev => [enhancedResult, ...prev].slice(0, 20)); // Reduced to 20 results
        await fetchUserStats();
        setActiveTab('history');
      }
    } catch (error) {
      handleError(error, 'analyze news');
    } finally {
      setLoading(false);
    }
  }, [API_BASE_URL, getAuthHeaders, fetchUserStats, handleError, logout]);

  const handleLogout = useCallback(() => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
  }, [logout]);

  const clearResults = useCallback(() => {
    if (window.confirm('Clear all analysis results?')) {
      setResults([]);
      // Also clear from storage
      const storageKey = getStorageKey();
      storageManager.removeItem(storageKey);
      // Update storage usage
      const usage = storageManager.getStorageUsage();
      setStorageUsage(usage);
    }
  }, [getStorageKey]);

  const cleanupStorage = useCallback(() => {
    if (window.confirm('Clean up old data to free up storage space?')) {
      storageManager.clearOldData();
      // Reload results from storage
      const storageKey = getStorageKey();
      const saved = storageManager.getItem(storageKey);
      setResults(saved ? saved : []);
      // Update storage usage
      const usage = storageManager.getStorageUsage();
      setStorageUsage(usage);
    }
  }, [getStorageKey]);

  const formatAccuracy = useCallback((accuracy) => {
    return isNaN(accuracy) ? '0.0' : (accuracy * 100).toFixed(1);
  }, []);

  // Enhanced StatCard with modern design
  const StatCard = ({ icon: Icon, title, value, subtitle, trend, color }) => (
    <div className={`stat-card stat-card-${color}`}>
      <div className="stat-background">
        <div className="stat-blob"></div>
      </div>
      <div className="stat-content">
        <div className="stat-header">
          <div className="stat-icon-wrapper">
            <Icon className="stat-icon" />
          </div>
          <div className="stat-trend">
            {trend && <span className={`trend-${trend.type}`}>{trend.value}</span>}
          </div>
        </div>
        <div className="stat-main">
          <h3 className="stat-value">{value}</h3>
          <p className="stat-title">{title}</p>
        </div>
        <p className="stat-subtitle">{subtitle}</p>
        <div className="stat-glow"></div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'analyze':
        return (
          <div className="analysis-section">
            <div className="analysis-header">
              <div className="analysis-title">
                <div className="title-icon-wrapper">
                  <Search className="title-icon" />
                </div>
                <div>
                  <h2>News Analysis</h2>
                  <p>Enter news content to verify authenticity</p>
                </div>
              </div>
              <div className="analysis-badge">
                <Cpu className="w-4 h-4" />
                <span>AI Powered</span>
              </div>
            </div>
            <NewsForm onSubmit={handleAnalysis} isLoading={loading} />
          </div>
        );
      case 'history':
        return (
          <div className="history-section">
            <div className="section-header">
              <div className="section-title">
                <div className="title-icon-wrapper">
                  <History className="title-icon" />
                </div>
                <div>
                  <h3>Analysis History</h3>
                  <p>Your recent news verifications</p>
                </div>
              </div>
              <div className="section-actions">
                <button className="filter-btn">
                  <Filter className="w-4 h-4" />
                  Filter
                </button>
                <button
                  onClick={cleanupStorage}
                  className="cleanup-btn"
                  title="Clean up old data to free up storage"
                >
                  <Database className="w-4 h-4" />
                  Cleanup Storage
                </button>
                <button
                  onClick={clearResults}
                  className="clear-btn"
                  disabled={results.length === 0}
                >
                  Clear All
                </button>
                <div className="storage-indicator">
                  <div className="storage-bar">
                    <div 
                      className={`storage-fill ${storageUsage.percentage > 80 ? 'warning' : ''}`}
                      style={{ width: `${Math.min(storageUsage.percentage, 100)}%` }}
                    />
                  </div>
                  <span className="storage-text">
                    {Math.round(storageUsage.percentage)}% used
                  </span>
                </div>
              </div>
            </div>
            
            <div className="results-grid">
              {results.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon-wrapper">
                    <FileText className="empty-icon" />
                  </div>
                  <h4>No analyses yet</h4>
                  <p>Submit news content to start verification</p>
                  <button 
                    onClick={() => setActiveTab('analyze')}
                    className="cta-button"
                  >
                    <Search className="w-4 h-4" />
                    Analyze News
                  </button>
                </div>
              ) : (
                results.map(result => (
                  <ResultCard key={result.id} result={result} />
                ))
              )}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  if (isInitialLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <div className="loading-logo">
            <div className="logo-spinner">
              <ShieldCheck className="w-8 h-8 text-white" />
            </div>
          </div>
          <div className="loading-text">
            <h3>Loading Dashboard</h3>
            <p>Preparing your news analysis environment...</p>
          </div>
          <div className="loading-progress">
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`dashboard-container ${darkMode ? 'dark-mode' : ''}`}>
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="mobile-sidebar-overlay">
          <div 
            className="overlay-backdrop" 
            onClick={() => setSidebarOpen(false)} 
          />
          <div className="mobile-sidebar">
            <SidebarContent 
              user={user} 
              onLogout={handleLogout}
              onClose={() => setSidebarOpen(false)} 
            />
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <aside className="desktop-sidebar">
        <SidebarContent user={user} onLogout={handleLogout} />
      </aside>

      {/* Main Content */}
      <div className="main-content">
        {/* Top Navigation */}
        <header className="dashboard-header">
          <div className="header-content">
            <div className="header-left">
              <button
                onClick={() => setSidebarOpen(true)}
                className="mobile-menu-btn"
                aria-label="Open menu"
              >
                <Menu className="w-5 h-5" />
              </button>
              <div className="breadcrumb">
                <span>Dashboard</span>
                <ChevronRight className="w-4 h-4" />
                <span className="breadcrumb-active">
                  {activeTab === 'analyze' ? 'News Analysis' : 
                   activeTab === 'history' ? 'Analysis History' : 'Dashboard'}
                </span>
              </div>
            </div>
            
            <div className="header-right">
              <button 
                className="theme-toggle"
                onClick={() => setDarkMode(!darkMode)}
                aria-label="Toggle theme"
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
              
              <div className="accuracy-display">
                <div className="accuracy-progress">
                  <div className="progress-circle">
                    <svg viewBox="0 0 36 36" className="circular-chart">
                      <path className="circle-bg"
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path className="circle"
                        strokeDasharray={`${stats.accuracy * 100}, 100`}
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                    </svg>
                    <Zap className="accuracy-icon" />
                  </div>
                  <div className="accuracy-text">
                    <span>{formatAccuracy(stats.accuracy)}%</span>
                    <small>Accuracy</small>
                  </div>
                </div>
              </div>

              <button className="notification-btn" aria-label="Notifications">
                <Bell className="w-5 h-5" />
                <div className="notification-indicator"></div>
              </button>

              <div className="user-menu">
                <div className="user-avatar">
                  {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Error Toast */}
        {error && (
          <div className="error-toast">
            <div className="error-content">
              <AlertCircle className="error-icon" />
              <div className="error-text">
                <span className="error-title">Analysis Error</span>
                <span className="error-message">{error}</span>
              </div>
              <button onClick={() => setError(null)} className="error-close">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Main Dashboard Content */}
        <main className="dashboard-main">
          {/* Welcome Section */}
          <div className="welcome-section">
            <div className="welcome-content">
              <h1>Welcome back, {user?.name?.split(' ')[0] || 'Analyst'}! 👋</h1>
              <p>Ready to verify today's news with AI-powered analysis</p>
            </div>
            <div className="welcome-actions">
              <button className="action-btn primary" onClick={initializeDashboard}>
                <RefreshCw className="w-4 h-4" />
                Refresh Data
              </button>
              <button className="action-btn secondary">
                <Download className="w-4 h-4" />
                Export Report
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="stats-grid">
            <StatCard
              icon={Activity}
              title="Total Analyses"
              value={stats?.total ? stats.total.toLocaleString() : "0"}
              subtitle="Lifetime verifications"
              trend={{ type: 'up', value: '+12%' }}
              color="blue"
            />
            <StatCard
              icon={AlertTriangle}
              title="Fake News"
              value={stats?.fake ? stats.fake.toLocaleString() : "0"}
              subtitle={stats.total ? `${((stats.fake/stats.total)*100).toFixed(1)}% detected` : 'No data'}
              trend={{ type: 'down', value: '-5%' }}
              color="red"
            />
            <StatCard
              icon={CheckCircle}
              title="Verified Real"
              value={stats?.real ? stats.real.toLocaleString() : "0"}
              subtitle={stats.total ? `${((stats.real/stats.total)*100).toFixed(1)}% verified` : 'No data'}
              trend={{ type: 'up', value: '+8%' }}
              color="green"
            />
            <StatCard
              icon={Target}
              title="Model Accuracy"
              value={stats?.accuracy ? `${formatAccuracy(stats.accuracy)}%` : "—"}
              subtitle="Current performance"
              trend={{ type: 'up', value: '+2%' }}
              color="purple"
            />
          </div>

          {/* Main Content Area */}
          <div className="main-grid">
            {/* Left Panel - Analysis & History */}
            <div className="left-panel">
              {/* Tab Navigation */}
              <div className="tab-navigation">
                <button
                  className={`tab-button ${activeTab === 'analyze' ? 'active' : ''}`}
                  onClick={() => setActiveTab('analyze')}
                >
                  <Search className="tab-icon" />
                  <span>Analyze News</span>
                  <div className="tab-indicator"></div>
                </button>
                <button
                  className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
                  onClick={() => setActiveTab('history')}
                >
                  <History className="tab-icon" />
                  <span>History</span>
                  <span className="tab-badge">{results.length}</span>
                  <div className="tab-indicator"></div>
                </button>
              </div>

              {/* Tab Content */}
              <div className="tab-content">
                {renderTabContent()}
              </div>
            </div>

            {/* Right Panel - Analytics & Tools */}
            <div className="right-panel">
              {/* Analytics Chart */}
              <div className="analytics-card">
                <div className="card-header">
                  <div className="card-title">
                    <TrendingUp className="card-icon" />
                    <h3>Analytics Overview</h3>
                  </div>
                  <button className="card-action">
                    <Play className="w-4 h-4" />
                  </button>
                </div>
                <ChartView stats={stats} recentNews={recentNews} loading={loading} />
              </div>

              {/* Quick Actions */}
              <div className="tools-card">
                <div className="card-header">
                  <h3>Quick Tools</h3>
                </div>
                <div className="tools-grid">
                  <button className="tool-item">
                    <Globe className="tool-icon" />
                    <span>Web Monitor</span>
                  </button>
                  <button className="tool-item">
                    <Database className="tool-icon" />
                    <span>Data Sources</span>
                  </button>
                  <button className="tool-item">
                    <Brain className="tool-icon" />
                    <span>AI Models</span>
                  </button>
                  <button className="tool-item">
                    <Shield className="tool-icon" />
                    <span>Security</span>
                  </button>
                </div>
              </div>

              {/* Recent News Feed */}
              <div className="news-card">
                <div className="card-header">
                  <h3>Trending News</h3>
                  <span className="news-badge">Live</span>
                </div>
                <div className="news-feed">
                  {recentNews.length === 0 ? (
                    <div className="no-news">
                      <Globe className="no-news-icon" />
                      <p>No recent news available</p>
                    </div>
                  ) : (
                    recentNews.slice(0, 4).map((news, index) => (
                      <div key={index} className="news-item">
                        <div className="news-content">
                          <a 
                            href={news.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="news-title"
                          >
                            {news.title || news.description || 'Untitled News'}
                          </a>
                          <div className="news-meta">
                            <span className="news-source">{news.source}</span>
                            <span className="news-time">
                              {new Date(news.published_at || Date.now()).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <button className="news-action">
                          <Search className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="dashboard-footer">
          <div className="footer-content">
            <div className="footer-left">
              <div className="footer-logo">
                <ShieldCheck className="footer-logo-icon" />
                <span>FakeNewsDetector AI</span>
              </div>
              <p>Protecting information integrity with artificial intelligence</p>
            </div>
            <div className="footer-right">
              <div className="footer-stats">
                <div className="footer-stat">
                  <span className="stat-number">{stats.total || 0}</span>
                  <span className="stat-label">Analyses</span>
                </div>
                <div className="footer-stat">
                  <span className="stat-number">{stats.real || 0}</span>
                  <span className="stat-label">Verified</span>
                </div>
                <div className="footer-stat">
                  <span className="stat-number">{formatAccuracy(stats.accuracy)}%</span>
                  <span className="stat-label">Accuracy</span>
                </div>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <span>© {new Date().getFullYear()} FakeNewsDetector AI • v1.0.0</span>
            <span>Made with ❤️ for a safer digital world</span>
          </div>
        </footer>
      </div>
    </div>
  );
};

// Enhanced Sidebar Component
const SidebarContent = ({ user, onLogout, onClose }) => (
  <div className="sidebar-content">
    {/* Logo & Close */}
    <div className="sidebar-header">
      <div className="logo-section">
        <div className="logo-graphic">
          <div className="logo-circle">
            <ShieldCheck className="logo-icon" />
          </div>
          <div className="logo-text">
            <h2>NewsGuard</h2>
            <p>AI Detector</p>
          </div>
        </div>
      </div>
      {onClose && (
        <button onClick={onClose} className="close-sidebar" aria-label="Close menu">
          <X className="w-5 h-5" />
        </button>
      )}
    </div>

    {/* Navigation */}
    <nav className="sidebar-nav">
      <NavItem icon={Home} label="Dashboard" to="/dashboard" active={true} />
      <NavItem icon={Search} label="Analyze News" to="/dashboard/analyze" />
      <NavItem icon={History} label="History" to="/dashboard/history" />
      <NavItem icon={BarChart3} label="Analytics" to="/dashboard/analytics" />
      <NavItem icon={Database} label="Datasets" to="/dashboard/datasets" />
      <NavItem icon={Brain} label="AI Models" to="/dashboard/models" />
      <NavItem icon={Settings} label="Settings" to="/dashboard/settings" />
    </nav>

    {/* User Section */}
    <div className="user-section">
      <div className="user-profile">
        <div className="user-avatar-large">
          {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
        </div>
        <div className="user-info">
          <p className="user-name">{user?.username || user?.name || user?.email?.split('@')[0] || 'User'}</p>
          <p className="user-email">{user?.email || ''}</p>
          <div className="user-status">
            <div className="status-dot"></div>
            <span>Online</span>
          </div>
        </div>
      </div>
      <button
        onClick={onLogout}
        className="logout-btn"
        aria-label="Logout"
      >
        <LogOut className="logout-icon" />
        <span>Sign Out</span>
      </button>
    </div>
  </div>
);

// Enhanced Navigation Item Component
const NavItem = ({ icon: Icon, label, to, active = false }) => (
  <Link
    to={to}
    className={`nav-item ${active ? 'nav-item-active' : ''}`}
  >
    <div className="nav-icon-wrapper">
      <Icon className="nav-icon" />
    </div>
    <span className="nav-label">{label}</span>
    <div className="nav-arrow">
      <ChevronRight className="w-4 h-4" />
    </div>
  </Link>
);

export default Dashboard;