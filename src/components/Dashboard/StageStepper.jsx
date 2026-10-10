import React from 'react';
import { Check, Circle } from 'lucide-react';

export function StageStepper({ currentStage, maxReachedStage = 1, onSelectStage }) {
  const stages = [
    { number: 1, title: 'Role & Resume', desc: 'Job text & resume file' },
    { number: 2, title: 'Skill Matching', desc: 'Job & candidate priorities' },
    { number: 3, title: 'Question Generation', desc: 'Synthesized interview plan' },
    { number: 4, title: 'Candidate Score', desc: 'Scorecard & final review kit' },
  ];

  return (
    <div
      className="card no-print animate-fade-in"
      style={{
        padding: '14px 20px',
        background: '#FFFFFF',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 12,
        }}
      >
        {stages.map((st) => {
          const isCurrent = currentStage === st.number;
          const isCompleted = currentStage > st.number;
          const isAccessible = st.number <= maxReachedStage;

          return (
            <button
              key={st.number}
              type="button"
              disabled={!isAccessible}
              onClick={() => isAccessible && onSelectStage && onSelectStage(st.number)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                border: isCurrent
                  ? '1.5px solid var(--color-primary)'
                  : isCompleted
                  ? '1px solid var(--color-accent-sage)'
                  : '1px solid var(--color-border)',
                background: isCurrent
                  ? 'var(--color-primary-light)'
                  : isCompleted
                  ? 'var(--color-accent-sage-light)'
                  : 'transparent',
                cursor: isAccessible ? 'pointer' : 'not-allowed',
                opacity: isAccessible ? 1 : 0.45,
                textAlign: 'left',
                transition: 'all 140ms ease',
              }}
            >
              {/* Step Icon / Number */}
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 'var(--radius-full)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 12,
                  fontWeight: 700,
                  flexShrink: 0,
                  background: isCurrent
                    ? 'var(--color-primary)'
                    : isCompleted
                    ? 'var(--color-accent-sage-dark)'
                    : 'var(--color-surface-subtle)',
                  color: isCurrent || isCompleted ? '#FFFFFF' : 'var(--color-text-secondary)',
                  border: isCompleted || isCurrent ? 'none' : '1px solid var(--color-border)',
                }}
              >
                {isCompleted ? <Check size={14} /> : st.number}
              </div>

              {/* Step Meta */}
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 12.5,
                    fontWeight: isCurrent ? 700 : 600,
                    color: isCurrent
                      ? 'var(--color-primary)'
                      : isCompleted
                      ? 'var(--color-text-main)'
                      : 'var(--color-text-secondary)',
                    lineHeight: 1.25,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  Stage {st.number}: {st.title}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--color-text-secondary)',
                    marginTop: 2,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {st.desc}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
