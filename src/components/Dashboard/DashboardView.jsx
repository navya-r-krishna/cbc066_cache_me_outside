import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { StageStepper } from './StageStepper';
import { Stage1RoleResume } from './Stage1RoleResume';
import { Stage2SkillMatching } from './Stage2SkillMatching';
import { Stage3Questions } from './Stage3Questions';
import { Stage4CandidateScore } from './Stage4CandidateScore';

export function DashboardView() {
  const { resetWorkflow } = useApp();

  // Workflow Stages: 1. Role & Resume -> 2. Skill Matching -> 3. Question Generation -> 4. Candidate Score
  const [currentStage, setCurrentStage] = useState(1);
  const [maxReachedStage, setMaxReachedStage] = useState(1);

  const handleStageTransition = (nextStage) => {
    setCurrentStage(nextStage);
    if (nextStage > maxReachedStage) {
      setMaxReachedStage(nextStage);
    }
  };

  const handleRestart = () => {
    resetWorkflow();
    setCurrentStage(1);
    setMaxReachedStage(1);
  };

  const renderActiveStage = () => {
    switch (currentStage) {
      case 1:
        return (
          <Stage1RoleResume
            onAnalyzeComplete={() => handleStageTransition(2)}
          />
        );
      case 2:
        return (
          <Stage2SkillMatching
            onBack={() => setCurrentStage(1)}
            onProceedToQuestions={() => handleStageTransition(3)}
            onRestart={handleRestart}
          />
        );
      case 3:
        return (
          <Stage3Questions
            onBack={() => setCurrentStage(2)}
            onProceedToScore={() => handleStageTransition(4)}
            onRestart={handleRestart}
          />
        );
      case 4:
        return (
          <Stage4CandidateScore
            onBack={() => setCurrentStage(3)}
            onRestart={handleRestart}
          />
        );
      default:
        return (
          <Stage1RoleResume
            onAnalyzeComplete={() => handleStageTransition(2)}
          />
        );
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* 4-Stage Progressive Workflow Stepper on the Dashboard */}
      <StageStepper
        currentStage={currentStage}
        maxReachedStage={maxReachedStage}
        onSelectStage={(st) => setCurrentStage(st)}
      />

      {/* Active Stage Content (Role & Resume -> Skill Matching -> Question Generation -> Candidate Score) */}
      {renderActiveStage()}
    </div>
  );
}
