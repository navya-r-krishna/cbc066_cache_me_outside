import React from 'react';
import { useApp } from '../context/AppContext';
import {
  LayoutDashboard,
  Sparkles,
  BookOpen,
  Sliders,
  RotateCcw,
  Zap,
  Brain,
  X,
} from 'lucide-react';

export function Sidebar({ mobileOpen, onCloseMobile }) {
  const { currentTab, setCurrentTab, stats, resetToMockDefaults } = useApp();

  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      id: 'library',
      label: 'Question Library',
      icon: BookOpen,
      badge: stats.accepted > 0 ? `${stats.accepted} accepted` : null,
    },
  ];

  const handleNavClick = (tabId) => {
    setCurrentTab(tabId);
    if (onCloseMobile) onCloseMobile();
  };

  return (
    <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="brand-icon-box">
            <Brain size={22} />
          </div>
          <div className="brand-title-wrap">
            <div className="brand-title">
              Interview<span>IQ</span>
            </div>
            <span className="brand-tag">AI Question Engine</span>
          </div>
          {mobileOpen && (
            <button
              onClick={onCloseMobile}
              style={{ marginLeft: 'auto', color: '#fff' }}
              aria-label="Close menu"
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-title">Navigation</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <div
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => handleNavClick(item.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleNavClick(item.id)}
            >
              <div className="nav-item-left">
                <Icon size={18} className="nav-icon" />
                <span>{item.label}</span>
              </div>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </div>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="backend-indicator-card">
          <div className="backend-info">
            <div className="status-dot mock" />
            <div>
              <div className="backend-label">
                Demo Mode
              </div>
              <div className="backend-sub">
                Backend Not Connected
              </div>
            </div>
          </div>
          <Zap size={15} style={{ color: 'var(--color-accent-sage)' }} />
        </div>

        <button
          className="btn-ghost"
          style={{ color: 'var(--sidebar-text)', fontSize: '12px', justifyContent: 'center' }}
          onClick={resetToMockDefaults}
          title="Reload preconfigured sample questions and candidate profiles"
        >
          <RotateCcw size={13} />
          Reset Demo Data
        </button>
      </div>
    </aside>
  );
}
