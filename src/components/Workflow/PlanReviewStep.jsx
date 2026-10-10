import React, { useState, useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { QuestionCard } from '../Questions/QuestionCard';
import { Modal } from '../Common/Modal';
import {
  ListChecks,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowLeft,
  ChevronRight,
  Filter,
  Layers,
  Sparkles,
  Award,
  RefreshCw,
  Send,
} from 'lucide-react';

export function PlanReviewStep({ onBack, onNext }) {
  const {
    workflowData,
    acceptQuestion,
    rejectQuestion,
    regenerateQuestionItem,
    addToast,
  } = useApp();

  const questions = workflowData.generatedQuestions || [];

  // Filter state
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'accepted' | 'pending' | 'rejected'
  const [competencyFilter, setCompetencyFilter] = useState('all');

  // Hint Regenerate Modal State
  const [regenerateTargetId, setRegenerateTargetId] = useState(null);
  const [regenerateHint, setRegenerateHint] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Review progress calculation
  const total = questions.length;
  const acceptedCount = questions.filter((q) => q.status === 'accepted').length;
  const rejectedCount = questions.filter((q) => q.status === 'rejected').length;
  const pendingCount = questions.filter((q) => !q.status || q.status === 'pending').length;
  const reviewedCount = acceptedCount + rejectedCount;
  const progressPercent = total > 0 ? Math.round((reviewedCount / total) * 100) : 0;

  // Filtered questions
  const filteredQuestions = useMemo(() => {
    return questions.filter((q) => {
      if (statusFilter !== 'all') {
        const s = q.status || 'pending';
        if (s !== statusFilter) return false;
      }
      if (competencyFilter !== 'all' && q.competency !== competencyFilter) {
        return false;
      }
      return true;
    });
  }, [questions, statusFilter, competencyFilter]);

  // Unique competencies
  const availableCompetencies = useMemo(() => {
    const set = new Set();
    questions.forEach((q) => {
      if (q.competency) set.add(q.competency);
    });
    return Array.from(set);
  }, [questions]);

  const handleOpenRegenerateHint = (questionId) => {
    setRegenerateTargetId(questionId);
    setRegenerateHint('');
  };

  const handleConfirmRegenerate = async () => {
    if (!regenerateTargetId) return;
    setIsRegenerating(true);
    await regenerateQuestionItem(regenerateTargetId, regenerateHint);
    setIsRegenerating(false);
    setRegenerateTargetId(null);
    setRegenerateHint('');
  };

  const handleAcceptAllPending = () => {
    let count = 0;
    questions.forEach((q) => {
      if (!q.status || q.status === 'pending') {
        acceptQuestion(q.id);
        count++;
      }
    });
    if (count > 0) {
      addToast({
        type: 'success',
        title: 'All Questions Accepted',
        message: `Accepted ${count} pending questions for final kit.`,
      });
    }
  };

  const canProceed = acceptedCount > 0;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header Card */}
      <div className="card" style={{ padding: '20px 24px', background: '#FFFFFF' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-primary)', marginBottom: 4 }}>
              Stage 3: Interview Plan Review & Calibration
            </h2>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', maxWidth: 650 }}>
              Review each synthesized question, examine rubric criteria, and individually Accept, Reject, or
              Regenerate questions. Approved questions will form your final executive interview kit.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleAcceptAllPending}
              disabled={pendingCount === 0}
              style={{ fontSize: 12.5 }}
            >
              <CheckCircle2 size={14} style={{ color: 'var(--color-success-text)' }} />
              Accept All Pending ({pendingCount})
            </button>
          </div>
        </div>

        {/* Review Progress Tracker */}
        <div
          style={{
            marginTop: 18,
            padding: '14px 16px',
            background: 'var(--color-surface-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-primary)' }}>
                Review Progress: {reviewedCount} of {total} Questions
              </span>
              <span className="badge badge-sage" style={{ fontSize: 11 }}>
                {progressPercent}% Complete
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: 12, color: 'var(--color-success-text)', fontWeight: 600 }}>
                ✓ {acceptedCount} Accepted
              </span>
              <span style={{ fontSize: 12, color: 'var(--color-accent-terra)', fontWeight: 600 }}>
                ✕ {rejectedCount} Rejected
              </span>
              <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                • {pendingCount} Pending
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div style={{ height: 6, background: '#E2E1D9', borderRadius: 999, overflow: 'hidden', display: 'flex' }}>
            <div
              style={{
                width: `${total > 0 ? (acceptedCount / total) * 100 : 0}%`,
                background: 'var(--color-primary)',
                transition: 'width 0.3s ease',
              }}
              title={`Accepted: ${acceptedCount}`}
            />
            <div
              style={{
                width: `${total > 0 ? (rejectedCount / total) * 100 : 0}%`,
                background: 'var(--color-accent-terra)',
                transition: 'width 0.3s ease',
              }}
              title={`Rejected: ${rejectedCount}`}
            />
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div
        className="card"
        style={{
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Filter size={14} style={{ color: 'var(--color-text-secondary)' }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)' }}>Status:</span>
            <div className="pill-radio-group">
              {[
                { val: 'all', label: `All (${total})` },
                { val: 'accepted', label: `Accepted (${acceptedCount})` },
                { val: 'pending', label: `Pending (${pendingCount})` },
                { val: 'rejected', label: `Rejected (${rejectedCount})` },
              ].map((s) => (
                <button
                  key={s.val}
                  type="button"
                  className={`pill-radio-btn ${statusFilter === s.val ? 'selected' : ''}`}
                  onClick={() => setStatusFilter(s.val)}
                  style={{ padding: '4px 9px', fontSize: 11.5 }}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Competency Filter */}
          {availableCompetencies.length > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Layers size={14} style={{ color: 'var(--color-text-secondary)' }} />
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)' }}>Domain:</span>
              <select
                className="form-select"
                style={{ padding: '4px 8px', fontSize: 12, width: 'auto' }}
                value={competencyFilter}
                onChange={(e) => setCompetencyFilter(e.target.value)}
              >
                <option value="all">All Domains</option>
                {availableCompetencies.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
          Showing {filteredQuestions.length} of {total} questions
        </div>
      </div>

      {/* Question Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {filteredQuestions.length === 0 ? (
          <div
            className="card"
            style={{
              padding: '36px 20px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <Clock size={32} style={{ color: 'var(--color-text-muted)' }} />
            <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-primary)' }}>
              No questions match the current filter
            </div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
              Try selecting "All" to view the full question set.
            </div>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                setStatusFilter('all');
                setCompetencyFilter('all');
              }}
              style={{ marginTop: 8 }}
            >
              Reset Filters
            </button>
          </div>
        ) : (
          filteredQuestions.map((q) => (
            <div key={q.id} style={{ position: 'relative' }}>
              <QuestionCard question={q} />
              {/* Optional hint regenerate override button overlay */}
              <div style={{ position: 'absolute', bottom: 18, right: 100, zIndex: 10 }}>
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => handleOpenRegenerateHint(q.id)}
                  style={{ fontSize: 11.5, padding: '3px 8px', color: 'var(--color-primary)' }}
                  title="Regenerate this question with a specific interviewer guidance hint"
                >
                  <Sparkles size={12} />
                  Regenerate with Hint
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Bottom Actions Bar */}
      <div
        className="card"
        style={{
          padding: '16px 22px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <button type="button" className="btn-secondary" onClick={onBack}>
          <ArrowLeft size={15} />
          Back to Skills & Weights
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {!canProceed && (
            <span style={{ fontSize: 12.5, color: 'var(--color-accent-terra)', fontWeight: 500 }}>
              Please accept at least 1 question to finalize the interview kit.
            </span>
          )}

          <button
            type="button"
            className="btn-primary"
            onClick={onNext}
            disabled={!canProceed}
            style={{ padding: '11px 22px', fontSize: 14 }}
            title={canProceed ? 'Compile approved questions into final executive kit' : 'Accept at least 1 question first'}
          >
            Finish Interview Plan ({acceptedCount} Accepted)
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* Regenerate with Hint Modal */}
      {regenerateTargetId && (
        <Modal
          isOpen={!!regenerateTargetId}
          onClose={() => setRegenerateTargetId(null)}
          title="Regenerate Question with Interviewer Hint"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: 0 }}>
              Provide guidance or specific focus areas you want this question to emphasize.
              The generator will incorporate your direction into the alternative prompt and evaluation rubric.
            </p>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="hint-input">
                Guidance Hint / Focus Angle (Optional)
              </label>
              <textarea
                id="hint-input"
                className="form-textarea"
                rows={3}
                placeholder="e.g. 'Ask more about production outage recovery' or 'Focus specifically on memory leak profiling in high-load scenarios'..."
                value={regenerateHint}
                onChange={(e) => setRegenerateHint(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setRegenerateTargetId(null)}
                disabled={isRegenerating}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleConfirmRegenerate}
                disabled={isRegenerating}
              >
                {isRegenerating ? (
                  <>
                    <RefreshCw size={14} className="spin" />
                    Regenerating...
                  </>
                ) : (
                  <>
                    <Sparkles size={14} />
                    Regenerate Question
                  </>
                )}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
