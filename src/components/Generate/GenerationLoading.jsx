import React from 'react';
import { Sparkles, Check, Brain, Cpu, FileSearch, Target } from 'lucide-react';

export function GenerationLoading({ currentStep = 1, statusMessage }) {
  const steps = [
    {
      num: 1,
      title: 'Analyze Job Requirements',
      desc: 'Extracting key technical responsibilities and core deliverables',
      icon: FileSearch,
    },
    {
      num: 2,
      title: 'Cross-Reference Candidate Profile',
      desc: 'Detecting claimed proficiencies, experience depth, and edge cases',
      icon: Target,
    },
    {
      num: 3,
      title: 'Synthesize Interview Prompts',
      desc: 'Crafting non-generic, high-signal questions across target competencies',
      icon: Brain,
    },
    {
      num: 4,
      title: 'Formulate Rubrics & Rationales',
      desc: 'Establishing look-for rubrics and tailored relevance explanations',
      icon: Cpu,
    },
  ];

  return (
    <div className="generation-loading-container animate-fade-in">
      <div className="ai-pulse-orb">
        <Sparkles size={32} />
      </div>

      <div className="loading-heading">InterviewIQ AI Engine Active</div>
      <div className="loading-subtext">
        {statusMessage || 'Analyzing requirements and synthesizing candidate-tailored questions...'}
      </div>

      <div className="stepper-progress-box">
        {steps.map((step) => {
          const isDone = currentStep > step.num;
          const isActive = currentStep === step.num;
          const stepClass = isDone ? 'done' : isActive ? 'active' : '';

          return (
            <div key={step.num} className={`step-item ${stepClass}`}>
              <div className="step-indicator-circle">
                {isDone ? <Check size={13} /> : step.num}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: 13.5 }}>{step.title}</span>
                <span style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>{step.desc}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Shimmer Placeholder Skeletons */}
      <div style={{ marginTop: 36, display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="shimmer-box" style={{ height: 90, width: '100%' }} />
        <div className="shimmer-box" style={{ height: 110, width: '100%' }} />
        <div className="shimmer-box" style={{ height: 80, width: '100%' }} />
      </div>
    </div>
  );
}
