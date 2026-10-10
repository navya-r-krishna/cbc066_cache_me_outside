import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  CheckCircle2,
  XCircle,
  Sparkles,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Lightbulb,
  FileText,
  Trash2,
  Loader2,
} from 'lucide-react';
import { Modal } from '../Common/Modal';

export function QuestionCard({ question }) {
  const {
    acceptQuestion,
    rejectQuestion,
    regenerateQuestionItem,
    updateQuestionNotes,
    deleteQuestion,
    addToast,
  } = useApp();

  const [expandedRubric, setExpandedRubric] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [notes, setNotes] = useState(question.interviewerNotes || '');

  const getCompetencyBadgeStyle = (comp) => {
    if (!comp) return { bg: 'var(--color-primary-light)', color: 'var(--color-primary)', border: 'var(--color-accent-sage)' };
    if (comp.includes('Technical') || comp.includes('Coding')) {
      return { bg: 'var(--color-primary-light)', color: 'var(--color-primary)', border: 'var(--color-accent-sage)' };
    }
    if (comp.includes('Problem') || comp.includes('Algorithm') || comp.includes('Performance')) {
      return { bg: 'var(--color-surface-subtle)', color: 'var(--color-text-main)', border: 'var(--color-border)' };
    }
    if (comp.includes('Behavioral') || comp.includes('Behavioural') || comp.includes('Leadership')) {
      return { bg: '#F2EFE8', color: 'var(--color-text-secondary)', border: 'var(--color-border)' };
    }
    if (comp.includes('System') || comp.includes('Design') || comp.includes('Architecture')) {
      return { bg: 'var(--color-accent-sage-light)', color: 'var(--color-accent-sage-dark)', border: '#C4D3C0' };
    }
    return { bg: 'var(--color-primary-light)', color: 'var(--color-primary)', border: 'var(--color-accent-sage)' };
  };

  const compStyle = getCompetencyBadgeStyle(question.competency);

  const handleCopy = () => {
    const textToCopy = `QUESTION:
${question.question}

WHY RELEVANT:
${question.whyRelevant}

EVALUATION RUBRIC:
${question.evaluationRubric}

FOLLOW-UP PROBES:
${Array.isArray(question.followUps) ? question.followUps.map((f) => `- ${f}`).join('\n') : ''}`;

    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    addToast({
      type: 'info',
      title: 'Copied to Clipboard',
      message: 'Question and evaluation rubric copied.',
      duration: 2000,
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    await regenerateQuestionItem(question.id);
    setIsRegenerating(false);
  };

  const confirmReject = () => {
    rejectQuestion(question.id, rejectReason);
    setShowRejectModal(false);
    setRejectReason('');
  };

  const saveNotes = () => {
    updateQuestionNotes(question.id, notes);
    setShowNotesModal(false);
  };

  const statusClass =
    question.status === 'accepted'
      ? 'status-accepted'
      : question.status === 'rejected'
      ? 'status-rejected'
      : 'status-pending';

  return (
    <>
      <div className={`card question-card ${statusClass} animate-fade-in`}>
        {/* Top bar with badges */}
        <div className="q-card-top-bar">
          <div className="q-badges-group">
            <span
              className="badge"
              style={{
                backgroundColor: compStyle.bg,
                color: compStyle.color,
                border: `1px solid ${compStyle.border}`,
              }}
            >
              {question.competency}
            </span>

            <span className="badge badge-forest">Difficulty: {question.difficulty}</span>

            {question.jobTitle && (
              <span
                style={{
                  fontSize: '11.5px',
                  color: 'var(--text-muted)',
                  fontWeight: 500,
                  maxWidth: 260,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {question.jobTitle}
              </span>
            )}
          </div>

          <div>
            {question.status === 'accepted' && (
              <span className="badge badge-success">
                <CheckCircle2 size={12} /> Accepted
              </span>
            )}
            {question.status === 'rejected' && (
              <span className="badge badge-danger">
                <XCircle size={12} /> Rejected
              </span>
            )}
            {(!question.status || question.status === 'pending') && (
              <span className="badge badge-warning">Needs Review</span>
            )}
          </div>
        </div>

        {/* Main Question Text */}
        <div className="q-prompt-text">{question.question}</div>

        {/* Relevance Explanation Box */}
        {question.whyRelevant && (
          <div className="ai-relevance-box">
            <div className="ai-relevance-header">
              <Lightbulb size={14} style={{ color: 'var(--primary)' }} />
              Why Relevant
            </div>
            <div className="ai-relevance-content">{question.whyRelevant}</div>
          </div>
        )}

        {/* Evaluation Rubric & Follow-ups Drawer */}
        {(question.evaluationRubric || (question.followUps && question.followUps.length > 0)) && (
          <div className="rubric-drawer">
            <div
              className="rubric-toggle-bar"
              onClick={() => setExpandedRubric(!expandedRubric)}
              role="button"
              tabIndex={0}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <FileText size={15} style={{ color: 'var(--primary)' }} />
                <span>Interviewer Evaluation Rubric & Follow-Up Probes</span>
              </div>
              {expandedRubric ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>

            {expandedRubric && (
              <div className="rubric-content-details animate-fade-in">
                {question.evaluationRubric && (
                  <div style={{ marginBottom: 10 }}>
                    <div
                      style={{
                        fontSize: 11.5,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        color: 'var(--text-muted)',
                        marginBottom: 4,
                      }}
                    >
                      Evaluation Criteria:
                    </div>
                    <div>{question.evaluationRubric}</div>
                  </div>
                )}

                {question.followUps && question.followUps.length > 0 && (
                  <div>
                    <div
                      style={{
                        fontSize: 11.5,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        color: 'var(--text-muted)',
                        marginBottom: 4,
                      }}
                    >
                      Follow-up Probing Questions:
                    </div>
                    <ul className="followups-list">
                      {question.followUps.map((fu, idx) => (
                        <li key={idx}>{fu}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Rejection Reason notice if rejected */}
        {question.status === 'rejected' && question.rejectionReason && (
          <div
            style={{
              padding: '8px 12px',
              background: 'var(--danger-bg)',
              border: '1px solid var(--danger-border)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              color: 'var(--danger-text)',
              marginBottom: 14,
            }}
          >
            <strong>Rejection Reason:</strong> {question.rejectionReason}
          </div>
        )}

        {/* Interviewer Notes preview if added */}
        {question.interviewerNotes && (
          <div
            style={{
              padding: '8px 12px',
              background: 'var(--color-primary-light)',
              border: '1px solid var(--color-accent-sage)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              color: 'var(--color-primary)',
              marginBottom: 14,
            }}
          >
            <strong>Interviewer Notes:</strong> {question.interviewerNotes}
          </div>
        )}

        {/* Action Buttons Bar */}
        <div className="q-card-actions-bar">
          <div className="q-action-buttons-left">
            <button
              className="btn-accept"
              onClick={() => acceptQuestion(question.id)}
              disabled={question.status === 'accepted'}
              title="Approve this question into your final interview kit"
            >
              <CheckCircle2 size={15} />
              {question.status === 'accepted' ? 'Accepted' : 'Accept'}
            </button>

            <button
              className="btn-reject"
              onClick={() => setShowRejectModal(true)}
              disabled={question.status === 'rejected'}
              title="Reject or flag this question as unsuitable"
            >
              <XCircle size={15} />
              {question.status === 'rejected' ? 'Rejected' : 'Reject'}
            </button>

            <button
              className="btn-regenerate"
              onClick={handleRegenerate}
              disabled={isRegenerating}
              title="Synthesize an alternative prompt for this competency"
            >
              {isRegenerating ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <Sparkles size={15} />
              )}
              {isRegenerating ? 'Regenerating...' : 'Regenerate'}
            </button>
          </div>

          <div className="q-tools-right">
            <button
              className="btn-ghost"
              onClick={() => setShowNotesModal(true)}
              title="Add or edit interviewer evaluation notes"
            >
              <MessageSquare size={15} />
              {question.interviewerNotes ? 'Edit Notes' : 'Notes'}
            </button>

            <button
              className="btn-ghost"
              onClick={handleCopy}
              title="Copy question and rubric to clipboard"
            >
              {copied ? <Check size={15} style={{ color: 'var(--success)' }} /> : <Copy size={15} />}
              {copied ? 'Copied' : 'Copy'}
            </button>

            <button
              className="btn-ghost"
              onClick={() => deleteQuestion(question.id)}
              title="Delete question permanently"
              style={{ color: 'var(--text-muted)' }}
            >
              <Trash2 size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Reject Reason Modal */}
      <Modal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        title="Reject Interview Question"
        footer={
          <>
            <button className="btn-secondary" onClick={() => setShowRejectModal(false)}>
              Cancel
            </button>
            <button className="btn-primary" style={{ background: 'var(--danger)' }} onClick={confirmReject}>
              Confirm Reject
            </button>
          </>
        }
      >
        <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', marginBottom: 12 }}>
          Provide an optional reason or flag for why this question is unsuitable for this role.
        </p>
        <textarea
          className="form-textarea"
          rows={3}
          placeholder="e.g. Too theoretical, covered in previous screen, doesn't match team tech stack..."
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
        />
      </Modal>

      {/* Notes Modal */}
      <Modal
        isOpen={showNotesModal}
        onClose={() => setShowNotesModal(false)}
        title="Interviewer Evaluation Notes"
        footer={
          <>
            <button className="btn-secondary" onClick={() => setShowNotesModal(false)}>
              Cancel
            </button>
            <button className="btn-primary" onClick={saveNotes}>
              Save Notes
            </button>
          </>
        }
      >
        <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', marginBottom: 12 }}>
          Record private notes, expected keywords, or live candidate observations.
        </p>
        <textarea
          className="form-textarea"
          rows={4}
          placeholder="e.g. Candidate answered the caching layer well but struggled when pressed on database connection pool limits..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </Modal>
    </>
  );
}
