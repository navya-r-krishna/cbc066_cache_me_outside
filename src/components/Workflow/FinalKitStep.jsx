import React, { useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { exportAcceptedToCsv, exportAcceptedToJson } from '../../services/exportUtils';
import {
  Printer,
  Download,
  FileText,
  CheckCircle2,
  BookOpen,
  ArrowLeft,
  RotateCcw,
  ShieldCheck,
  Clock,
  Sparkles,
  Layers,
  Award,
} from 'lucide-react';

export function FinalKitStep({ onBack, onRestart }) {
  const { workflowData, setCurrentTab, addToast } = useApp();

  const candidateSummary = workflowData.candidateSummary || {
    candidateName: 'Candidate Profile',
    score: 88,
    band: 'Senior Specialist',
    strengths: ['Strong technical fundamentals', 'Demonstrated production ownership'],
    gaps: ['Limited multi-region disaster recovery evidence'],
  };

  const weights = workflowData.weights || { technical: 50, experience: 35, academic: 15 };

  // Get accepted questions, or fallback to all questions in batch if none explicitly accepted
  const acceptedQuestions = useMemo(() => {
    const list = workflowData.generatedQuestions || [];
    const accepted = list.filter((q) => q.status === 'accepted');
    const target = accepted.length > 0 ? accepted : list;

    // Sort by difficulty progression: Easy -> Medium -> Hard
    const diffRank = { Easy: 1, Junior: 1, Medium: 2, Mid: 2, Hard: 3, Senior: 3, Staff: 4 };
    return [...target].sort((a, b) => {
      const rA = diffRank[a.difficulty] || 2;
      const rB = diffRank[b.difficulty] || 2;
      return rA - rB;
    });
  }, [workflowData.generatedQuestions]);

  const handlePrintPdf = () => {
    window.print();
    addToast({
      type: 'info',
      title: 'Print Dialog Opened',
      message: 'Select "Save as PDF" to save your executive interview kit.',
      duration: 3500,
    });
  };

  const handleExportCsv = () => {
    try {
      const res = exportAcceptedToCsv(acceptedQuestions, `interview_kit_${workflowData.jobTitle}`);
      addToast({
        type: 'success',
        title: 'CSV Export Successful',
        message: `Saved ${res.count} interview questions to ${res.filename}`,
      });
    } catch (e) {
      addToast({ type: 'warning', title: 'Export Notice', message: e.message });
    }
  };

  const handleExportJson = () => {
    try {
      const res = exportAcceptedToJson(acceptedQuestions, `interview_kit_${workflowData.jobTitle}`);
      addToast({
        type: 'success',
        title: 'JSON Export Successful',
        message: `Saved ${res.count} interview questions to ${res.filename}`,
      });
    } catch (e) {
      addToast({ type: 'warning', title: 'Export Notice', message: e.message });
    }
  };

  const handleGoToLibrary = () => {
    setCurrentTab('library');
    addToast({
      type: 'info',
      title: 'Question Repository',
      message: 'Viewing approved questions in library.',
    });
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Action Toolbar (Hidden during print) */}
      <div
        className="card no-print"
        style={{
          padding: '16px 22px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          background: '#FFFFFF',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button type="button" className="btn-secondary" onClick={onBack}>
            <ArrowLeft size={15} />
            Back to Plan Review
          </button>
          <button type="button" className="btn-ghost" onClick={onRestart} style={{ fontSize: 12.5 }}>
            <RotateCcw size={14} />
            New Interview
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn-primary"
            onClick={handlePrintPdf}
            style={{ padding: '8px 16px', fontSize: 13 }}
            title="Open browser print dialog formatted for clean PDF output"
          >
            <Printer size={15} />
            Download PDF Kit
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={handleExportCsv}
            style={{ padding: '8px 13px', fontSize: 13 }}
          >
            <Download size={15} />
            Export CSV
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={handleExportJson}
            style={{ padding: '8px 13px', fontSize: 13 }}
          >
            <Download size={15} />
            Export JSON
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={handleGoToLibrary}
            style={{ padding: '8px 13px', fontSize: 13 }}
          >
            <BookOpen size={15} />
            View in Repository
          </button>
        </div>
      </div>

      {/* Main Formatted Executive Interview Document */}
      <div
        className="card final-document-container"
        style={{
          padding: '36px 42px',
          background: '#FFFFFF',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        {/* Document Header */}
        <div
          style={{
            borderBottom: '2px solid var(--color-primary)',
            paddingBottom: 20,
            marginBottom: 24,
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 16,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: 0.8,
                color: 'var(--color-text-secondary)',
                marginBottom: 4,
              }}
            >
              InterviewIQ • Executive Interview Guide
            </div>
            <h1
              style={{
                fontSize: 24,
                fontWeight: 800,
                color: 'var(--color-primary)',
                lineHeight: 1.2,
                marginBottom: 6,
              }}
            >
              {workflowData.jobTitle}
            </h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', fontSize: 13, color: 'var(--color-text-secondary)' }}>
              <span>
                <strong>Candidate:</strong> {candidateSummary.candidateName}
              </span>
              <span>•</span>
              <span>
                <strong>Duration:</strong> {workflowData.duration || 45} mins
              </span>
              <span>•</span>
              <span>
                <strong>Target Level:</strong> {candidateSummary.band}
              </span>
              <span>•</span>
              <span>
                <strong>Date:</strong> {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
              </span>
            </div>
          </div>

          {/* Calibrated Weights Pill Badge */}
          <div
            style={{
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 14px',
              textAlign: 'right',
            }}
          >
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-secondary)', marginBottom: 4 }}>
              Calibrated Evaluation Weights
            </div>
            <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-primary)' }}>
              Technical: {weights.technical}% • Experience: {weights.experience}% • Academic: {weights.academic}%
            </div>
          </div>
        </div>

        {/* Candidate Fit Overview Bar */}
        <div
          style={{
            background: 'var(--color-surface-subtle)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '16px 20px',
            marginBottom: 28,
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 16,
          }}
        >
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-primary)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
              <ShieldCheck size={14} style={{ color: 'var(--color-primary)' }} />
              Candidate Profile Strengths
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12 }}>
              {candidateSummary.strengths?.slice(0, 2).map((s, idx) => (
                <li key={idx} style={{ color: 'var(--color-text-main)' }}>
                  ✓ {s}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-accent-terra-dark)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Award size={14} style={{ color: 'var(--color-accent-terra)' }} />
              Key Areas to Probe in Interview
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12 }}>
              {candidateSummary.gaps?.slice(0, 2).map((g, idx) => (
                <li key={idx} style={{ color: 'var(--color-accent-terra-dark)' }}>
                  • {g}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Question Sequence List (Sorted Easy -> Hard) */}
        <div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              color: 'var(--color-primary)',
              borderBottom: '1px solid var(--color-border)',
              paddingBottom: 8,
              marginBottom: 20,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>Approved Question Sequence ({acceptedQuestions.length} Questions)</span>
            <span style={{ fontSize: 11.5, fontWeight: 500, color: 'var(--color-text-secondary)', textTransform: 'none' }}>
              Structured in progressive difficulty order
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {acceptedQuestions.map((q, idx) => (
              <div
                key={q.id || idx}
                className="question-card"
                style={{
                  padding: '20px 22px',
                  background: '#FFFFFF',
                  border: '1px solid var(--color-border)',
                  borderLeft: '4px solid var(--color-primary)',
                }}
              >
                {/* Question Item Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span
                      style={{
                        background: 'var(--color-primary)',
                        color: '#FFFFFF',
                        fontSize: 12,
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-xs)',
                      }}
                    >
                      Question {idx + 1}
                    </span>
                    <span className="badge badge-forest">{q.competency}</span>
                    <span className="badge badge-sage">{q.difficulty}</span>
                    {q.skillName && (
                      <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 500 }}>
                        Skill: {q.skillName}
                      </span>
                    )}
                  </div>

                  <span className="badge badge-success">
                    <CheckCircle2 size={12} /> Approved
                  </span>
                </div>

                {/* Prompt Text */}
                <div style={{ fontSize: 15.5, fontWeight: 600, color: 'var(--color-primary)', lineHeight: 1.45, marginBottom: 12 }}>
                  {q.question}
                </div>

                {/* Rationale */}
                {q.whyRelevant && (
                  <div
                    style={{
                      background: 'var(--color-surface-subtle)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-xs)',
                      padding: '8px 12px',
                      fontSize: 12.5,
                      color: 'var(--color-text-main)',
                      marginBottom: 12,
                    }}
                  >
                    <strong>Why Relevant: </strong>
                    {q.whyRelevant}
                  </div>
                )}

                {/* Evaluation Rubric */}
                {q.evaluationRubric && (
                  <div
                    style={{
                      borderTop: '1px dashed var(--color-border)',
                      paddingTop: 10,
                      marginBottom: 10,
                    }}
                  >
                    <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-secondary)', marginBottom: 4 }}>
                      Interviewer Evaluation Rubric (What to Look For):
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                      {q.evaluationRubric}
                    </div>
                  </div>
                )}

                {/* Follow-Up Probes */}
                {Array.isArray(q.followUps) && q.followUps.length > 0 && (
                  <div style={{ borderTop: '1px dashed var(--color-border)', paddingTop: 8 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-secondary)', marginBottom: 4 }}>
                      Suggested Follow-Up Probes:
                    </div>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12.5 }}>
                      {q.followUps.map((f, fIdx) => (
                        <li key={fIdx} style={{ color: 'var(--color-text-main)', display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                          <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>›</span>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Interviewer Scoring Box (Useful during print interview evaluation) */}
                <div
                  style={{
                    marginTop: 14,
                    paddingTop: 10,
                    borderTop: '1px solid var(--color-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: 12,
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span>Candidate Score: [ &nbsp; ] 1 &nbsp; [ &nbsp; ] 2 &nbsp; [ &nbsp; ] 3 &nbsp; [ &nbsp; ] 4 &nbsp; [ &nbsp; ] 5</span>
                  </div>
                  <div style={{ fontStyle: 'italic', fontSize: 11.5 }}>
                    Evaluator Notes: _______________________________
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Document Footer */}
        <div
          style={{
            marginTop: 36,
            paddingTop: 16,
            borderTop: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 11.5,
            color: 'var(--color-text-secondary)',
          }}
        >
          <div>InterviewIQ Assessment System • Confidential Recruiting Record</div>
          <div>Page 1 of 1</div>
        </div>
      </div>
    </div>
  );
}
