import React, { useMemo } from 'react';
import { CheckCircle2, AlertCircle, ShieldCheck, ArrowRight } from 'lucide-react';

export const CORE_COMPETENCIES = [
  { id: 'Technical Skills', label: 'Technical Skills', desc: 'Coding, frameworks, syntax, internals' },
  { id: 'Problem Solving', label: 'Problem Solving', desc: 'Algorithms, performance, incident triage' },
  { id: 'Behavioural Skills', label: 'Behavioural Skills', desc: 'Collaboration, culture fit, ownership' },
  { id: 'System Design', label: 'System Design', desc: 'Distributed systems, scaling, resilience' },
];

export function CoverageMeter({ questions, onNavigateToLibrary }) {
  // Compute coverage based on accepted questions
  const analysis = useMemo(() => {
    const acceptedQuestions = questions.filter((q) => q.status === 'accepted');

    const counts = {
      'Technical Skills': 0,
      'Problem Solving': 0,
      'Behavioural Skills': 0,
      'System Design': 0,
    };

    acceptedQuestions.forEach((q) => {
      const comp = q.competency || '';
      if (comp.includes('Technical') || comp.includes('Coding')) {
        counts['Technical Skills']++;
      } else if (comp.includes('Problem') || comp.includes('Algorithm')) {
        counts['Problem Solving']++;
      } else if (comp.includes('Behavioral') || comp.includes('Behavioural') || comp.includes('Leadership')) {
        counts['Behavioural Skills']++;
      } else if (comp.includes('Design') || comp.includes('Architecture') || comp.includes('Resilience')) {
        counts['System Design']++;
      } else {
        // Fallback mapping
        counts['Technical Skills']++;
      }
    });

    const coveredCount = CORE_COMPETENCIES.filter((c) => counts[c.id] > 0).length;
    const totalCore = CORE_COMPETENCIES.length;
    const coveragePercentage = Math.round((coveredCount / totalCore) * 100);

    return {
      acceptedTotal: acceptedQuestions.length,
      counts,
      coveredCount,
      totalCore,
      coveragePercentage,
    };
  }, [questions]);

  const { coveragePercentage, counts, coveredCount, totalCore, acceptedTotal } = analysis;

  const getStatusDetails = (pct) => {
    if (pct === 100) {
      return {
        label: 'Optimal Coverage',
        color: 'var(--success-text)',
        badgeClass: 'badge-success',
        message: 'All 4 critical interview dimensions are covered with approved questions.',
      };
    }
    if (pct >= 75) {
      return {
        label: 'Strong Coverage',
        color: 'var(--color-primary)',
        badgeClass: 'badge-forest',
        message: '3 of 4 core competency domains covered. Add 1 more domain for a balanced kit.',
      };
    }
    if (pct >= 50) {
      return {
        label: 'Moderate Coverage',
        color: '#b45309',
        badgeClass: 'badge-warning',
        message: '2 core competencies covered. Candidate will be tested on partial dimensions.',
      };
    }
    if (pct > 0) {
      return {
        label: 'Partial Coverage',
        color: 'var(--danger-text)',
        badgeClass: 'badge-danger',
        message: 'Only 1 core competency represented in accepted questions.',
      };
    }
    return {
      label: 'Zero Coverage',
      color: 'var(--text-muted)',
      badgeClass: 'badge-warning',
      message: 'No questions have been accepted yet. Review pending questions to build your kit.',
    };
  };

  const status = getStatusDetails(coveragePercentage);

  return (
    <div className="card coverage-meter-card" style={{ padding: '22px 24px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 18,
          flexWrap: 'wrap',
          gap: 8,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ShieldCheck size={18} style={{ color: 'var(--primary)' }} />
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Competency Coverage Overview
            </h3>
          </div>
          <p style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 2 }}>
            Real-time readiness index calculated from your {acceptedTotal} approved questions
          </p>
        </div>

        <span className={`badge ${status.badgeClass}`}>{status.label}</span>
      </div>

      {/* Visual Percentage Progress Meter */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 20,
          padding: '16px 20px',
          background: 'var(--color-primary-light)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-accent-sage)',
          marginBottom: 20,
        }}
      >
        {/* Radial Meter representation */}
        <div style={{ position: 'relative', width: 74, height: 74, flexShrink: 0 }}>
          <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="#D8E4D5"
              strokeWidth="3.6"
            />
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="url(#forestGrad)"
              strokeDasharray={`${coveragePercentage}, 100`}
              strokeLinecap="round"
              strokeWidth="3.6"
              style={{ transition: 'stroke-dasharray 0.5s ease' }}
            />
            <defs>
              <linearGradient id="forestGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#182D27" />
                <stop offset="100%" stopColor="#2F4D38" />
              </linearGradient>
            </defs>
          </svg>
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontWeight: 800,
              fontSize: 16,
              color: 'var(--color-primary)',
            }}
          >
            {coveragePercentage}%
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-main)' }}>
              {coveredCount} of {totalCore} Core Competency Domains Covered
            </span>
            <span style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--primary)' }}>
              {coveragePercentage}% Ready
            </span>
          </div>

          <div
            style={{
              height: 7,
              background: '#e9e4f7',
              borderRadius: 999,
              overflow: 'hidden',
              marginBottom: 8,
            }}
          >
            <div
              style={{
                width: `${coveragePercentage}%`,
                height: '100%',
                background: 'var(--color-primary)',
                transition: 'width 0.4s ease',
              }}
            />
          </div>

          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            {status.message}
          </div>
        </div>
      </div>

      {/* Grid of Competency Status */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 12,
        }}
      >
        {CORE_COMPETENCIES.map((comp) => {
          const count = counts[comp.id] || 0;
          const isCovered = count > 0;

          return (
            <div
              key={comp.id}
              style={{
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                background: isCovered ? '#ffffff' : 'var(--color-surface-subtle)',
                border: `1px solid ${isCovered ? 'var(--color-accent-sage)' : 'var(--color-border)'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {isCovered ? (
                  <CheckCircle2 size={16} style={{ color: 'var(--success)' }} />
                ) : (
                  <AlertCircle size={16} style={{ color: '#d97706' }} />
                )}
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-main)' }}>
                    {comp.label}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {comp.desc}
                  </div>
                </div>
              </div>

              <span
                className={`badge ${isCovered ? 'badge-success' : 'badge-warning'}`}
                style={{ fontSize: 11 }}
              >
                {count > 0 ? `${count} Accepted` : '0 Accepted'}
              </span>
            </div>
          );
        })}
      </div>

      {onNavigateToLibrary && coveragePercentage < 100 && (
        <div style={{ marginTop: 14, textAlign: 'right' }}>
          <button
            className="btn-ghost"
            style={{ fontSize: 12.5, color: 'var(--primary)' }}
            onClick={onNavigateToLibrary}
          >
            Review and Accept Questions in Library <ArrowRight size={13} />
          </button>
        </div>
      )}
    </div>
  );
}
