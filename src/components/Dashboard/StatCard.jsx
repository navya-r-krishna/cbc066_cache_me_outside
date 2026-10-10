import React from 'react';

export function StatCard({ title, value, icon: Icon, color = 'purple', footerText, trend }) {
  const colorMap = {
    purple: {
      bg: 'var(--color-primary-light)',
      icon: 'var(--color-primary)',
      border: 'var(--color-accent-sage)',
    },
    forest: {
      bg: 'var(--color-primary-light)',
      icon: 'var(--color-primary)',
      border: 'var(--color-accent-sage)',
    },
    green: {
      bg: 'var(--color-success-bg)',
      icon: 'var(--color-success-text)',
      border: 'var(--color-success-border)',
    },
    yellow: {
      bg: 'var(--color-warning-bg)',
      icon: 'var(--color-warning-text)',
      border: 'var(--color-warning-border)',
    },
    red: {
      bg: 'var(--color-accent-terra-light)',
      icon: 'var(--color-accent-terra-dark)',
      border: 'var(--color-accent-terra-border, #F4D3C7)',
    },
    terra: {
      bg: 'var(--color-accent-terra-light)',
      icon: 'var(--color-accent-terra-dark)',
      border: 'var(--color-accent-terra-border, #F4D3C7)',
    },
  };

  const activeColor = colorMap[color] || colorMap.purple;

  return (
    <div className="card stat-card animate-fade-in">
      <div className="stat-card-top">
        <span className="stat-title">{title}</span>
        <div
          className="stat-icon-wrapper"
          style={{ background: activeColor.bg, color: activeColor.icon, border: `1px solid ${activeColor.border}` }}
        >
          {Icon && <Icon size={18} />}
        </div>
      </div>

      <div className="stat-value">{value}</div>

      {footerText && (
        <div className="stat-footer">
          {trend && (
            <span
              style={{
                color: trend.isPositive ? 'var(--success-text)' : 'var(--danger-text)',
                fontWeight: 700,
              }}
            >
              {trend.text}
            </span>
          )}
          <span>{footerText}</span>
        </div>
      )}
    </div>
  );
}
