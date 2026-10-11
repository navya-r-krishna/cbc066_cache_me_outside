import React, { useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { getExpectedAnswer } from '../../services/answerEvaluation';
import {
  Award,
  Printer,
  RotateCcw,
  ArrowLeft,
  MessageSquare,
  CheckCircle2,
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
              <span
                className={`badge ${
                  workflowData.candidateSummary?.comparison?.candidate_band?.includes('strong')
                    ? 'badge-success'
                    : 'badge-forest'
                }`}
                style={{ fontSize: 9.5, marginTop: 2, textTransform: 'uppercase' }}
              >
                {workflowData.candidateSummary?.band || 'Provisional Match'}
              </span>
            </div>
          </div>
        </div>

        {/* ===================================================================== */}
        {/* ANALYSIS A: FACTOR SCORES & CANDIDATE BREAKDOWN (Banavi's Backend) */}
        {/* ===================================================================== */}
        {workflowData.candidateSummary?.comparison && (
          <div
            style={{
              padding: '12px 14px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
              flexShrink: 0,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 6 }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--color-primary)' }}>
                Analysis A Evaluation Breakdown (Weighted Factors & Candidate Evidence)
              </div>
              {workflowData.candidateSummary.comparison.provisional && (
                <span className="badge badge-sage" style={{ fontSize: 10 }}>
                  Provisional Scoring Active
                </span>
              )}
            </div>

            {/* Factor Scores Grid (Skills 40%, Experience 30%, Role Relevance 20%, Academics 10%) */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: 8,
              }}
            >
              {[
                {
                  label: 'Skills Fit (40%)',
                  val: workflowData.candidateSummary.comparison.factor_scores?.skills,
                  suffix: '%',
                },
                {
                  label: 'Experience (30%)',
                  val: workflowData.candidateSummary.comparison.factor_scores?.experience,
                  suffix: '%',
                },
                {
                  label: 'Role Relevance (20%)',
                  val: workflowData.candidateSummary.comparison.factor_scores?.role_relevance,
                  suffix: '%',
                },
                {
                  label: 'Academics (10%)',
                  val: workflowData.candidateSummary.comparison.factor_scores?.academics,
                  suffix: workflowData.candidateSummary.comparison.factor_scores?.academics != null ? '%' : 'N/A',
                },
              ].map((f, i) => (
                <div
                  key={i}
                  style={{
                    background: '#FFFFFF',
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--color-border)',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: 10, color: 'var(--color-text-secondary)', fontWeight: 600 }}>{f.label}</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: 'var(--color-primary)', marginTop: 2 }}>
                    {f.val != null ? `${Math.round(f.val)}${f.suffix}` : 'Unassessed'}
                  </div>
                </div>
              ))}
            </div>

            {/* Strengths & Skill Gaps split */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
              {/* Strengths */}
              <div
                style={{
                  background: '#FFFFFF',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-primary)', marginBottom: 4 }}>
                  Identified Candidate Strengths ({workflowData.candidateSummary.comparison.strengths?.length || 0})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {(workflowData.candidateSummary.comparison.strengths || []).map((str, idx) => (
                    <span key={idx} className="badge badge-forest" style={{ fontSize: 10 }}>
                      ✓ {str}
                    </span>
                  ))}
                </div>
              </div>

              {/* Skill Gaps */}
              <div
                style={{
                  background: '#FFFFFF',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-primary)', marginBottom: 4 }}>
                  Skill Gaps & Target Areas ({workflowData.candidateSummary.comparison.skill_gaps?.length || 0})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {(workflowData.candidateSummary.comparison.skill_gaps || []).map((gap, idx) => (
                    <span key={idx} className="badge badge-sage" style={{ fontSize: 10 }}>
                      ! {gap.name || gap} {gap.competency ? `(${gap.competency})` : ''}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Experience Breakdown & Disclaimers */}
            {workflowData.candidateSummary.comparison.experience_breakdown && (
              <div style={{ fontSize: 10.5, color: 'var(--color-text-secondary)', display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                <span>
                  <strong>Professional Experience:</strong> {workflowData.candidateSummary.comparison.experience_breakdown.professional_months || 0} mos
                </span>
                <span>
                  <strong>Relevant Internships:</strong> {workflowData.candidateSummary.comparison.experience_breakdown.relevant_internship_months || 0} mos (50% credit factor)
                </span>
                <span>
                  <strong>Equivalent Total:</strong> {workflowData.candidateSummary.comparison.experience_breakdown.equivalent_experience_months || 0} mos
                </span>
              </div>
            )}
          </div>
        )}




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

                  {/* Expected Benchmark Answer */}
                  <div
                    style={{
                      background: '#F0FDF4',
                      padding: '9px 12px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid #BBF7D0',
                      borderLeft: '3.5px solid #16A34A',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 3,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 10.5,
                        fontWeight: 700,
                        color: '#15803D',
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                    >
                      <CheckCircle2 size={12} /> Expected Answer / Benchmark Criteria:
                    </div>
                    <div style={{ fontSize: 12, color: '#166534', lineHeight: 1.45 }}>
                      {q.expectedAnswer || getExpectedAnswer(q)}
                    </div>
                  </div>

                  {/* Answer Given by Candidate */}
                  <div
                    style={{
                      background: '#FFFFFF',
                      padding: '9px 12px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--color-border)',
                      borderLeft: '3.5px solid var(--color-primary)',
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
                        justifyContent: 'space-between',
                      }}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <MessageSquare size={12} /> Answer Given by Candidate:
                      </span>
                      {q.evaluationFeedback && (
                        <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'none' }}>
                          {q.evaluationFeedback}
                        </span>
                      )}
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: (q.candidateAnswer && q.candidateAnswer.trim()) ? 'var(--color-text-main)' : 'var(--color-text-secondary)',
                        lineHeight: 1.45,
                        fontStyle: (q.candidateAnswer && q.candidateAnswer.trim()) ? 'normal' : 'italic',
                      }}
                    >
                      {(q.candidateAnswer && q.candidateAnswer.trim()) || 'No response recorded for this question.'}
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
