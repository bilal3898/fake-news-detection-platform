import React from 'react';

const ResultCard = ({ result, onAnalyzeAnother, isLoading = false }) => {
  if (!result) return null;

  const { prediction, confidence, probabilities, model_version, processing_time, text_preview, error_type, message, suggestion, content_status } = result;

  const isFake = prediction?.toLowerCase() === 'fake';
  const isUnableToAnalyze = prediction?.toLowerCase() === 'unable_to_analyze';
  const confidencePercentage = (confidence * 100).toFixed(1);

  // Confidence color gradient
  const getConfidenceColor = (conf) => {
    if (conf >= 0.8) return 'bg-red-500';
    if (conf >= 0.6) return 'bg-orange-500';
    if (conf >= 0.4) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // Get prediction display info
  const getPredictionInfo = () => {
    if (isUnableToAnalyze) {
      return {
        text: '⚠️ UNABLE TO ANALYZE',
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-800',
        icon: '⚠️'
      };
    } else if (isFake) {
      return {
        text: '🚫 FAKE NEWS',
        bgColor: 'bg-red-100',
        textColor: 'text-red-800',
        icon: '🚫'
      };
    } else {
      return {
        text: '✅ REAL NEWS',
        bgColor: 'bg-green-100',
        textColor: 'text-green-800',
        icon: '✅'
      };
    }
  };

  const predictionInfo = getPredictionInfo();

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      {/* Result Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Analysis Result</h2>
        <span className="text-sm text-gray-500">
          {new Date(processing_time).toLocaleString()}
        </span>
      </div>

      {/* Main Prediction */}
      <div className="text-center mb-6">
        <div className={`inline-flex items-center justify-center px-6 py-3 rounded-full ${predictionInfo.bgColor}`}>
          <span className={`text-2xl font-bold ${predictionInfo.textColor}`}>
            {predictionInfo.text}
          </span>
        </div>
      </div>

      {/* Confidence Meter */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Confidence Level</span>
          <span className="text-sm font-bold text-gray-800">{confidencePercentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full ${getConfidenceColor(confidence)} transition-all duration-500`}
            style={{ width: `${confidencePercentage}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Low</span>
          <span>High</span>
        </div>
      </div>

      {/* Probability Breakdown - Only show for actual predictions */}
      {!isUnableToAnalyze && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-green-800">Real News Probability</span>
              <span className="text-2xl font-bold text-green-600">
                {((probabilities?.real || 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-red-800">Fake News Probability</span>
              <span className="text-2xl font-bold text-red-600">
                {((probabilities?.fake || 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Model Information */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6">
        <h4 className="font-semibold text-gray-700 mb-2">Model Information</h4>
        <div className="text-sm text-gray-600">
          <p>Model Version: {model_version || 'v1.0'}</p>
          <p>Analysis Time: {processing_time ? new Date(processing_time).toLocaleTimeString() : 'N/A'}</p>
        </div>
      </div>

      {/* Text Preview */}
      {text_preview && (
        <div className="mb-6">
          <h4 className="font-semibold text-gray-700 mb-2">Analyzed Content Preview</h4>
          <div className="bg-gray-100 p-4 rounded-lg">
            <p className="text-sm text-gray-600 leading-relaxed">
              {text_preview.length > 200 ? text_preview.substring(0, 200) + '...' : text_preview}
            </p>
          </div>
        </div>
      )}

      {/* Error Message for UNABLE_TO_ANALYZE */}
      {isUnableToAnalyze && (
        <div className="mb-6">
          <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
            <h4 className="font-semibold text-red-800 mb-2">⚠️ Analysis Issue Detected</h4>
            <p className="text-sm text-red-700 mb-2">
              {message || 'Unable to analyze this content due to technical issues.'}
            </p>
            {suggestion && (
              <p className="text-sm text-red-600">
                <strong>Suggestion:</strong> {suggestion}
              </p>
            )}
            {content_status && (
              <details className="mt-2">
                <summary className="text-xs text-red-500 cursor-pointer">Technical Details</summary>
                <div className="mt-2 text-xs text-red-400">
                  <p><strong>Issue Type:</strong> {content_status.issue_type}</p>
                  <p><strong>Confidence:</strong> {(content_status.confidence * 100).toFixed(0)}%</p>
                  <p><strong>Issues Found:</strong> {content_status.details?.issues_found?.join(', ')}</p>
                </div>
              </details>
            )}
          </div>
        </div>
      )}

      {/* Explanation */}
      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <h4 className="font-semibold text-blue-800 mb-2">📊 What This Means</h4>
        <p className="text-sm text-blue-600">
          {isUnableToAnalyze 
            ? 'The content could not be analyzed due to technical limitations. This may be caused by JavaScript requirements, access restrictions, or content loading issues.'
            : isFake 
              ? 'This content shows characteristics commonly associated with fake news, such as sensational language, lack of credible sources, or inconsistent facts.'
              : 'This content appears to be legitimate news with proper sourcing, factual information, and professional writing standards.'
          }
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button
          onClick={onAnalyzeAnother}
          disabled={isLoading}
          className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg font-semibold hover:bg-gray-700 disabled:opacity-50 transition-colors"
        >
          Analyze Another
        </button>
        
        <button
          onClick={() => window.print()}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Print Result
        </button>
        
        <button
          onClick={() => {
            const resultStr = JSON.stringify(result, null, 2);
            navigator.clipboard.writeText(resultStr);
          }}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Copy JSON
        </button>
      </div>

      {/* Disclaimer */}
      <div className="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-xs text-yellow-800 text-center">
          ⚠️ Disclaimer: This analysis is generated by AI and should be used as a reference only. 
          Always verify information from multiple credible sources.
        </p>
      </div>
    </div>
  );
};

export default ResultCard;