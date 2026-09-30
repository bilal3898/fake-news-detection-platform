/**
 * Utility functions for the Fake News Detection application
 */

/**
 * Formats a date to a readable string
 * @param {string|Date} date - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export const formatDate = (date, options = {}) => {
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  };
  
  const mergedOptions = { ...defaultOptions, ...options };
  
  return new Intl.DateTimeFormat('en-US', mergedOptions).format(new Date(date));
};

/**
 * Truncates text to a specified length with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length before truncation
 * @returns {string} Truncated text
 */
export const truncateText = (text, maxLength = 100) => {
  if (!text || typeof text !== 'string') return '';
  if (text.length <= maxLength) return text;
  
  return text.substring(0, maxLength).trim() + '...';
};

/**
 * Formats a number with commas for thousands
 * @param {number} number - Number to format
 * @returns {string} Formatted number string
 */
export const formatNumber = (number) => {
  return new Intl.NumberFormat('en-US').format(number);
};

/**
 * Converts a confidence score to a percentage string
 * @param {number} confidence - Confidence score (0-1)
 * @returns {string} Percentage string
 */
export const confidenceToPercentage = (confidence) => {
  return `${Math.round(confidence * 100)}%`;
};

/**
 * Gets color based on prediction type
 * @param {string} prediction - Prediction type ('REAL' or 'FAKE')
 * @returns {Object} Color configuration
 */
export const getPredictionColor = (prediction) => {
  const colors = {
    REAL: {
      bg: 'bg-green-100',
      text: 'text-green-800',
      border: 'border-green-200',
      ring: 'ring-green-500'
    },
    FAKE: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      border: 'border-red-200',
      ring: 'ring-red-500'
    },
    default: {
      bg: 'bg-gray-100',
      text: 'text-gray-800',
      border: 'border-gray-200',
      ring: 'ring-gray-500'
    }
  };
  
  return colors[prediction] || colors.default;
};

/**
 * Validates a URL string
 * @param {string} url - URL to validate
 * @returns {boolean} True if valid URL
 */
export const isValidUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Debounces a function call
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
};

/**
 * Capitalizes the first letter of a string
 * @param {string} string - String to capitalize
 * @returns {string} Capitalized string
 */
export const capitalize = (string) => {
  if (!string) return '';
  return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
};

/**
 * Generates a random ID
 * @param {number} length - Length of the ID
 * @returns {string} Random ID
 */
export const generateId = (length = 8) => {
  return Math.random().toString(36).substring(2, 2 + length);
};

/**
 * Copies text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      return successful;
    } catch (fallbackError) {
      document.body.removeChild(textArea);
      return false;
    }
  }
};

/**
 * Formats file size to human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Validates email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid email
 */
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Sanitizes HTML content to prevent XSS
 * @param {string} html - HTML content to sanitize
 * @returns {string} Sanitized HTML
 */
export const sanitizeHtml = (html) => {
  const temp = document.createElement('div');
  temp.textContent = html;
  return temp.innerHTML;
};

/**
 * Calculates reading time for text
 * @param {string} text - Text to calculate reading time for
 * @param {number} wordsPerMinute - Reading speed (default: 200)
 * @returns {number} Reading time in minutes
 */
export const calculateReadingTime = (text, wordsPerMinute = 200) => {
  if (!text) return 0;
  
  const wordCount = text.split(/\s+/).length;
  return Math.ceil(wordCount / wordsPerMinute);
};

/**
 * Gets browser information
 * @returns {Object} Browser information
 */
export const getBrowserInfo = () => {
  const userAgent = navigator.userAgent;
  let browserName = 'Unknown';
  let browserVersion = 'Unknown';

  if (userAgent.includes('Chrome') && !userAgent.includes('Edg')) {
    browserName = 'Chrome';
    browserVersion = userAgent.match(/Chrome\/(\d+)/)?.[1] || 'Unknown';
  } else if (userAgent.includes('Firefox')) {
    browserName = 'Firefox';
    browserVersion = userAgent.match(/Firefox\/(\d+)/)?.[1] || 'Unknown';
  } else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
    browserName = 'Safari';
    browserVersion = userAgent.match(/Version\/(\d+)/)?.[1] || 'Unknown';
  } else if (userAgent.includes('Edg')) {
    browserName = 'Edge';
    browserVersion = userAgent.match(/Edg\/(\d+)/)?.[1] || 'Unknown';
  }

  return {
    name: browserName,
    version: browserVersion,
    userAgent: userAgent
  };
};

/**
 * Handles API errors consistently
 * @param {Error} error - Error object
 * @returns {string} User-friendly error message
 */
export const handleApiError = (error) => {
  console.error('API Error:', error);
  
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.detail || error.response.data?.message;
    
    switch (status) {
      case 400:
        return message || 'Invalid request. Please check your input.';
      case 401:
        return 'Please log in to continue.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return message || `Error: ${status}`;
    }
  } else if (error.request) {
    // Request was made but no response received
    return 'Network error. Please check your connection.';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred.';
  }
};

/**
 * Creates a download link for data
 * @param {string} data - Data to download
 * @param {string} filename - Download filename
 * @param {string} type - MIME type
 */
export const downloadData = (data, filename, type = 'text/plain') => {
  const blob = new Blob([data], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Checks if device is mobile
 * @returns {boolean} True if mobile device
 */
export const isMobileDevice = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  );
};

/**
 * Local storage utilities with error handling
 */
export const storage = {
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('LocalStorage set error:', error);
      return false;
    }
  },
  
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('LocalStorage get error:', error);
      return defaultValue;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error('LocalStorage remove error:', error);
      return false;
    }
  },
  
  clear: () => {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('LocalStorage clear error:', error);
      return false;
    }
  }
};

/**
 * Throttle function to limit execution rate
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

export default {
  formatDate,
  truncateText,
  formatNumber,
  confidenceToPercentage,
  getPredictionColor,
  isValidUrl,
  debounce,
  capitalize,
  generateId,
  copyToClipboard,
  formatFileSize,
  isValidEmail,
  sanitizeHtml,
  calculateReadingTime,
  getBrowserInfo,
  handleApiError,
  downloadData,
  isMobileDevice,
  storage,
  throttle
};