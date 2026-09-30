import api from './api';

export const modelTrainingService = {
  // Get available datasets
  getDatasets: async () => {
    try {
      const response = await api.get('/api/v1/admin/datasets');
      return response.data;
    } catch (error) {
      console.error('Error fetching datasets:', error);
      throw error;
    }
  },

  // Start model training
  startTraining: async (trainingConfig) => {
    try {
      const response = await api.post('/api/v1/admin/train-model', trainingConfig);
      return response.data;
    } catch (error) {
      console.error('Error starting training:', error);
      throw error;
    }
  },

  // Get training status
  getTrainingStatus: async (trainingId) => {
    try {
      const response = await api.get(`/api/v1/admin/training-status/${trainingId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching training status:', error);
      throw error;
    }
  },

  // Stop training
  stopTraining: async (trainingId) => {
    try {
      const response = await api.post(`/api/v1/admin/stop-training/${trainingId}`);
      return response.data;
    } catch (error) {
      console.error('Error stopping training:', error);
      throw error;
    }
  },

  // Get training history
  getTrainingHistory: async () => {
    try {
      const response = await api.get('/api/v1/admin/training-history');
      return response.data;
    } catch (error) {
      console.error('Error fetching training history:', error);
      throw error;
    }
  },

  // Deploy model
  deployModel: async (modelId) => {
    try {
      const response = await api.post(`/api/v1/admin/deploy-model/${modelId}`);
      return response.data;
    } catch (error) {
      console.error('Error deploying model:', error);
      throw error;
    }
  },

  // Test model
  testModel: async (modelId, testData) => {
    try {
      const response = await api.post(`/api/v1/admin/test-model/${modelId}`, testData);
      return response.data;
    } catch (error) {
      console.error('Error testing model:', error);
      throw error;
    }
  }
};