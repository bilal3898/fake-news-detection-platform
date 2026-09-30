// frontend/src/components/Settings.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userAPI } from '../services/api';
import './Settings.css';

const Settings = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' }); // type: 'success' | 'error'

  /* ---------- life-cycle ---------- */
  useEffect(() => {
    loadSettings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---------- helpers ---------- */
  const showMessage = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), 4000);
  };

  const getDefaultSettings = () => ({
    profile: {
      name: user?.full_name || 'User',
      email: user?.email || '',
      bio: '',
      company: '',
      location: '',
    },
    account: {
      language: 'en',
      timezone: 'UTC-8',
      dateFormat: 'MM/DD/YYYY',
      resultsPerPage: 20,
      emailNotifications: true,
      pushNotifications: false,
      newsletter: true,
    },
    security: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
      twoFactorAuth: false,
      loginAlerts: true,
    },
    api: {
      apiKey: `fn_sk_${user?.id || 'user'}_${user?.email?.replace('@', '_') || 'email'}`,
      rateLimit: 1000,
      webhookUrl: '',
      autoRefresh: true,
    },
  });

  /* ---------- API calls ---------- */
  const loadSettings = async () => {
    try {
      setLoading(true);
      const { data } = await userAPI.getSettings();
      setSettings(data.settings);
    } catch (err) {
      console.error(err);
      showMessage('Failed to load settings', 'error');
      setSettings(getDefaultSettings());
    } finally {
      setLoading(false);
    }
  };

  const saveProfile = async () => {
    setSaving(true);
    try {
      await userAPI.updateProfile(settings.profile);
      showMessage('Profile saved!');
    } catch (err) {
      console.error(err);
      showMessage(err?.response?.data?.detail || 'Profile update failed', 'error');
    } finally {
      setSaving(false);
    }
  };

  const saveAccount = async () => {
    setSaving(true);
    try {
      await userAPI.updateSettings({ account: settings.account });
      showMessage('Account preferences saved!');
    } catch (err) {
      console.error(err);
      showMessage(err?.response?.data?.detail || 'Account update failed', 'error');
    } finally {
      setSaving(false);
    }
  };

  const saveSecurity = async () => {
    const { currentPassword, newPassword, confirmPassword } = settings.security;
    if (!newPassword) return showMessage('Please enter a new password', 'error');
    if (newPassword !== confirmPassword) return showMessage('Passwords do not match', 'error');

    setSaving(true);
    try {
      await userAPI.changePassword({ currentPassword, newPassword, confirmPassword });
      showMessage('Password changed successfully!');
      // clear fields
      setSettings(s => ({
        ...s,
        security: { ...s.security, currentPassword: '', newPassword: '', confirmPassword: '' },
      }));
    } catch (err) {
      console.error(err);
      showMessage(err?.response?.data?.detail || 'Password change failed', 'error');
    } finally {
      setSaving(false);
    }
  };

  const saveApi = async () => {
    setSaving(true);
    try {
      await userAPI.updateSettings({ api: settings.api });
      showMessage('API settings saved!');
    } catch (err) {
      console.error(err);
      showMessage(err?.response?.data?.detail || 'API update failed', 'error');
    } finally {
      setSaving(false);
    }
  };

  const copyApiKey = async () => {
    try {
      await navigator.clipboard.writeText(settings.api.apiKey);
      showMessage('API key copied!');
    } catch {
      showMessage('Could not copy API key', 'error');
    }
  };

  const regenerateApiKey = async () => {
    if (!window.confirm('Regenerate API key? The old one will stop working.')) return;
    try {
      const { data } = await userAPI.regenerateApiKey();
      setSettings(s => ({ ...s, api: { ...s.api, apiKey: data.apiKey } }));
      showMessage('API key regenerated!');
    } catch (err) {
      console.error(err);
      showMessage(err?.response?.data?.detail || 'Regeneration failed', 'error');
    }
  };

  /* ---------- render ---------- */
  if (loading)
    return (
      <div className="settings-page">
        <div className="loading">Loading settings…</div>
      </div>
    );

  if (!settings)
    return (
      <div className="settings-page">
        <div className="error">Could not load settings</div>
      </div>
    );

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Manage your account preferences and security settings</p>
        {message.text && <div className={`message ${message.type}`}>{message.text}</div>}
      </div>

      <div className="settings-container">
        {/* ------------ Sidebar ------------ */}
        <div className="settings-sidebar">
          <div className="user-profile">
            <div className="avatar">{user?.full_name?.[0] || 'U'}</div>
            <div className="user-info">
              <h3>{settings.profile.name}</h3>
              <p>{settings.profile.email}</p>
            </div>
          </div>

          <nav className="settings-nav">
            {['profile', 'account', 'security', 'api'].map(tab => (
              <button
                key={tab}
                className={`nav-item ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === 'profile' && '👤'}
                {tab === 'account' && '⚙️'}
                {tab === 'security' && '🔒'}
                {tab === 'api' && '🔑'} {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>

          <div className="sidebar-footer">
            <button className="logout-btn" onClick={logout}>
              🚪 Logout
            </button>
          </div>
        </div>

        {/* ------------ Main Content ------------ */}
        <div className="settings-content">
          {activeTab === 'profile' && (
            <div className="settings-section">
              <h2>Profile Settings</h2>
              <p>Update your personal information and preferences</p>
              <div className="settings-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>Full Name</label>
                    <input
                      type="text"
                      value={settings.profile.name}
                      onChange={e =>
                        setSettings(s => ({ ...s, profile: { ...s.profile, name: e.target.value } }))
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label>Email Address</label>
                    <input type="email" value={settings.profile.email} disabled />
                  </div>
                </div>

                <div className="form-group">
                  <label>Bio</label>
                  <textarea
                    rows="4"
                    value={settings.profile.bio}
                    onChange={e =>
                      setSettings(s => ({ ...s, profile: { ...s.profile, bio: e.target.value } }))
                    }
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Company</label>
                    <input
                      type="text"
                      value={settings.profile.company}
                      onChange={e =>
                        setSettings(s => ({ ...s, profile: { ...s.profile, company: e.target.value } }))
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label>Location</label>
                    <input
                      type="text"
                      value={settings.profile.location}
                      onChange={e =>
                        setSettings(s => ({ ...s, profile: { ...s.profile, location: e.target.value } }))
                      }
                    />
                  </div>
                </div>

                <div className="form-actions">
                  <button className="save-btn" onClick={saveProfile} disabled={saving}>
                    {saving ? '💾 Saving…' : '💾 Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'account' && (
            <div className="settings-section">
              <h2>Account Preferences</h2>
              <p>Customize your application experience</p>
              <div className="settings-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>Language</label>
                    <select
                      value={settings.account.language}
                      onChange={e =>
                        setSettings(s => ({ ...s, account: { ...s.account, language: e.target.value } }))
                      }
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
                      value={settings.account.timezone}
                      onChange={e =>
                        setSettings(s => ({ ...s, account: { ...s.account, timezone: e.target.value } }))
                      }
                    >
                      <option value="UTC-8">Pacific Time (UTC-8)</option>
                      <option value="UTC-5">Eastern Time (UTC-5)</option>
                      <option value="UTC">UTC</option>
                      <option value="UTC+1">Central European Time (UTC+1)</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>Date Format</label>
                  <select
                    value={settings.account.dateFormat}
                    onChange={e =>
                      setSettings(s => ({ ...s, account: { ...s.account, dateFormat: e.target.value } }))
                    }
                  >
                    <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                    <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Results Per Page</label>
                  <input
                    type="number"
                    min="10"
                    max="100"
                    value={settings.account.resultsPerPage}
                    onChange={e =>
                      setSettings(s => ({
                        ...s,
                        account: { ...s.account, resultsPerPage: parseInt(e.target.value) || 20 },
                      }))
                    }
                  />
                </div>

                <div className="notification-settings">
                  <h3>Notification Preferences</h3>
                  <div className="checkbox-group">
                    {['emailNotifications', 'pushNotifications', 'newsletter'].map(key => (
                      <label className="checkbox" key={key}>
                        <input
                          type="checkbox"
                          checked={settings.account[key]}
                          onChange={e =>
                            setSettings(s => ({
                              ...s,
                              account: { ...s.account, [key]: e.target.checked },
                            }))
                          }
                        />
                        <span>
                          {key === 'emailNotifications' && 'Email Notifications'}
                          {key === 'pushNotifications' && 'Push Notifications'}
                          {key === 'newsletter' && 'Newsletter'}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="form-actions">
                  <button className="save-btn" onClick={saveAccount} disabled={saving}>
                    {saving ? '💾 Saving…' : '💾 Save Preferences'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="settings-section">
              <h2>Security Settings</h2>
              <p>Manage your password and security preferences</p>
              <div className="settings-form">
                <div className="form-group">
                  <label>Current Password</label>
                  <input
                    type="password"
                    value={settings.security.currentPassword}
                    onChange={e =>
                      setSettings(s => ({
                        ...s,
                        security: { ...s.security, currentPassword: e.target.value },
                      }))
                    }
                  />
                </div>

                <div className="form-group">
                  <label>New Password</label>
                  <input
                    type="password"
                    value={settings.security.newPassword}
                    onChange={e =>
                      setSettings(s => ({
                        ...s,
                        security: { ...s.security, newPassword: e.target.value },
                      }))
                    }
                  />
                </div>

                <div className="form-group">
                  <label>Confirm New Password</label>
                  <input
                    type="password"
                    value={settings.security.confirmPassword}
                    onChange={e =>
                      setSettings(s => ({
                        ...s,
                        security: { ...s.security, confirmPassword: e.target.value },
                      }))
                    }
                  />
                </div>

                <div className="security-features">
                  <h3>Security Features</h3>
                  <div className="checkbox-group">
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={settings.security.twoFactorAuth}
                        onChange={e =>
                          setSettings(s => ({
                            ...s,
                            security: { ...s.security, twoFactorAuth: e.target.checked },
                          }))
                        }
                      />
                      <span>Two-Factor Authentication</span>
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={settings.security.loginAlerts}
                        onChange={e =>
                          setSettings(s => ({
                            ...s,
                            security: { ...s.security, loginAlerts: e.target.checked },
                          }))
                        }
                      />
                      <span>Login Alerts</span>
                    </label>
                  </div>
                </div>

                <div className="form-actions">
                  <button className="save-btn" onClick={saveSecurity} disabled={saving}>
                    {saving ? '🔒 Updating…' : '🔒 Update Security'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="settings-section">
              <h2>API Settings</h2>
              <p>Manage your API keys and integration settings</p>
              <div className="settings-form">
                <div className="api-key-section">
                  <label>API Key</label>
                  <div className="api-key-display">
                    <code>{settings.api.apiKey}</code>
                    <button className="copy-btn" onClick={copyApiKey}>
                      📋 Copy
                    </button>
                    <button className="regenerate-btn" onClick={regenerateApiKey}>
                      🔄 Regenerate
                    </button>
                  </div>
                  <p className="api-warning">⚠️ Keep your API key secure. Do not share it publicly.</p>
                </div>

                <div className="form-group">
                  <label>Rate Limit (requests/hour)</label>
                  <input
                    type="number"
                    min="100"
                    max="10000"
                    value={settings.api.rateLimit}
                    onChange={e =>
                      setSettings(s => ({
                        ...s,
                        api: { ...s.api, rateLimit: parseInt(e.target.value) || 1000 },
                      }))
                    }
                  />
                </div>

                <div className="form-group">
                  <label>Webhook URL</label>
                  <input
                    type="url"
                    placeholder="https://your-domain.com/webhook"
                    value={settings.api.webhookUrl}
                    onChange={e =>
                      setSettings(s => ({
                        ...s,
                        api: { ...s.api, webhookUrl: e.target.value },
                      }))
                    }
                  />
                </div>

                <div className="checkbox-group">
                  <label className="checkbox">
                    <input
                      type="checkbox"
                      checked={settings.api.autoRefresh}
                      onChange={e =>
                        setSettings(s => ({
                          ...s,
                          api: { ...s.api, autoRefresh: e.target.checked },
                        }))
                      }
                    />
                    <span>Auto-refresh API tokens</span>
                  </label>
                </div>

                <div className="form-actions">
                  <button className="save-btn" onClick={saveApi} disabled={saving}>
                    {saving ? '💾 Saving…' : '💾 Save API Settings'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;