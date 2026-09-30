// frontend/src/components/ErrorBoundary.js
import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <div className="error-boundary-icon">
              <AlertCircle className="w-12 h-12 text-red-500" />
            </div>
            <h2>Something went wrong</h2>
            <p>We encountered an error while rendering this component.</p>
            <div className="error-boundary-actions">
              <button
                onClick={() => window.location.reload()}
                className="error-retry-btn"
              >
                <RefreshCw className="w-4 h-4" />
                Reload Page
              </button>
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="error-retry-btn secondary"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;