import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { testBackendConnection } from '../../services/api';
import { WeightSliders, DEFAULT_WEIGHTS } from '../Common/WeightSliders';
import {
  User,
  Server,
  Sliders,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Zap,
  Building,
  Mail,
  Briefcase,
} from 'lucide-react';

export function SettingsView() {
  const { profile, updateProfile, settings, updateSettings, resetToMockDefaults, addToast } =
    useApp();

  // Profile Form State
  const [profileForm, setProfileForm] = useState({
    name: profile.name || '',
    email: profile.email || '',
    role: profile.role || '',
    company: profile.company || '',
    department: profile.department || '',
  });

  // Settings State
  const [apiBaseUrl, setApiBaseUrl] = useState(settings.apiBaseUrl || 'http://localhost:8000/api/v1');
  const [defaultDifficulty, setDefaultDifficulty] = useState(
    settings.defaultDifficulty || 'Senior'
  );
  const [defaultQuestionCount, setDefaultQuestionCount] = useState(
    settings.defaultQuestionCount || 6
  );
  const [defaultWeights, setDefaultWeights] = useState(
    settings.defaultWeights || DEFAULT_WEIGHTS
  );

  // Connection testing state
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await testBackendConnection(apiBaseUrl);
      setTestResult(res);
      if (res.success) {
        addToast({
          type: 'success',
          title: 'Backend Connected',
          message: res.message,
        });
      } else {
        addToast({
          type: 'info',
          title: 'Backend Offline',
          message: 'FastAPI server not responding. Operating in Demo Mode.',
        });
      }
    } catch (err) {
      setTestResult({ success: false, message: err.message });
      addToast({
        type: 'warning',
        title: 'Connection Check',
        message: 'Could not reach server. Continuing in Demo Mode.',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = (e) => {
    e.preventDefault();
    updateProfile(profileForm);
    updateSettings({
      apiBaseUrl,
      defaultDifficulty,
      defaultQuestionCount: parseInt(defaultQuestionCount, 10),
      defaultWeights,
    });
    addToast({
      type: 'success',
      title: 'Settings Saved',
      message: 'Profile details, default weights, and session settings updated successfully.',
    });
  };

  return (
    <div className="settings-container animate-fade-in" style={{ paddingBottom: 40 }}>
      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {/* Backend Connection Status Card */}
        <div className="card settings-section-card">
          <div className="settings-card-header">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Server size={20} style={{ color: 'var(--primary)' }} />
                <h2 className="settings-card-title">Backend Connection Status</h2>
              </div>
              <span
                className="badge badge-warning"
                style={{ fontWeight: 800, padding: '5px 12px', fontSize: 12 }}
              >
                Demo Mode — Backend Not Connected
              </span>
            </div>
            <p className="settings-card-subtitle" style={{ marginTop: 6 }}>
              InterviewIQ is currently running in local demo mode. AI question synthesis and
              evaluations are simulated on the client without contacting external servers.
            </p>
          </div>

          <div
            style={{
              padding: '16px 18px',
              background: 'var(--color-primary-light)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-accent-sage)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 12,
              marginBottom: 16,
            }}
          >
            <div>
              <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--text-main)' }}>
                FastAPI Gateway Configuration
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                When your FastAPI backend is running (e.g. <code>uvicorn main:app --port 8000</code>),
                the service layer in <code>src/services/api.js</code> can seamlessly connect.
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="text"
                className="form-input"
                style={{ width: 260, fontSize: 13 }}
                placeholder="http://localhost:8000/api/v1"
                value={apiBaseUrl}
                onChange={(e) => setApiBaseUrl(e.target.value)}
              />
              <button
                type="button"
                className="btn-secondary"
                style={{ fontSize: 12.5, padding: '7px 12px' }}
                onClick={handleTestConnection}
                disabled={isTesting}
              >
                {isTesting ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
                {isTesting ? 'Testing...' : 'Test Connection'}
              </button>
            </div>
          </div>

          {testResult && (
            <div
              style={{
                fontSize: 12.5,
                color: testResult.success ? 'var(--success-text)' : '#b45309',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              {testResult.success ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
              <span>{testResult.message}</span>
            </div>
          )}
        </div>

        {/* Profile Information Form */}
        <div className="card settings-section-card">
          <div className="settings-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <User size={20} style={{ color: 'var(--primary)' }} />
              <h2 className="settings-card-title">Profile Information</h2>
            </div>
            <p className="settings-card-subtitle">
              Your interviewer identification details used for batch attribution and exports.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">
                <User size={13} style={{ display: 'inline', marginRight: 4 }} />
                Interviewer Name
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Sarah Jenkins"
                value={profileForm.name}
                onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">
                <Mail size={13} style={{ display: 'inline', marginRight: 4 }} />
                Interviewer Email
              </label>
              <input
                type="email"
                className="form-input"
                placeholder="e.g. sarah.jenkins@techflow.io"
                value={profileForm.email}
                onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">
                <Briefcase size={13} style={{ display: 'inline', marginRight: 4 }} />
                Title / Role
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Staff Engineering Hiring Lead"
                value={profileForm.role}
                onChange={(e) => setProfileForm({ ...profileForm, role: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">
                <Building size={13} style={{ display: 'inline', marginRight: 4 }} />
                Company / Organization
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. TechFlow Systems"
                value={profileForm.company}
                onChange={(e) => setProfileForm({ ...profileForm, company: e.target.value })}
              />
            </div>

            <div className="form-group" style={{ gridColumn: 'span 2', margin: 0 }}>
              <label className="form-label">Default Department</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Platform & Infrastructure"
                value={profileForm.department}
                onChange={(e) => setProfileForm({ ...profileForm, department: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Default Difficulty & Question Count Settings */}
        <div className="card settings-section-card">
          <div className="settings-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Sliders size={20} style={{ color: 'var(--primary)' }} />
              <h2 className="settings-card-title">Default Generation Settings</h2>
            </div>
            <p className="settings-card-subtitle">
              Presets applied when initializing new candidate generation sessions.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
            <div>
              <label className="form-label">Default Difficulty</label>
              <select
                className="form-select"
                value={defaultDifficulty}
                onChange={(e) => setDefaultDifficulty(e.target.value)}
              >
                <option value="Junior">Junior / Entry</option>
                <option value="Mid">Mid-Level</option>
                <option value="Senior">Senior</option>
                <option value="Staff">Staff / Principal</option>
              </select>
            </div>

            <div>
              <label className="form-label">Default Question Count</label>
              <select
                className="form-select"
                value={defaultQuestionCount}
                onChange={(e) => setDefaultQuestionCount(e.target.value)}
              >
                <option value={4}>4 questions</option>
                <option value={5}>5 questions</option>
                <option value={6}>6 questions</option>
                <option value={8}>8 questions</option>
                <option value={10}>10 questions</option>
              </select>
            </div>
          </div>
        </div>

        {/* Default Competency Weight Settings */}
        <div className="card settings-section-card">
          <div className="settings-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Sliders size={20} style={{ color: 'var(--primary)' }} />
              <h2 className="settings-card-title">Default Competency Weights</h2>
            </div>
            <p className="settings-card-subtitle">
              Set your preferred baseline evaluation distribution (always totals 100%).
            </p>
          </div>

          <WeightSliders
            weights={defaultWeights}
            onChange={setDefaultWeights}
            onReset={() => setDefaultWeights(DEFAULT_WEIGHTS)}
            defaultWeights={DEFAULT_WEIGHTS}
            title="Baseline Dimension Weights"
          />
        </div>

        {/* Demo Data Management */}
        <div className="card settings-section-card">
          <div className="settings-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <RotateCcw size={20} style={{ color: 'var(--primary)' }} />
              <h2 className="settings-card-title">Reset Demo Workspace</h2>
            </div>
            <p className="settings-card-subtitle">
              Restore the initial preloaded sample questions, candidate sessions, and rubrics.
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '6px 0',
            }}
          >
            <div>
              <div style={{ fontSize: 13.5, fontWeight: 600 }}>Reset Sample Questions</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Re-seeds initial demo batches for Maya Lin and David Kross.
              </div>
            </div>
            <button type="button" className="btn-secondary" onClick={resetToMockDefaults}>
              <RotateCcw size={14} />
              Reset Demo Data
            </button>
          </div>
        </div>

        {/* Save Bar */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <button type="submit" className="btn-primary" style={{ padding: '11px 28px', fontSize: 14 }}>
            Save Settings & Profile
          </button>
        </div>
      </form>
    </div>
  );
}
