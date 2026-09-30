//src/contexts/AuthContext.jsx

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authAPI, apiUtils } from '../services/api';

// Auth state actions
const AuthActions = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  REGISTER_START: 'REGISTER_START',
  REGISTER_SUCCESS: 'REGISTER_SUCCESS',
  REGISTER_FAILURE: 'REGISTER_FAILURE',
  SET_USER: 'SET_USER',
  UPDATE_USER: 'UPDATE_USER',
  CLEAR_ERROR: 'CLEAR_ERROR',
  SET_LOADING: 'SET_LOADING',
  REFRESH_TOKEN_START: 'REFRESH_TOKEN_START',
  REFRESH_TOKEN_SUCCESS: 'REFRESH_TOKEN_SUCCESS',
  REFRESH_TOKEN_FAILURE: 'REFRESH_TOKEN_FAILURE'
};

// Initial state
const initialState = {
  user: null,
  token: localStorage.getItem('authToken'),
  isAuthenticated: false,
  isLoading: false,
  error: null,
  isInitialized: false,
  isRefreshingToken: false
};

// Auth reducer
const authReducer = (state, action) => {
  switch (action.type) {
    case AuthActions.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload
      };

    case AuthActions.LOGIN_START:
    case AuthActions.REGISTER_START:
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case AuthActions.LOGIN_SUCCESS:
    case AuthActions.REGISTER_SUCCESS:
      localStorage.setItem('authToken', action.payload.access_token);
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        isInitialized: true
      };

    case AuthActions.LOGIN_FAILURE:
    case AuthActions.REGISTER_FAILURE:
      localStorage.removeItem('authToken');
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
        isInitialized: true
      };

    case AuthActions.LOGOUT:
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        isInitialized: true
      };

    case AuthActions.SET_USER:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isInitialized: true
      };

    case AuthActions.UPDATE_USER:
      return {
        ...state,
        user: { ...state.user, ...action.payload }
      };

    case AuthActions.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };

    case AuthActions.REFRESH_TOKEN_START:
      return {
        ...state,
        isRefreshingToken: true
      };

    case AuthActions.REFRESH_TOKEN_SUCCESS:
      localStorage.setItem('authToken', action.payload.access_token);
      return {
        ...state,
        token: action.payload.access_token,
        isRefreshingToken: false
      };

    case AuthActions.REFRESH_TOKEN_FAILURE:
      localStorage.removeItem('authToken');
      return {
        ...state,
        token: null,
        isAuthenticated: false,
        isRefreshingToken: false,
        user: null
      };

    default:
      return state;
  }
};

// Create context
const AuthContext = createContext();

