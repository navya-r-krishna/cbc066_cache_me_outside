import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { generateInterviewPlanFromSkills } from '../../services/api';
import { WeightSliders } from '../Common/WeightSliders';
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  ChevronRight,
  ShieldCheck,
  TrendingUp,
  Tag,
  Loader2,
  Sliders,
  Sparkles,
} from 'lucide-react';

export function SkillsStep({ onBack, onNext }) {
  const { workflowData, updateWorkflowData, addNewBatch, addToast } = useApp();

  const [skills, setSkills] = useState(workflowData.skills || []);
  const [weights, setWeights] = useState(workflowData.weights || { technical: 50, experience: 35, academic: 15 });
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');

  const candidateSummary = workflowData.candidateSummary || {
    candidateName: 'Candidate',
    score: 85,
    band: 'Senior Specialist',
    strengths: ['Direct experience in core architecture', 'Proven project delivery'],
    gaps: ['Limited evidence of disaster recovery in profile'],
    lowInfo: workflowData.lowInfo,
  };

  const handleToggleStatus = (skillId) => {
    setSkills((prev) =>
      prev.map((s) =>
        s.id === skillId
          ? { ...s, status: s.status === 'required' ? 'preferred' : 'required' }
          : s
      )
    );
  };

  const handleGeneratePlan = async () => {
    if (skills.length === 0) {
      addToast({
        type: 'warning',
        title: 'No Skills Selected',
        message: 'At least one skill competency must be included.',
      });
      return;
    }

    setIsGenerating(true);
    setLoadingMsg('Formulating competency interview plan...');

    try {
      const result = await generateInterviewPlanFromSkills(
        {
          jobTitle: workflowData.jobTitle,
          candidateProfile: workflowData.candidateProfile,
          skills,
          weights,
          duration: workflowData.duration,
          difficulty: workflowData.difficulty,
        },
        {
          onProgress: ({ message }) => setLoadingMsg(message),
        }
      );

      if (result.success && result.questions) {
        // Save to workflow
        updateWorkflowData({
          skills,
          weights,
          generatedQuestions: result.questions,
          batchId: result.batchId,
        });

        // Also register batch in the application store for library and dashboard
        const batchMeta = {
          id: result.batchId,
          jobTitle: workflowData.jobTitle,
          candidateName: candidateSummary.candidateName,
          difficulty: workflowData.difficulty,
          experienceLevel: candidateSummary.band,
          duration: workflowData.duration,
          questionCount: result.questions.length,
        };
        addNewBatch(batchMeta, result.questions);

        addToast({
          type: 'success',
          title: 'Interview Plan Generated',
          message: `Created ${result.questions.length} questions mapped to calibrated competencies.`,
        });

        if (onNext) onNext();
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Plan Generation Failed',
        message: err.message,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Header Card */}
      <div className="card" style={{ padding: '20px 24px', background: '#FFFFFF' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-primary)', marginBottom: 4 }}>
              Stage 2: Competency Calibration & Candidate Fit
            </h2>
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', maxWidth: 650 }}>
              Review parsed competencies, required vs. preferred attributes, and adjust evaluation weights.
              The resulting questions will be strictly balanced across these calibrated dimensions.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="badge badge-forest" style={{ fontSize: 12, padding: '5px 10px' }}>
              {skills.length} Extracted Skills
            </span>
            <span className="badge badge-sage" style={{ fontSize: 12, padding: '5px 10px' }}>
              Duration: {workflowData.duration || 45} mins
            </span>
          </div>
        </div>
      </div>

      {/* Low-info warning alert if job description is sparse */}
      {workflowData.lowInfo && (
        <div
          style={{
            background: 'var(--color-accent-terra-light)',
            border: '1px solid var(--color-accent-terra-border, #F4D3C7)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <AlertTriangle size={18} style={{ color: 'var(--color-accent-terra)', flexShrink: 0 }} />
          <div style={{ fontSize: 13, color: 'var(--color-accent-terra-dark)' }}>
            <strong>Notice: Brief Job Description Detected.</strong> The provided role specification is brief.
            Skills and interview questions have been extracted using industry standards for {workflowData.jobTitle}.
            You can calibrate required skills below.
          </div>
        </div>
      )}

      {/* Candidate Fit Summary Card */}
      <div className="card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <ShieldCheck size={20} style={{ color: 'var(--color-primary)' }} />
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-primary)' }}>
                Candidate Fit Assessment • {candidateSummary.candidateName}
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                Target Band: {candidateSummary.band}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                Profile Match
              </div>
              <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--color-primary)' }}>
                {candidateSummary.score}%
              </div>
            </div>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 'var(--radius-full)',
                background: 'var(--color-primary-light)',
                border: '2px solid var(--color-accent-sage)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-primary)',
                fontWeight: 700,
                fontSize: 13,
              }}
            >
              Fit
            </div>
          </div>
        </div>

        {/* Strengths & Gaps Columns */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, borderTop: '1px solid var(--color-border)', paddingTop: 14 }}>
          {/* Strengths */}
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-primary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <CheckCircle2 size={14} style={{ color: 'var(--color-success-text)' }} />
              Key Strengths & Evidence
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {candidateSummary.strengths?.map((s, idx) => (
                <li key={idx} style={{ fontSize: 12.5, color: 'var(--color-text-main)', display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                  <span style={{ color: 'var(--color-success-text)', fontWeight: 700 }}>•</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Gaps (highlighted in Terracotta) */}
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-accent-terra-dark)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertTriangle size={14} style={{ color: 'var(--color-accent-terra)' }} />
              Identified Gaps & Interview Probes
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {candidateSummary.gaps?.map((g, idx) => (
                <li key={idx} style={{ fontSize: 12.5, color: 'var(--color-accent-terra-dark)', display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                  <span style={{ color: 'var(--color-accent-terra)', fontWeight: 700 }}>•</span>
                  <span>{g}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Extracted Skills List with Status and Evidence */}
      <div className="card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Cpu size={18} style={{ color: 'var(--color-primary)' }} />
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
              Parsed Competency Matrix & Citations
            </h3>
          </div>
          <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
            Click status pill to toggle between Required and Preferred
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: '28%' }}>Competency / Skill</th>
                <th style={{ width: '20%' }}>Category</th>
                <th style={{ width: '16%' }}>Requirement Status</th>
                <th style={{ width: '36%' }}>Evidence Citation (JD & Resume)</th>
              </tr>
            </thead>
            <tbody>
              {skills.map((skill) => (
                <tr key={skill.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{skill.name}</div>
                  </td>
                  <td>
                    <span className="badge badge-neutral">{skill.category}</span>
                  </td>
                  <td>
                    <button
                      type="button"
                      onClick={() => handleToggleStatus(skill.id)}
                      className={`badge ${skill.status === 'required' ? 'badge-forest' : 'badge-sage'}`}
                      style={{ cursor: 'pointer', border: '1px solid currentColor' }}
                      title="Click to toggle Required / Preferred"
                    >
                      {skill.status === 'required' ? '★ Required' : 'Preferred'}
                    </button>
                  </td>
                  <td>
                    <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.35 }}>
                      "{skill.evidence}"
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Weight Calibration Sliders */}
      <WeightSliders
        weights={weights}
        onChange={(newWeights) => setWeights(newWeights)}
        title="Interview Evaluation Weight Calibration (Must Total 100%)"
      />

      {/* Bottom Action Footer */}
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
        <button type="button" className="btn-secondary" onClick={onBack} disabled={isGenerating}>
          <ArrowLeft size={15} />
          Back to Role & Resume
        </button>

        <button
          type="button"
          className="btn-primary"
          onClick={handleGeneratePlan}
          disabled={isGenerating}
          style={{ padding: '11px 22px', fontSize: 14 }}
        >
          {isGenerating ? (
            <>
              <Loader2 size={16} className="spin" />
              {loadingMsg || 'Generating Plan...'}
            </>
          ) : (
            <>
              Generate Interview Plan
              <ChevronRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
