import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './profile.css';

const Profile = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('personal');
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [profileData, setProfileData] = useState({
    personal: {
      name: '',
      email: '',
      phone: '',
      location: '',
      bio: '',
      avatar: ''
    },
    professional: {
      company: '',
      role: '',
      expertise: [],
      experience: ''
    },
    preferences: {
      language: 'en',
      timezone: 'UTC+5:30',
      notifications: true,
      newsletter: true,
      theme: 'light'
    }
  });

  const [stats, setStats] = useState({
    analyses: 0,
    accuracy: 0,
    modelsTrained: 0,
    datasets: 0
  });

  const [activities, setActivities] = useState([]);

  const API_BASE_URL = 'http://localhost:8000/api/v1';

  // Fetch profile data
  useEffect(() => {
    fetchProfile();
    fetchActivities();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/profile`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setProfileData({
          personal: data.personal,
          professional: data.professional,
          preferences: data.preferences
        });
        setStats({
          analyses: data.stats.analyses || 0,
          accuracy: data.stats.accuracy || 0,
          modelsTrained: data.stats.models_trained || 0,
          datasets: data.stats.datasets_uploaded || 0
        });
      } else {
        setError('Failed to load profile');
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const fetchActivities = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/profile/activity?limit=10`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      const data = await response.json();
      
      if (data.success) {
        setActivities(data.activities);
      }
    } catch (error) {
      console.error('Error fetching activities:', error);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');

      const response = await fetch(`${API_BASE_URL}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(profileData),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess('Profile updated successfully!');
        setIsEditing(false);
        fetchProfile(); // Refresh data
      } else {
        setError(data.detail || 'Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      setError('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    fetchProfile(); // Reset to original data
  };

  const handleAvatarUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/profile/avatar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setSuccess('Avatar updated successfully!');
        // Update avatar URL in state
        setProfileData(prev => ({
          ...prev,
          personal: {
            ...prev.personal,
            avatar: data.avatar_url
          }
        }));
      } else {
        setError(data.detail || 'Failed to upload avatar');
      }
    } catch (error) {
      console.error('Error uploading avatar:', error);
      setError('Failed to upload avatar');
    }
  };

  const addExpertise = (expertise) => {
    if (expertise && !profileData.professional.expertise.includes(expertise)) {
      setProfileData(prev => ({
        ...prev,
        professional: {
          ...prev.professional,
          expertise: [...prev.professional.expertise, expertise]
        }
      }));
    }
  };

  const removeExpertise = (index) => {
    setProfileData(prev => ({
      ...prev,
      professional: {
        ...prev.professional,
        expertise: prev.professional.expertise.filter((_, i) => i !== index)
      }
    }));
  };

  const formatTime = (timeString) => {
    const time = new Date(timeString);
    const now = new Date();
    const diffInHours = (now - time) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return `${Math.floor(diffInHours * 60)} minutes ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)} hours ago`;
    } else {
      return `${Math.floor(diffInHours / 24)} days ago`;
    }
  };

  if (loading) {
    return (
      <div className="profile-page">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h1>My Profile</h1>
        <p>Manage your personal information and account settings</p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="notification error">
          <span>⚠</span>
          {error}
        </div>
      )}
      {success && (
        <div className="notification success">
          <span>✅</span>
          {success}
        </div>
      )}

      <div className="profile-container">
        {/* Sidebar */}
        <div className="profile-sidebar">
          <div className="user-card">
            <div className="avatar-section">
              <div className="avatar-large">
                {profileData.personal.avatar ? (
                  <img 
                    src={`${API_BASE_URL}${profileData.personal.avatar}`} 
                    alt="Profile" 
                  />
                ) : (
                  <span>{profileData.personal.name.charAt(0)}</span>
                )}
              </div>
              <label className="change-avatar-btn">
                📷 Change Photo
                <input 
                  type="file" 
                  accept="image/*"
                  onChange={handleAvatarUpload}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
            
            <div className="user-info">
              <h3>{profileData.personal.name}</h3>
              <p>{profileData.personal.email}</p>
              <p className="user-role">{profileData.professional.role}</p>
            </div>

            <div className="user-stats">
              <div className="stat-item">
                <span className="stat-number">{stats.analyses}</span>
                <span className="stat-label">Analyses</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{stats.accuracy}%</span>
                <span className="stat-label">Accuracy</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{stats.modelsTrained}</span>
                <span className="stat-label">Models</span>
              </div>
            </div>
          </div>

          <nav className="profile-nav">
            <button 
              className={`nav-item ${activeTab === 'personal' ? 'active' : ''}`}
              onClick={() => setActiveTab('personal')}
            >
              👤 Personal Info
            </button>
            <button 
              className={`nav-item ${activeTab === 'professional' ? 'active' : ''}`}
              onClick={() => setActiveTab('professional')}
            >
              💼 Professional
            </button>
            <button 
              className={`nav-item ${activeTab === 'preferences' ? 'active' : ''}`}
              onClick={() => setActiveTab('preferences')}
            >
              ⚙️ Preferences
            </button>
            <button 
              className={`nav-item ${activeTab === 'activity' ? 'active' : ''}`}
              onClick={() => setActiveTab('activity')}
            >
              📊 Activity
            </button>
          </nav>
        </div>

        {/* Main Content */}
        <div className="profile-content">
          <div className="content-header">
            <h2>
              {activeTab === 'personal' && 'Personal Information'}
              {activeTab === 'professional' && 'Professional Details'}
              {activeTab === 'preferences' && 'Account Preferences'}
              {activeTab === 'activity' && 'Activity History'}
            </h2>
            
            {activeTab !== 'activity' && (
              <div className="header-actions">
                {!isEditing ? (
                  <button 
                    className="edit-btn"
                    onClick={() => setIsEditing(true)}
                  >
                    ✏️ Edit Profile
                  </button>
                ) : (
                  <div className="edit-actions">
                    <button 
                      className={`save-btn ${saving ? 'loading' : ''}`}
                      onClick={handleSave}
                      disabled={saving}
                    >
                      {saving ? (
                        <>
                          <span className="spinner"></span>
                          Saving...
                        </>
                      ) : (
                        '💾 Save Changes'
                      )}
                    </button>
                    <button 
                      className="cancel-btn" 
                      onClick={handleCancel}
                      disabled={saving}
                    >
                      ❌ Cancel
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Personal Information Tab */}
          {activeTab === 'personal' && (
            <div className="tab-content">
              <div className="form-grid">
                <div className="form-group">
                  <label>Full Name *</label>
                  <input 
                    type="text" 
                    value={profileData.personal.name}
                    onChange={(e) => setProfileData(prev => ({
                      ...prev,
                      personal: {...prev.personal, name: e.target.value}
                    }))}
                    disabled={!isEditing}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>Email Address *</label>
                  <input 
                    type="email" 
                    value={profileData.personal.email}
                    onChange={(e) => setProfileData(prev => ({
                      ...prev,
                      personal: {...prev.personal, email: e.target.value}
                    }))}
                    disabled={!isEditing}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>Phone Number</label>
                  <input 
                    type="tel" 
                    value={profileData.personal.phone}
                    onChange={(e) => setProfileData(prev => ({
                      ...prev,
                      personal: {...prev.personal, phone: e.target.value}
                    }))}
                    disabled={!isEditing}
                  />
                </div>
                
                <div className="form-group">
                  <label>Location</label>
                  <input 
                    type="text" 
                    value={profileData.personal.location}
                    onChange={(e) => setProfileData(prev => ({
                      ...prev,
                      personal: {...prev.personal, location: e.target.value}
                    }))}
                    disabled={!isEditing}
                  />
                </div>
                
                <div className="form-group full-width">
                  <label>Bio</label>
                  <textarea 
                    value={profileData.personal.bio}
                    onChange={(e) => setProfileData(prev => ({
                      ...prev,
                      personal: {...prev.personal, bio: e.target.value}
                    }))}
                    disabled={!isEditing}
                    rows="4"
                    placeholder="Tell us about yourself..."
                  />
                </div>
              </div>
            </div>
          )}

          {/* Professional Tab */}
          {activeTab === 'professional' && (
            <div className="tab-content">
              <div className="form-grid">
                <div className="form-group">
                  <label>Company</label>
                  <input 
                    type="text" 
                    value={profileData.professional.company}
                    onChange={(e) => setProfileData(prev => ({
                      ...prev,
                      professional: {...prev.professional, company: e.target.value}
                    }))}
                    disabled={!isEditing}
                  />
                </div>
                
                <div className="form-group">
                  <label>Role/Title</label>
                  <input 
                    type="text" 
                    value={profileData.professional.role}
                    onChange={(e) => setProfileData(prev => ({
                      ...prev,
                      professional: {...prev.professional, role: e.target.value}
                    }))}
                    disabled={!isEditing}
                  />
                </div>
                
                <div className="form-group">
                  <label>Experience</label>
                  <input 
                    type="text" 
                    value={profileData.professional.experience}
                    onChange={(e) => setProfileData(prev => ({
                      ...prev,
                      professional: {...prev.professional, experience: e.target.value}
                    }))}
                    disabled={!isEditing}
                  />
                </div>
                
                <div className="form-group full-width">
                  <label>Areas of Expertise</label>
                  <div className="expertise-tags">
                    {profileData.professional.expertise.map((exp, index) => (
                      <span key={index} className="expertise-tag">
                        {exp}
                        {isEditing && (
                          <button 
                            onClick={() => removeExpertise(index)}
                            className="remove-tag"
                          >
                            ×
                          </button>
                        )}
                      </span>
                    ))}
                    {isEditing && (
                      <input 
                        type="text" 
                        placeholder="Add expertise..."
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            addExpertise(e.target.value.trim());
                            e.target.value = '';
                          }
                        }}
                        className="add-expertise-input"
                      />
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="tab-content">
              <div className="preferences-grid">
                <div className="preference-group">
                  <h3>Language & Region</h3>
                  <div className="form-group">
                    <label>Language</label>
                    <select 
                      value={profileData.preferences.language}
                      onChange={(e) => setProfileData(prev => ({
                        ...prev,
                        preferences: {...prev.preferences, language: e.target.value}
                      }))}
                      disabled={!isEditing}
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Timezone</label>
                    <select 
                      value={profileData.preferences.timezone}
                      onChange={(e) => setProfileData(prev => ({
                        ...prev,
                        preferences: {...prev.preferences, timezone: e.target.value}
                      }))}
                      disabled={!isEditing}
                    >
                      <option value="UTC+5:30">IST (UTC+5:30)</option>
                      <option value="UTC-8">PST (UTC-8)</option>
                      <option value="UTC-5">EST (UTC-5)</option>
                      <option value="UTC">UTC</option>
                    </select>
                  </div>
                </div>

                <div className="preference-group">
                  <h3>Notifications</h3>
                  <div className="checkbox-group">
                    <label className="checkbox">
                      <input 
                        type="checkbox" 
                        checked={profileData.preferences.notifications}
                        onChange={(e) => setProfileData(prev => ({
                          ...prev,
                          preferences: {...prev.preferences, notifications: e.target.checked}
                        }))}
                        disabled={!isEditing}
                      />
                      <span>Email Notifications</span>
                    </label>
                    
                    <label className="checkbox">
                      <input 
                        type="checkbox" 
                        checked={profileData.preferences.newsletter}
                        onChange={(e) => setProfileData(prev => ({
                          ...prev,
                          preferences: {...prev.preferences, newsletter: e.target.checked}
                        }))}
                        disabled={!isEditing}
                      />
                      <span>Newsletter</span>
                    </label>
                  </div>
                </div>

                <div className="preference-group">
                  <h3>Appearance</h3>
                  <div className="theme-selector">
                    <label className="theme-option">
                      <input 
                        type="radio" 
                        name="theme"
                        value="light"
                        checked={profileData.preferences.theme === 'light'}
                        onChange={(e) => setProfileData(prev => ({
                          ...prev,
                          preferences: {...prev.preferences, theme: e.target.value}
                        }))}
                        disabled={!isEditing}
                      />
                      <span>Light Mode</span>
                    </label>
                    
                    <label className="theme-option">
                      <input 
                        type="radio" 
                        name="theme"
                        value="dark"
                        checked={profileData.preferences.theme === 'dark'}
                        onChange={(e) => setProfileData(prev => ({
                          ...prev,
                          preferences: {...prev.preferences, theme: e.target.value}
                        }))}
                        disabled={!isEditing}
                      />
                      <span>Dark Mode</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Activity Tab */}
          {activeTab === 'activity' && (
            <div className="tab-content">
              <div className="activity-timeline">
                <h3>Recent Activity</h3>
                {activities.length === 0 ? (
                  <div className="empty-state">
                    <p>No recent activity</p>
                  </div>
                ) : (
                  <div className="timeline">
                    {activities.map((activity, index) => (
                      <div key={activity.id} className="timeline-item">
                        <div className="timeline-marker"></div>
                        <div className="timeline-content">
                          <p>{activity.action}</p>
                          <span className="timeline-time">
                            {formatTime(activity.time)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="activity-stats">
                <h3>Usage Statistics</h3>
                <div className="stats-cards">
                  <div className="stat-card">
                    <span className="stat-value">{stats.analyses}</span>
                    <span className="stat-label">Total Analyses</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{stats.accuracy}%</span>
                    <span className="stat-label">Average Accuracy</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{stats.modelsTrained}</span>
                    <span className="stat-label">Models Trained</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{stats.datasets}</span>
                    <span className="stat-label">Datasets</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;