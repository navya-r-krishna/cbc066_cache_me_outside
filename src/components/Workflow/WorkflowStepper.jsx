import React from 'react';
import { Check, FileText, Cpu, ListChecks, Award } from 'lucide-react';

export function WorkflowStepper({ currentStep, onSelectStep, maxReachedStep }) {
  const steps = [
    { id: 'input', number: 1, label: 'Role & Resume', icon: FileText },
    { id: 'skills', number: 2, label: 'Skills & Calibration', icon: Cpu },
    { id: 'plan', number: 3, label: 'Interview Plan Review', icon: ListChecks },
    { id: 'final', number: 4, label: 'Final Interview Kit', icon: Award },
  ];

  const stepOrder = ['input', 'skills', 'plan', 'final'];
  const currentIndex = stepOrder.indexOf(currentStep);

  return (
    <div className="workflow-stepper-container" style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
      padding: '14px 20px',
      marginBottom: '20px',
      boxShadow: 'var(--shadow-xs)'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isCurrent = currentStep === step.id;
          const isPassed = currentIndex > idx;
          const isAccessible = onSelectStep && (idx <= (stepOrder.indexOf(maxReachedStep || currentStep)));

          return (
            <React.Fragment key={step.id}>
              <div
                onClick={() => isAccessible && onSelectStep(step.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  cursor: isAccessible ? 'pointer' : 'default',
                  opacity: isAccessible || isCurrent ? 1 : 0.6,
                  transition: 'all var(--transition-fast)'
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: 'var(--radius-full)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '13px',
                    fontWeight: 700,
                    background: isCurrent
                      ? 'var(--color-primary)'
                      : isPassed
                      ? 'var(--color-accent-sage)'
                      : 'var(--color-surface-subtle)',
                    color: isCurrent
                      ? '#FFFFFF'
                      : isPassed
                      ? 'var(--color-primary)'
                      : 'var(--color-text-secondary)',
                    border: isCurrent
                      ? '1px solid var(--color-primary)'
                      : isPassed
                      ? '1px solid #B8CBB5'
                      : '1px solid var(--color-border)'
                  }}
                >
                  {isPassed ? <Check size={16} strokeWidth={2.5} /> : <Icon size={15} />}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{
                    fontSize: '10.5px',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    color: isCurrent ? 'var(--color-accent-terra)' : 'var(--color-text-secondary)'
                  }}>
                    Stage {step.number}
                  </span>
                  <span style={{
                    fontSize: '13.5px',
                    fontWeight: isCurrent ? 700 : 500,
                    color: isCurrent ? 'var(--color-primary)' : 'var(--color-text-main)'
                  }}>
                    {step.label}
                  </span>
                </div>
              </div>

              {idx < steps.length - 1 && (
                <div
                  style={{
                    flex: 1,
                    minWidth: '24px',
                    height: '2px',
                    background: isPassed ? 'var(--color-accent-sage)' : 'var(--color-border)',
                    margin: '0 8px'
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
