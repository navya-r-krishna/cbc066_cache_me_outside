import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { WorkflowStepper } from '../Workflow/WorkflowStepper';
import { InputStep } from '../Workflow/InputStep';
import { SkillsStep } from '../Workflow/SkillsStep';
import { PlanReviewStep } from '../Workflow/PlanReviewStep';
import { FinalKitStep } from '../Workflow/FinalKitStep';
import { Sparkles, Info } from 'lucide-react';

export function GenerateView() {
  const {
    workflowStep,
    setWorkflowStep,
    resetWorkflow,
    workflowData,
  } = useApp();

  // Track furthest reached step so user can navigate back and forth using the stepper
  const [maxReachedStep, setMaxReachedStep] = useState(workflowStep);

  const handleStepTransition = (newStep) => {
    setWorkflowStep(newStep);
    const stepOrder = ['input', 'skills', 'plan', 'final'];
    if (stepOrder.indexOf(newStep) > stepOrder.indexOf(maxReachedStep)) {
      setMaxReachedStep(newStep);
    }
  };

  const renderActiveStep = () => {
    switch (workflowStep) {
      case 'input':
        return <InputStep onNext={() => handleStepTransition('skills')} />;
      case 'skills':
        return (
          <SkillsStep
            onBack={() => handleStepTransition('input')}
            onNext={() => handleStepTransition('plan')}
          />
        );
      case 'plan':
        return (
          <PlanReviewStep
            onBack={() => handleStepTransition('skills')}
            onNext={() => handleStepTransition('final')}
          />
        );
      case 'final':
        return (
          <FinalKitStep
            onBack={() => handleStepTransition('plan')}
            onRestart={() => {
              resetWorkflow();
              setMaxReachedStep('input');
            }}
          />
        );
      default:
        return <InputStep onNext={() => handleStepTransition('skills')} />;
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Editorial Notice Banner: Clearly Labeled Mock / Demo Engine */}
      <div
        className="no-print"
        style={{
          background: 'var(--color-primary-light)',
          border: '1px solid var(--color-accent-sage)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="badge badge-forest" style={{ fontWeight: 800, letterSpacing: 0.5 }}>
            DEMO GENERATOR MODE
          </span>
          <span style={{ fontSize: 13, color: 'var(--color-primary)', fontWeight: 500 }}>
            InterviewIQ synthesizes questions locally with calibrated weights. No external API keys are required.
          </span>
        </div>

        <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
          Workflow: Input → Skills → Interview Plan → Final Kit
        </span>
      </div>

      {/* 4-Stage Stepper Bar */}
      <div className="no-print">
        <WorkflowStepper
          currentStep={workflowStep}
          onSelectStep={(targetStep) => handleStepTransition(targetStep)}
          maxReachedStep={maxReachedStep}
        />
      </div>

      {/* Active Stage Content */}
      {renderActiveStep()}
    </div>
  );
}
