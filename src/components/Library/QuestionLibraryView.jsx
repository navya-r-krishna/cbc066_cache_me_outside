import React, { useMemo, useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  FileText,
  Download,
  Printer,
  Copy,
  Check,
  BookOpen,
  Sparkles,
  ArrowLeft,
  User,
} from 'lucide-react';
import {
  exportToCsv,
  exportAcceptedToCsv,
  exportAcceptedToJson,
} from '../../services/exportUtils';

export function QuestionLibraryView() {
  const {
    questions: globalQuestions,
    workflowData,
    addToast,
    setCurrentTab,
  } = useApp();

  const [copiedId, setCopiedId] = useState(null);

  const candidateName =
    workflowData.candidateSummary?.candidateName ||
    workflowData.resumeFileName?.replace(/\.[^/.]+$/, '') ||
    'Candidate';

  const jobTitle = workflowData.jobTitle || 'Senior Full-Stack Engineer';
  const difficulty = workflowData.difficulty || 'Medium';

  // Derive approved questions and ensure each is stored with candidate name from resume
  const approvedQuestions = useMemo(() => {
    const workflowList = workflowData.generatedQuestions || [];
    const acceptedWorkflow = workflowList.filter((q) => q.status === 'accepted');
    let baseList = [];

    if (acceptedWorkflow.length > 0) {
      baseList = acceptedWorkflow;
    } else if (workflowList.length > 0) {
      baseList = workflowList;
    } else {
      const acceptedGlobal = (globalQuestions || []).filter((q) => q.status === 'accepted');
      baseList = acceptedGlobal.length > 0 ? acceptedGlobal : globalQuestions || [];
    }

    return baseList.map((q) => ({
      ...q,
      candidateName: q.candidateName || candidateName,
    }));
  }, [workflowData.generatedQuestions, globalQuestions, candidateName]);

  // Copy individual question text to clipboard
  const handleCopyQuestion = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    addToast({
      type: 'success',
      title: 'Copied to Clipboard',
      message: 'Question prompt copied for interview notes.',
      duration: 2000,
    });
    setTimeout(() => {
      setCopiedId(null);
    }, 2000);
  };

  // Export handlers
  const handleExportCsv = () => {
    if (approvedQuestions.length === 0) return;
    try {
      let res;
      try {
        res = exportAcceptedToCsv(approvedQuestions, `interview_kit_${candidateName.replace(/\s+/g, '_')}`);
      } catch {
        res = exportToCsv(approvedQuestions, `interview_kit_${candidateName.replace(/\s+/g, '_')}`);
      }
      addToast({
        type: 'success',
        title: 'CSV Export Succeeded',
        message: `Saved ${res.count} questions for ${candidateName} to ${res.filename}`,
      });
    } catch (e) {
      addToast({ type: 'warning', title: 'Export Notice', message: e.message });
    }
  };

  const handleExportJson = () => {
    if (approvedQuestions.length === 0) return;
    try {
      let res;
      try {
        res = exportAcceptedToJson(approvedQuestions, `interview_kit_${candidateName.replace(/\s+/g, '_')}`);
      } catch {
        const payload = {
          candidateName,
          jobTitle,
          difficulty,
          approvedQuestions,
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `interview_kit_${candidateName.replace(/\s+/g, '_')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        res = { count: approvedQuestions.length, filename: `interview_kit_${candidateName.replace(/\s+/g, '_')}.json` };
      }
      addToast({
        type: 'success',
        title: 'JSON Export Succeeded',
        message: `Saved ${res.count} questions for ${candidateName} to ${res.filename}`,
      });
    } catch (e) {
      addToast({ type: 'warning', title: 'Export Notice', message: e.message });
    }
  };

  const handlePrintPdf = () => {
    window.print();
    addToast({
      type: 'info',
      title: 'Print Dialog Opened',
      message: 'Select "Save as PDF" to save interview question kit.',
    });
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header Bar */}
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
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileText size={20} style={{ color: 'var(--color-primary)' }} />
              <h1
                style={{
                  fontSize: 20,
                  fontWeight: 700,
                  color: 'var(--color-primary)',
                  margin: 0,
                  letterSpacing: '-0.3px',
                }}
              >
                Approved Interview Question Kit ({approvedQuestions.length} Questions)
              </h1>
            </div>
            <p
              style={{
                fontSize: 13,
                color: 'var(--color-text-secondary)',
                marginTop: 4,
                margin: 0,
              }}
            >
              Curated questions stored for candidate <strong>{candidateName}</strong> based on evaluated resume
            </p>
          </div>

          <div className="no-print" style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <button
              className="btn-secondary"
              onClick={handleExportCsv}
              disabled={approvedQuestions.length === 0}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13 }}
            >
              <Download size={14} /> Export CSV
            </button>
            <button
              className="btn-secondary"
              onClick={handleExportJson}
              disabled={approvedQuestions.length === 0}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13 }}
            >
              <Download size={14} /> Export JSON
            </button>
            <button
              className="btn-primary"
              onClick={handlePrintPdf}
              disabled={approvedQuestions.length === 0}
              style={{
                background: 'var(--color-primary)',
                color: '#FFFFFF',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                fontSize: 13,
              }}
            >
              <Printer size={14} /> Print / Save PDF
            </button>
          </div>
        </div>

        {/* Candidate & Role Metadata Strip */}
        {approvedQuestions.length > 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 10,
              marginTop: 16,
              paddingTop: 14,
              borderTop: '1px solid var(--color-border)',
            }}
          >
            <span
              className="badge badge-forest"
              style={{
                fontSize: 12,
                padding: '4px 10px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
              }}
            >
              <User size={13} /> Candidate: {candidateName}
            </span>
            <span className="badge badge-sage" style={{ fontSize: 11.5 }}>
              Role: {jobTitle}
            </span>
            <span className="badge badge-sage" style={{ fontSize: 11.5 }}>
              Difficulty: {difficulty}
            </span>
            <span className="badge badge-success" style={{ fontSize: 11.5, marginLeft: 'auto' }}>
              ✓ Stored with Candidate Resume Record
            </span>
          </div>
        )}
      </div>

      {/* Empty State if no questions approved */}
      {approvedQuestions.length === 0 ? (
        <div
          className="card empty-state-card animate-fade-in"
          style={{
            padding: '52px 24px',
            textAlign: 'center',
            background: '#FFFFFF',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: '50%',
              background: 'var(--color-primary-light)',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 16,
            }}
          >
            <BookOpen size={26} />
          </div>
          <h2
            style={{
              fontSize: 18,
              fontWeight: 700,
              color: 'var(--color-primary)',
              marginBottom: 8,
            }}
          >
            No Approved Questions in Kit Yet
          </h2>
          <p
            style={{
              fontSize: 14,
              color: 'var(--color-text-secondary)',
              maxWidth: 460,
              margin: '0 auto 22px',
              lineHeight: 1.5,
            }}
          >
            Formulate and approve interview questions on the Dashboard to populate your interview question kit.
          </p>
          <button
            className="btn-primary"
            onClick={() => setCurrentTab('dashboard')}
            style={{
              background: 'var(--color-primary)',
              color: '#FFFFFF',
              padding: '10px 24px',
              fontSize: 13.5,
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              borderRadius: 'var(--radius-sm)',
            }}
          >
            <Sparkles size={15} />
            Go to Executive Dashboard
          </button>
        </div>
      ) : (
        /* Approved Questions Cards List */
        <div
          className="card"
          style={{
            padding: '20px 24px',
            background: '#FFFFFF',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {approvedQuestions.map((q, idx) => (
              <div
                key={q.id || idx}
                style={{
                  padding: '16px 18px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--color-surface-subtle)',
                  border: '1px solid var(--color-border)',
                  borderLeft: '4px solid var(--color-primary)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                  transition: 'box-shadow 150ms ease',
                }}
              >
                {/* Meta Badges Row with Candidate Name */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span className="badge badge-forest" style={{ fontSize: 11.5 }}>
                      Q{idx + 1} • {q.competency || 'Core Competency'}
                    </span>
                    <span
                      className="badge badge-forest"
                      style={{
                        fontSize: 11.5,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                    >
                      <User size={12} /> Candidate: {q.candidateName || candidateName}
                    </span>
                    <span className="badge badge-sage" style={{ fontSize: 11.5 }}>
                      Difficulty: {q.difficulty || difficulty}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="badge badge-success" style={{ fontSize: 11 }}>
                      Approved
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopyQuestion(q.id || idx, q.question)}
                      style={{
                        padding: '3px 8px',
                        fontSize: 11,
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid var(--color-border)',
                        background: '#FFFFFF',
                        color: copiedId === (q.id || idx) ? 'var(--color-success-text)' : 'var(--color-text-secondary)',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                      }}
                      title="Copy question text to clipboard"
                    >
                      {copiedId === (q.id || idx) ? (
                        <>
                          <Check size={11} /> Copied
                        </>
                      ) : (
                        <>
                          <Copy size={11} /> Copy
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Question Text */}
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-main)', lineHeight: 1.5 }}>
                  {q.question}
                </div>

                {/* Evaluation Rubric "Look for:" */}
                {q.evaluationRubric && (
                  <div
                    style={{
                      fontSize: 12.5,
                      color: 'var(--color-text-secondary)',
                      background: '#FFFFFF',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--color-border)',
                      lineHeight: 1.45,
                    }}
                  >
                    <strong style={{ color: 'var(--color-primary)' }}>Look for:</strong> {q.evaluationRubric}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Back to Dashboard Footer */}
      <div
        className="card no-print"
        style={{
          padding: '14px 24px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <button
          type="button"
          className="btn-secondary"
          onClick={() => setCurrentTab('dashboard')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 13 }}
        >
          <ArrowLeft size={14} /> Back to Dashboard
        </button>

        <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
          InterviewIQ • Candidate: {candidateName}
        </span>
      </div>
    </div>
  );
}
