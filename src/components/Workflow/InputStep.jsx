import React from 'react';
import { AnalysisForm } from '../Common/AnalysisForm';

export function InputStep({ onNext }) {
  return (
    <div className="animate-fade-in">
      <AnalysisForm
        title="Stage 1: Job Description & Candidate Resume"
        subtitle="Provide the role description and candidate background. InterviewIQ will parse competency requirements, evaluate candidate fit, and formulate targeted evaluation rubrics."
        onAnalyzeSuccess={onNext}
      />
    </div>
  );
}
