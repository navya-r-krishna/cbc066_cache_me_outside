import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Menu, Bell } from 'lucide-react';

export function Header({ onOpenMobile }) {
  const { currentTab, toasts } = useApp();
  const [showNotifications, setShowNotifications] = useState(false);

  const getHeaderTitles = () => {
    switch (currentTab) {
      case 'dashboard':
        return {
          title: 'Home',
          subtitle: '',
        };
      case 'library':
        return {
          title: 'Question Library',
          subtitle: 'Manage and review your saved interview questions and evaluation rubrics',
        };
      default:
        return {
          title: 'InterviewIQ',
          subtitle: '',
        };
    }
  };

  const { title, subtitle } = getHeaderTitles();

  return (
    <header className="top-header">
      <div className="header-left">
        <button
          className="btn-ghost menu-toggle-btn"
          onClick={onOpenMobile}
          aria-label="Open sidebar menu"
        >
          <Menu size={20} />
        </button>
        <div className="page-title-group">
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>

      <div className="header-right">
        {currentTab !== 'dashboard' && (
          <div style={{ position: 'relative' }}>
            <button
              className="header-icon-btn"
              onClick={() => setShowNotifications(!showNotifications)}
              aria-label="Toggle notifications"
            >
              <Bell size={18} />
              {toasts.length > 0 && <span className="notif-badge-pill">{toasts.length}</span>}
            </button>

            {showNotifications && (
              <div
                className="card"
                style={{
                  position: 'absolute',
                  right: 0,
                  top: 48,
                  width: 310,
                  padding: '14px 16px',
                  zIndex: 50,
                  boxShadow: 'var(--shadow-lg)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 10,
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: 13 }}>Activity Stream</div>
                  <button
                    className="btn-ghost"
                    style={{ fontSize: 11, padding: '2px 6px' }}
                    onClick={() => setShowNotifications(false)}
                  >
                    Close
                  </button>
                </div>

                {toasts.length === 0 ? (
                  <div style={{ fontSize: 12.5, color: 'var(--text-muted)', padding: '12px 0' }}>
                    No recent activity events.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 220, overflowY: 'auto' }}>
                    {toasts.map((t) => (
                      <div
                        key={t.id}
                        style={{
                          padding: '8px 10px',
                          background: 'var(--color-surface-subtle)',
                          borderRadius: 6,
                          border: '1px solid var(--color-border)',
                          fontSize: 12,
                        }}
                      >
                        <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{t.title}</div>
                        <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>{t.message}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