// Auth provider component
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('authToken');
      
      if (token) {
        try {
          dispatch({ type: AuthActions.SET_LOADING, payload: true });
          
          // Verify token and get user data
          const userData = await authAPI.getCurrentUser();
          
          dispatch({
            type: AuthActions.SET_USER,
            payload: userData
          });
        } catch (error) {
          console.error('Auth initialization failed:', error);
          
          // If token is invalid, clear it
          if (error.status === 401) {
            localStorage.removeItem('authToken');
          }
          
          dispatch({
            type: AuthActions.SET_USER,
            payload: null
          });
        } finally {
          dispatch({ type: AuthActions.SET_LOADING, payload: false });
        }
      } else {
        dispatch({
          type: AuthActions.SET_USER,
          payload: null
        });
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      dispatch({ type: AuthActions.LOGIN_START });

      const response = await authAPI.login(email, password);

      // Token को localStorage में save करें
      localStorage.setItem("authToken", response.access_token);
      
      // User data fetch करें
      const userData = await authAPI.getCurrentUser();

      dispatch({
        type: AuthActions.LOGIN_SUCCESS,
        payload: { 
          access_token: response.access_token, 
          user: userData 
        }
      });

      return { success: true, data: userData };
    } catch (error) {
      const errorMessage = apiUtils.getErrorMessage(error);
      
      // Clear invalid token
      localStorage.removeItem('authToken');
      
      dispatch({
        type: AuthActions.LOGIN_FAILURE,
        payload: errorMessage
      });

      return { success: false, error: errorMessage };
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      dispatch({ type: AuthActions.REGISTER_START });

      const response = await authAPI.register(userData);
      
      // If registration includes auto-login
      if (response.access_token) {
        localStorage.setItem("authToken", response.access_token);
        const userData = await authAPI.getCurrentUser();
        
        dispatch({
          type: AuthActions.REGISTER_SUCCESS,
          payload: { 
            access_token: response.access_token, 
            user: userData 
          }
        });
      } else {
        // Registration successful but no auto-login
        dispatch({
          type: AuthActions.REGISTER_SUCCESS,
          payload: response
        });
      }

      return { success: true, data: response };
    } catch (error) {
      const errorMessage = apiUtils.getErrorMessage(error);
      
      dispatch({
        type: AuthActions.REGISTER_FAILURE,
        payload: errorMessage
      });

      return { success: false, error: errorMessage };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Call logout API to invalidate token on server
      await authAPI.logout();
    } catch (error) {
      console.error('Logout API error:', error);
      // Continue with client-side logout even if API fails
    } finally {
      dispatch({ type: AuthActions.LOGOUT });
    }
  };

  // Update user profile
  const updateUser = async (userData) => {
    try {
      const updatedUser = await authAPI.updateProfile(userData);
      
      dispatch({
        type: AuthActions.UPDATE_USER,
        payload: updatedUser
      });

      return { success: true, data: updatedUser };
    } catch (error) {
      const errorMessage = apiUtils.getErrorMessage(error);
      return { success: false, error: errorMessage };
    }
  };

  // Refresh token function
  const refreshToken = async () => {
    try {
      dispatch({ type: AuthActions.REFRESH_TOKEN_START });
      
      // This would require a refresh token endpoint
      // const response = await authAPI.refreshToken(refreshToken);
      // For now, we'll just get current user to validate token
      const userData = await authAPI.getCurrentUser();
      
      dispatch({
        type: AuthActions.REFRESH_TOKEN_SUCCESS,
        payload: { access_token: state.token }
      });
      
      return { success: true };
    } catch (error) {
      dispatch({ type: AuthActions.REFRESH_TOKEN_FAILURE });
      return { success: false, error: 'Token refresh failed' };
    }
  };

  // Clear error
  const clearError = () => {
    dispatch({ type: AuthActions.CLEAR_ERROR });
  };

  // Check if user has specific role
  const hasRole = (role) => {
    return state.user?.roles?.includes(role) || state.user?.role === role || false;
  };

  // Check if user has specific permission
  const hasPermission = (permission) => {
    return state.user?.permissions?.includes(permission) || false;
  };

  // Check if user is admin
  const isAdmin = () => {
    return hasRole('admin') || hasRole('administrator') || state.user?.is_admin === true;
  };

  // Validate current token
  const validateToken = async () => {
    try {
      if (!state.token) {
        return false;
      }
      
      await authAPI.getCurrentUser();
      return true;
    } catch (error) {
      if (error.status === 401) {
        // Token is invalid, logout user
        logout();
        return false;
      }
      return true; // Assume token is valid for other errors
    }
  };

  // Get user display name
  const getDisplayName = () => {
    if (!state.user) return '';
    
    if (state.user.full_name) {
      return state.user.full_name;
    } else if (state.user.first_name && state.user.last_name) {
      return `${state.user.first_name} ${state.user.last_name}`;
    } else {
      return state.user.email || state.user.username || 'User';
    }
  };

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!state.user) return 'U';
    
    const displayName = getDisplayName();
    return displayName
      .split(' ')
      .map(name => name[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Value to provide
  const value = {
    // State
    user: state.user,
    token: state.token,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    isInitialized: state.isInitialized,
    isRefreshingToken: state.isRefreshingToken,

    // Actions
    login,
    register,
    logout,
    updateUser,
    refreshToken,
    clearError,
    validateToken,
    hasRole,
    hasPermission,
    isAdmin,
    getDisplayName,
    getUserInitials
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

// Higher Order Component for protecting routes
export const withAuth = (Component) => {
  return function WithAuthComponent(props) {
    const { isAuthenticated, isLoading, isInitialized } = useAuth();
    
    if (isLoading || !isInitialized) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading...</p>
          </div>
        </div>
      );
    }
    
    if (!isAuthenticated) {
      // Redirect to login
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      return null;
    }
    
    return <Component {...props} />;
  };
};

// Higher Order Component for role-based access
export const withRole = (Component, requiredRole) => {
  return function WithRoleComponent(props) {
    const { isAuthenticated, isLoading, isInitialized, hasRole } = useAuth();
    
    if (isLoading || !isInitialized) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading...</p>
          </div>
        </div>
      );
    }
    
    if (!isAuthenticated) {
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      return null;
    }
    
    if (!hasRole(requiredRole)) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center max-w-md mx-auto p-6">
            <div className="text-red-500 text-6xl mb-4">🚫</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
            <p className="text-gray-600 mb-4">
              You don't have permission to access this page. Required role: {requiredRole}
            </p>
            <button 
              onClick={() => window.history.back()}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
};

// Higher Order Component for admin access
export const withAdmin = (Component) => {
  return withRole(Component, 'admin');
};

// Public route component (for already authenticated users)
export const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    window.location.href = '/dashboard';
    return null;
  }
  
  return children;
};

export default AuthContext;