import React, { useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import {
  Award,
  Printer,
  RotateCcw,
  ArrowLeft,
  CheckCircle2,
  FileQuestion,
  MessageSquare,
} from 'lucide-react';

export function Stage4CandidateScore({ onBack, onRestart }) {
  const { workflowData, addToast } = useApp();

  const candidateName =
    workflowData.candidateSummary?.candidateName ||
    workflowData.resumeFileName?.replace(/\.[^/.]+$/, '') ||
    'Candidate';

  const answeredQuestions = useMemo(() => {
    return workflowData.generatedQuestions || [];
  }, [workflowData.generatedQuestions]);

  // Overall fit score computed from the average of answer scores
  const overallFitScore = useMemo(() => {
    if (answeredQuestions.length === 0) {
      return workflowData.candidateSummary?.score || 88;
    }
    const sum = answeredQuestions.reduce((acc, q) => acc + (q.candidateScore || 88), 0);
    return Math.round(sum / answeredQuestions.length);
  }, [answeredQuestions, workflowData.candidateSummary]);

  const candidateSummary = {
    candidateName,
    score: overallFitScore,
    band: 'Senior Specialist',
  };

  const handlePrintPdf = () => {
    window.print();
    addToast({
      type: 'info',
      title: 'Print Dialog Opened',
      message: 'Select "Save as PDF" to save candidate scorecard.',
    });
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
      {/* Stage Header - Heading Only with Print and Start New Formulation */}
      <div
        className="card"
        style={{
          padding: '20px 24px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
              Stage 4: Candidate Scorecard & Assessment
            </h2>
          </div>

          <div className="no-print" style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <button className="btn-primary" onClick={handlePrintPdf} style={{ fontSize: 13 }}>
              <Printer size={14} /> Print / Save Scorecard
            </button>
            {onRestart && (
              <button
                type="button"
                className="btn-secondary"
                onClick={onRestart}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  fontSize: 12,
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--color-primary)',
                  background: '#FFFFFF',
                  border: '1px solid var(--color-border)',
                }}
                title="Reset and start fresh"
              >
                <RotateCcw size={13} /> Start New Formulation
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Candidate Scorecard Hero Card */}
      <div
        className="card"
        style={{
          padding: '24px 28px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          flexDirection: 'column',
          gap: 22,
        }}
      >
        {/* Candidate & Fit Score Summary Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div
              style={{
                width: 54,
                height: 54,
                borderRadius: 'var(--radius-full)',
                background: 'var(--color-primary-light)',
                border: '2px solid var(--color-accent-sage)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-primary)',
              }}
            >
              <Award size={28} />
            </div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-accent-sage-dark)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Candidate Fit Scorecard
              </div>
              <h3 style={{ fontSize: 19, fontWeight: 800, color: 'var(--color-primary)', margin: '2px 0 0' }}>
                {candidateSummary.candidateName} • {workflowData.jobTitle || 'Target Role'}
              </h3>
              <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', marginTop: 3 }}>
                Difficulty: <strong>{workflowData.difficulty || 'Medium'}</strong> • Band:{' '}
                <strong>{candidateSummary.band}</strong>
              </div>
            </div>
          </div>

          {/* Large Radial Fit Score Meter */}
          <div
            style={{
              padding: '12px 20px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                Overall Fit Score
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.1 }}>
                {candidateSummary.score}%
              </div>
              <span className="badge badge-success" style={{ fontSize: 10.5, marginTop: 4 }}>
                Recommended for Interview
              </span>
            </div>
          </div>
        </div>

        {/* Technical Competency Metric */}
        <div style={{ paddingTop: 16, borderTop: '1px solid var(--color-border)' }}>
          <div
            style={{
              padding: '14px 18px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              maxWidth: 420,
            }}
          >
            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600 }}>
              Technical Competency
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, margin: '6px 0 6px' }}>
              <span style={{ fontSize: 20, fontWeight: 800, color: 'var(--color-primary)' }}>
                {candidateSummary.score}%
              </span>
              <span style={{ fontSize: 11.5, color: 'var(--color-success-text)', fontWeight: 600 }}>
                Strong Mastery
              </span>
            </div>
            <div className="comp-bar-track" style={{ height: 6, background: 'var(--color-border)' }}>
              <div
                className="comp-bar-fill"
                style={{
                  width: `${candidateSummary.score}%`,
                  background: 'var(--color-primary)',
                  height: '100%',
                  borderRadius: 3,
                }}
              />
            </div>
          </div>
        </div>

        {/* Candidate Answered Questions and Scores Block */}
        <div style={{ paddingTop: 18, borderTop: '1px solid var(--color-border)', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
              Evaluated Candidate Answers & Individual Question Scores
            </h4>
            <span className="badge badge-forest">{answeredQuestions.length} Questions Evaluated</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {answeredQuestions.map((q, idx) => {
              const score = q.candidateScore || 88;

              return (
                <div
                  key={q.id || idx}
                  style={{
                    padding: '16px 20px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--color-surface-subtle)',
                    border: '1px solid var(--color-border)',
                    borderLeft: '4px solid var(--color-primary)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10,
                  }}
                >
                  {/* Question Header & Score Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="badge badge-forest" style={{ fontSize: 11.5 }}>
                        Question {idx + 1} • {q.competency || 'Technical Skills'}
                      </span>
                      <span className="badge badge-sage" style={{ fontSize: 11.5 }}>
                        Difficulty: {q.difficulty || 'Medium'}
                      </span>
                    </div>

                    {/* Individual Answer Score Badge */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span
                        className="badge"
                        style={{
                          fontSize: 12,
                          fontWeight: 800,
                          padding: '4px 10px',
                          background: score >= 85 ? 'var(--color-accent-sage)' : 'var(--color-surface-hover)',
                          color: 'var(--color-primary)',
                          border: '1px solid var(--color-border)',
                        }}
                      >
                        Score: {score}%
                      </span>
                    </div>
                  </div>

                  {/* Question Prompt */}
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-primary)', lineHeight: 1.45 }}>
                    {q.question}
                  </div>

                  {/* Answer Given by Candidate */}
                  <div
                    style={{
                      background: '#FFFFFF',
                      padding: '12px 16px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--color-border)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 4,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        color: 'var(--color-primary)',
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 5,
                      }}
                    >
                      <MessageSquare size={13} /> Answer Given by Candidate:
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--color-text-main)', lineHeight: 1.55 }}>
                      {q.candidateAnswer || 'No response recorded.'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom Navigation Controls */}
      <div
        className="card no-print"
        style={{
          padding: '16px 24px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 14,
        }}
      >
        <button
          type="button"
          className="btn-secondary"
          onClick={onBack}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}
        >
          <ArrowLeft size={15} /> Back to Question Generation
        </button>

        {onRestart && (
          <button
            type="button"
            className="btn-primary"
            onClick={onRestart}
            style={{
              background: 'var(--color-primary)',
              color: '#FFFFFF',
              padding: '11px 24px',
              fontSize: 13.5,
              fontWeight: 700,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <RotateCcw size={14} /> Start New Formulation
          </button>
        )}
      </div>
    </div>
  );
}
