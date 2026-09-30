// Enhanced Storage Utility with Quota Management
class StorageManager {
  constructor() {
    this.maxStorageSize = 4 * 1024 * 1024; // 4MB limit
    this.maxResults = 20; // Maximum number of results to store
  }

  // Check if localStorage is available and has space
  isStorageAvailable() {
    try {
      const test = '__storage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch (e) {
      return false;
    }
  }

  // Get current storage usage
  getStorageUsage() {
    let totalSize = 0;
    for (let key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        totalSize += localStorage[key].length + key.length;
      }
    }
    return {
      used: totalSize,
      available: this.maxStorageSize - totalSize,
      percentage: (totalSize / this.maxStorageSize) * 100
    };
  }

  // Compress data before storing
  compressData(data) {
    try {
      // Remove unnecessary fields from results to save space
      if (Array.isArray(data)) {
        return data.map(item => ({
          id: item.id,
          prediction: item.prediction,
          confidence: item.confidence,
          timestamp: item.timestamp,
          title: item.title ? item.title.substring(0, 100) + '...' : '',
          text: item.text ? item.text.substring(0, 200) + '...' : '',
          source: item.source,
          method: item.method,
          // Remove large fields like full text, detailed analysis, etc.
        }));
      }
      return data;
    } catch (e) {
      console.error('Error compressing data:', e);
      return data;
    }
  }

  // Safe set item with quota management
  setItem(key, value) {
    if (!this.isStorageAvailable()) {
      console.warn('localStorage not available');
      return false;
    }

    try {
      // Check storage usage before setting
      const usage = this.getStorageUsage();
      if (usage.percentage > 80) {
        console.warn('Storage usage high, clearing old data');
        this.clearOldData();
      }

      // Compress the data
      const compressedData = this.compressData(value);
      const serializedData = JSON.stringify(compressedData);

      // Check if data fits in storage
      if (serializedData.length > this.maxStorageSize) {
        console.error('Data too large for localStorage');
        return false;
      }

      localStorage.setItem(key, serializedData);
      return true;
    } catch (e) {
      if (e.name === 'QuotaExceededError') {
        console.warn('Storage quota exceeded, clearing old data');
        this.clearOldData();
        // Try again after clearing
        try {
          const compressedData = this.compressData(value);
          localStorage.setItem(key, JSON.stringify(compressedData));
          return true;
        } catch (e2) {
          console.error('Still cannot store data after cleanup:', e2);
          return false;
        }
      } else {
        console.error('Error storing data:', e);
        return false;
      }
    }
  }

  // Safe get item
  getItem(key) {
    if (!this.isStorageAvailable()) {
      return null;
    }

    try {
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.error('Error retrieving data:', e);
      return null;
    }
  }

  // Remove item
  removeItem(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      console.error('Error removing item:', e);
      return false;
    }
  }

  // Clear old data to free up space
  clearOldData() {
    try {
      // Get all keys related to news analysis
      const keys = Object.keys(localStorage).filter(key => 
        key.startsWith('newsAnalysisResults_')
      );

      // For each user's results, keep only the most recent ones
      keys.forEach(key => {
        const data = this.getItem(key);
        if (data && Array.isArray(data)) {
          // Keep only the most recent 10 results
          const recentData = data.slice(0, 10);
          this.setItem(key, recentData);
        }
      });

      // Also clear any other non-essential data
      const nonEssentialKeys = Object.keys(localStorage).filter(key => 
        !key.includes('authToken') && 
        !key.includes('token') && 
        !key.includes('user') &&
        !key.startsWith('newsAnalysisResults_')
      );

      nonEssentialKeys.forEach(key => {
        localStorage.removeItem(key);
      });

      console.log('Cleared old data to free up storage');
    } catch (e) {
      console.error('Error clearing old data:', e);
    }
  }

  // Get storage info for debugging
  getStorageInfo() {
    const usage = this.getStorageUsage();
    const keys = Object.keys(localStorage);
    
    return {
      usage,
      totalKeys: keys.length,
      keys: keys.map(key => ({
        key,
        size: localStorage[key].length,
        isAnalysisResult: key.startsWith('newsAnalysisResults_')
      }))
    };
  }
}

// Create singleton instance
const storageManager = new StorageManager();

export default storageManager;
