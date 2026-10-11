import React, { useState, useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { evaluateCandidateAnswer, getExpectedAnswer } from '../../utils/answerEvaluation';
import {
  ArrowLeft,
  ChevronRight,
  ChevronLeft,
  RotateCcw,
  Check,
  MessageSquare,
  FileText,
  Sparkles,
} from 'lucide-react';

export function Stage3Questions({ onBack, onProceedToScore, onRestart }) {
  const {
    workflowData,
    questions: globalQuestions,
    updateWorkflowData,
    addToast,
  } = useApp();

  const questions = useMemo(() => {
    return workflowData.generatedQuestions && workflowData.generatedQuestions.length > 0
      ? workflowData.generatedQuestions
      : globalQuestions;
  }, [workflowData.generatedQuestions, globalQuestions]);

  const candidateName =
    workflowData.candidateSummary?.candidateName ||
    workflowData.resumeFileName?.replace(/\.[^/.]+$/, '') ||
    'Candidate';

  // Question index selection (Question 1, Question 2, etc.)
  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);

  // Candidate answers state initialized empty (no pre-filled answers)
  const [candidateAnswers, setCandidateAnswers] = useState(() => {
    const initial = {};
    questions.forEach((q) => {
      initial[q.id] = q.candidateAnswer || workflowData.candidateAnswers?.[q.id] || '';
    });
    return initial;
  });

  const total = questions.length;
  const answeredCount = questions.filter((q) => (candidateAnswers[q.id] || '').trim().length > 0).length;

  const currentQuestion = questions[activeQuestionIndex] || questions[0];

  const handleAnswerChange = (qId, value) => {
    setCandidateAnswers((prev) => ({
      ...prev,
      [qId]: value,
    }));
  };

  // Submit, evaluate against expected answers, allocate scores, and advance to Stage 4
  const handleProceed = () => {
    // Compare candidate answers against original expected answers
    const updatedQuestions = questions.map((q) => {
      const ans = (candidateAnswers[q.id] || '').trim();
      const evaluation = evaluateCandidateAnswer(ans, q);
      return {
        ...q,
        candidateAnswer: ans,
        candidateScore: evaluation.score,
        expectedAnswer: evaluation.expectedAnswer,
        evaluationFeedback: evaluation.feedback,
        matchPercentage: evaluation.matchPercentage,
        candidateName,
      };
    });

    // Calculate score from candidate answers
    const answeredList = updatedQuestions.filter((q) => (q.candidateAnswer || '').length > 0);
    const averageAnswerScore = answeredList.length > 0
      ? Math.round(answeredList.reduce((acc, q) => acc + q.candidateScore, 0) / answeredList.length)
      : 70;

    const resumeScore = workflowData.candidateSummary?.comparison?.score || workflowData.candidateSummary?.score || 85;
    const overallFitScore = Math.round(0.30 * resumeScore + 0.70 * averageAnswerScore);

    updateWorkflowData({
      generatedQuestions: updatedQuestions,
      candidateAnswers,
      candidateSummary: {
        ...(workflowData.candidateSummary || {}),
        candidateName,
        score: overallFitScore,
        interviewScore: averageAnswerScore,
      },
    });

    addToast({
      type: 'success',
      title: 'Answers Evaluated',
      message: `Evaluated ${answeredCount} of ${total} answers against benchmark criteria. Advancing to Scorecard.`,
    });

    if (onProceedToScore) {
      onProceedToScore();
    }
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
      {/* Stage Header - Heading Only with Corner Controls */}
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
              Stage 3: Question Formulation & Candidate Response
            </h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span className="badge badge-forest" style={{ fontSize: 11, padding: '3px 7px' }}>{total} Questions</span>
            <span className="badge badge-success" style={{ fontSize: 11, padding: '3px 7px' }}>{answeredCount} Answered</span>
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
          </div>
        </div>
      </div>

      {/* Horizontal Question Selector Tabs (Question 1, Question 2, Question 3...) */}
      <div
        className="card"
        style={{
          padding: '6px 12px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          overflowX: 'auto',
          flexShrink: 0,
        }}
      >
        {questions.map((q, idx) => {
          const isActive = idx === activeQuestionIndex;
          const hasAnswer = (candidateAnswers[q.id] || '').trim().length > 0;

          return (
            <button
              key={q.id || idx}
              type="button"
              onClick={() => setActiveQuestionIndex(idx)}
              style={{
                padding: '5px 12px',
                borderRadius: 'var(--radius-sm)',
                border: isActive
                  ? '1.5px solid var(--color-primary)'
                  : hasAnswer
                  ? '1px solid var(--color-accent-sage)'
                  : '1px solid var(--color-border)',
                background: isActive
                  ? 'var(--color-primary)'
                  : hasAnswer
                  ? 'var(--color-primary-light)'
                  : 'var(--color-surface-subtle)',
                color: isActive
                  ? '#FFFFFF'
                  : hasAnswer
                  ? 'var(--color-primary)'
                  : 'var(--color-text-main)',
                fontSize: 12,
                fontWeight: isActive ? 700 : 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                whiteSpace: 'nowrap',
                transition: 'all 120ms ease',
              }}
            >
              {hasAnswer && (
                <Check
                  size={11}
                  style={{
                    color: isActive ? '#FFFFFF' : 'var(--color-success-text)',
                    strokeWidth: 3,
                  }}
                />
              )}
              Question {idx + 1}
            </button>
          );
        })}
      </div>

      {/* Active Question Card (With Description & Candidate Answer Input - No Expected Answer) */}
      {currentQuestion && (
        <div
          className="card animate-fade-in"
          style={{
            padding: '12px 16px',
            background: '#FFFFFF',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            flex: 1,
            minHeight: 0,
            justifyContent: 'space-between',
            overflow: 'hidden',
          }}
        >
          {/* Header Badges */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className="badge badge-forest" style={{ fontSize: 11 }}>
                Question {activeQuestionIndex + 1} • {currentQuestion.competency || 'Technical Skills'}
              </span>
              <span className="badge badge-sage" style={{ fontSize: 11 }}>
                Difficulty: {currentQuestion.difficulty || 'Medium'}
              </span>
            </div>

            {(candidateAnswers[currentQuestion.id] || '').trim().length > 0 && (
              <span className="badge badge-success" style={{ fontSize: 11 }}>
                ✓ Answer Recorded
              </span>
            )}
          </div>

          {/* Main Question Text */}
          <div
            style={{
              fontSize: 14.5,
              fontWeight: 700,
              color: 'var(--color-primary)',
              lineHeight: 1.35,
            }}
          >
            {currentQuestion.question}
          </div>

          {/* Question Description / Context (No Expected Answer) */}
          <div
            style={{
              background: 'var(--color-surface-subtle)',
              padding: '8px 12px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              borderLeft: '3.5px solid var(--color-primary)',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
            }}
          >
            <div
              style={{
                fontSize: 10.5,
                fontWeight: 700,
                color: 'var(--color-primary)',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Question Description & Context:
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text-main)', lineHeight: 1.4 }}>
              {currentQuestion.whyRelevant ||
                `Evaluate the candidate's practical execution, engineering depth, and problem-solving methodology regarding ${currentQuestion.skillName || currentQuestion.competency}.`}
            </div>
          </div>

          {/* Candidate Answer Textarea Input */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minHeight: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <label
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: 'var(--color-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5,
                }}
              >
                <MessageSquare size={14} /> Candidate's Answer:
              </label>
              <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                {(candidateAnswers[currentQuestion.id] || '').length} characters
              </span>
            </div>

            <textarea
              rows={3}
              className="form-input"
              style={{
                width: '100%',
                flex: 1,
                minHeight: '70px',
                maxHeight: '110px',
                padding: '8px 10px',
                fontSize: 12.5,
                lineHeight: 1.45,
                resize: 'none',
                background: '#FFFFFF',
                border: '1.5px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
              }}
              placeholder="Enter candidate's answer to this question..."
              value={candidateAnswers[currentQuestion.id] || ''}
              onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
            />
          </div>

          {/* Question Stepper Navigation (Previous / Next Question) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: 6,
              borderTop: '1px solid var(--color-border)',
            }}
          >
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setActiveQuestionIndex((prev) => Math.max(0, prev - 1))}
              disabled={activeQuestionIndex === 0}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11.5, padding: '4px 10px' }}
            >
              <ChevronLeft size={13} /> Previous Question
            </button>

            <span style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              Question {activeQuestionIndex + 1} of {questions.length}
            </span>

            <button
              type="button"
              className="btn-secondary"
              onClick={() =>
                setActiveQuestionIndex((prev) => Math.min(questions.length - 1, prev + 1))
              }
              disabled={activeQuestionIndex === questions.length - 1}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11.5, padding: '4px 10px' }}
            >
              Next Question <ChevronRight size={13} />
            </button>
          </div>
        </div>
      )}

      {/* Bottom Action Controls */}
      <div
        className="card"
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
        <button
          type="button"
          className="btn-secondary"
          onClick={onBack}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '5px 12px' }}
        >
          <ArrowLeft size={14} /> Back to Skill Matching
        </button>

        <button
          type="button"
          className="btn-primary"
          onClick={handleProceed}
          style={{
            background: 'var(--color-primary)',
            color: '#FFFFFF',
            padding: '8px 20px',
            fontSize: 13,
            fontWeight: 700,
            borderRadius: 'var(--radius-sm)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          Proceed to Candidate Scorecard
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  );
}
