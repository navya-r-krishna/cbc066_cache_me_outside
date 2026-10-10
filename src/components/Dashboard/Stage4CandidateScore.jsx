import React, { useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import {
  Award,
  Printer,
  RotateCcw,
  ArrowLeft,
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
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        height: '100%',
        maxHeight: '100%',
        overflow: 'hidden',
        justifyContent: 'space-between',
      }}
    >
      {/* Stage Header - Heading Only with Print and Start New Formulation */}
      <div
        className="card"
        style={{
          padding: '8px 14px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
              Stage 4: Candidate Scorecard & Assessment
            </h2>
          </div>

          <div className="no-print" style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            {onRestart && (
              <button
                type="button"
                className="btn-secondary"
                onClick={onRestart}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 5,
                  fontSize: 11.5,
                  padding: '4px 9px',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--color-primary)',
                  background: '#FFFFFF',
                  border: '1px solid var(--color-border)',
                }}
                title="Reset and start fresh"
              >
                <RotateCcw size={12} /> Start New Formulation
              </button>
            )}
            <button className="btn-primary" onClick={handlePrintPdf} style={{ fontSize: 12, padding: '5px 12px' }}>
              <Printer size={13} /> Print / Save Scorecard
            </button>
          </div>
        </div>
      </div>

      {/* Candidate Scorecard Hero Card */}
      <div
        className="card"
        style={{
          padding: '12px 16px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          flex: 1,
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        {/* Candidate & Fit Score Summary Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 'var(--radius-full)',
                background: 'var(--color-primary-light)',
                border: '1.5px solid var(--color-accent-sage)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-primary)',
              }}
            >
              <Award size={20} />
            </div>
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--color-accent-sage-dark)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Candidate Fit Scorecard
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 800, color: 'var(--color-primary)', margin: '1px 0 0' }}>
                {candidateSummary.candidateName} • {workflowData.jobTitle || 'Target Role'}
              </h3>
              <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                Difficulty: <strong>{workflowData.difficulty || 'Medium'}</strong> • Band:{' '}
                <strong>{candidateSummary.band}</strong>
              </div>
            </div>
          </div>

          {/* Large Radial Fit Score Meter */}
          <div
            style={{
              padding: '8px 14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                Overall Fit Score
              </div>
              <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1.1 }}>
                {candidateSummary.score}%
              </div>
              <span className="badge badge-success" style={{ fontSize: 9.5, marginTop: 2 }}>
                Recommended for Interview
              </span>
            </div>
          </div>
        </div>



        {/* Candidate Answered Questions and Scores Block */}
        <div style={{ paddingTop: 8, borderTop: '1px solid var(--color-border)', display: 'flex', flexDirection: 'column', gap: 8, flex: 1, minHeight: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
            <h4 style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
              Evaluated Candidate Answers & Individual Question Scores
            </h4>
            <span className="badge badge-forest" style={{ fontSize: 10.5 }}>{answeredQuestions.length} Questions Evaluated</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, minHeight: 0, overflowY: 'auto', paddingRight: 4 }}>
            {answeredQuestions.map((q, idx) => {
              const score = q.candidateScore || 88;

              return (
                <div
                  key={q.id || idx}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--color-surface-subtle)',
                    border: '1px solid var(--color-border)',
                    borderLeft: '3.5px solid var(--color-primary)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                  }}
                >
                  {/* Question Header & Score Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span className="badge badge-forest" style={{ fontSize: 11 }}>
                        Question {idx + 1} • {q.competency || 'Technical Skills'}
                      </span>
                      <span className="badge badge-sage" style={{ fontSize: 11 }}>
                        Difficulty: {q.difficulty || 'Medium'}
                      </span>
                    </div>

                    {/* Individual Answer Score Badge */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span
                        className="badge"
                        style={{
                          fontSize: 11,
                          fontWeight: 800,
                          padding: '3px 8px',
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
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-primary)', lineHeight: 1.35 }}>
                    {q.question}
                  </div>

                  {/* Answer Given by Candidate */}
                  <div
                    style={{
                      background: '#FFFFFF',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--color-border)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 3,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 10.5,
                        fontWeight: 700,
                        color: 'var(--color-primary)',
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                    >
                      <MessageSquare size={12} /> Answer Given by Candidate:
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-main)', lineHeight: 1.45 }}>
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
          padding: '8px 16px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 10,
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {onRestart && (
            <button
              type="button"
              className="btn-secondary"
              onClick={onRestart}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                fontSize: 12,
                padding: '5px 12px',
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
          <button
            type="button"
            className="btn-secondary"
            onClick={onBack}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '5px 12px' }}
          >
            <ArrowLeft size={14} /> Back to Question Generation
          </button>
        </div>
      </div>
    </div>
  );
}
