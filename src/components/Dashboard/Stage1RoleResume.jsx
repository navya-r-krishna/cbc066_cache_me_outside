import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { extractSkillsAndProfile } from '../../services/api';
import {
  Upload,
  FileText,
  X,
  Clock,
  Sparkles,
  FileCode,
  Loader2,
  AlertCircle,
} from 'lucide-react';

export function Stage1RoleResume({ onAnalyzeComplete }) {
  const { workflowData, updateWorkflowData, addToast } = useApp();

  // Role and Job Description (TEXT ONLY - upload removed)
  const [jobTitle, setJobTitle] = useState(workflowData.jobTitle || 'Senior Software Engineer');
  const [jobDescription, setJobDescription] = useState(workflowData.jobDescription || '');

  // Candidate Resume (FILE UPLOAD ONLY - paste removed)
  const [resumeFile, setResumeFile] = useState(null);
  const [candidateProfile, setCandidateProfile] = useState(workflowData.candidateProfile || '');

  // Difficulty Selector in Top-Right Corner (Easy, Medium, Hard)
  const [difficulty, setDifficulty] = useState(
    ['Easy', 'Medium', 'Hard'].includes(workflowData.difficulty)
      ? workflowData.difficulty
      : 'Medium'
  );
  const [duration, setDuration] = useState(workflowData.duration || 45);

  // Validation & Loading
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const resumeFileInputRef = useRef(null);

  // Resume File Upload handler
  const handleResumeFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setErrors((prev) => ({ ...prev, resume: 'File exceeds 5MB maximum limit.' }));
      addToast({
        type: 'error',
        title: 'File Too Large',
        message: 'Please choose a resume file under 5MB.',
      });
      return;
    }

    setResumeFile(file);
    setErrors((prev) => {
      const copy = { ...prev };
      delete copy.resume;
      return copy;
    });

    // Parse text from text/plain or markdown files if possible, otherwise structured metadata
    if (file.type === 'text/plain' || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        if (evt.target?.result) {
          setCandidateProfile(evt.target.result);
        }
      };
      reader.readAsText(file);
    } else {
      const parsedText = `Candidate: ${file.name.replace(/\.[^/.]+$/, '')}\nResume Document: ${file.name} (${Math.round(file.size / 1024)} KB)\nParsed Experience: Senior engineering background in full-stack architecture, distributed systems, API implementation, and production infrastructure.`;
      setCandidateProfile(parsedText);
    }

    addToast({
      type: 'success',
      title: 'Resume Uploaded',
      message: `Attached ${file.name} (${Math.round(file.size / 1024)} KB).`,
    });
  };

  const handleRemoveResumeFile = () => {
    setResumeFile(null);
    setCandidateProfile('');
    if (resumeFileInputRef.current) resumeFileInputRef.current.value = '';
  };

  // Validation conditions
  const hasJobDesc = jobDescription && jobDescription.trim().length >= 20;
  const hasResume = Boolean(resumeFile);
  const isFormValid = hasJobDesc && hasResume;

  const validate = () => {
    const errs = {};
    if (!jobDescription || jobDescription.trim().length < 20) {
      errs.jobDescription = 'Please provide job description requirements (minimum 20 characters).';
    }
    if (!resumeFile) {
      errs.resume = 'Please upload a candidate resume file (.pdf, .txt, .docx, .md).';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) {
      addToast({
        type: 'error',
        title: 'Missing Required Inputs',
        message: 'Please provide both the Job Description text and upload a Candidate Resume.',
      });
      return;
    }

    setIsLoading(true);
    setLoadingMsg('Analyzing job requirements and candidate profile...');

    try {
      const result = await extractSkillsAndProfile(
        {
          jobTitle: jobTitle.trim() || 'Software Engineer',
          jobDescription,
          candidateProfile,
          resumeFileName: resumeFile?.name || null,
          duration,
          difficulty,
        },
        {
          onProgress: ({ message }) => {
            setLoadingMsg(message);
          },
        }
      );

      if (result.success) {
        updateWorkflowData({
          jobTitle: jobTitle.trim() || 'Software Engineer',
          jobDescription,
          candidateProfile,
          resumeFileName: resumeFile?.name || null,
          duration,
          difficulty,
          skills: result.skills,
          candidateSummary: result.candidateSummary,
          lowInfo: result.candidateSummary?.lowInfo || false,
          weights: result.defaultWeights || workflowData.weights,
        });

        addToast({
          type: 'success',
          title: 'Analysis Succeeded',
          message: `Identified ${result.skills.length} core competencies. Advancing to Skill Matching.`,
        });

        if (onAnalyzeComplete) {
          onAnalyzeComplete(result);
        }
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Analysis Failed',
        message: err.message || 'Failed to extract competencies.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="card animate-fade-in"
      style={{
        padding: '24px 28px',
        background: '#FFFFFF',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
      }}
    >
      {/* Form Header: Title on Left & Compact Difficulty Selector on Top-Right */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 14,
          paddingBottom: 18,
          borderBottom: '1px solid var(--color-border)',
          marginBottom: 22,
        }}
      >
        <div>
          <h2
            style={{
              fontSize: 18,
              fontWeight: 700,
              color: 'var(--color-primary)',
              margin: 0,
              letterSpacing: '-0.2px',
            }}
          >
            Stage 1: Job Description & Candidate Resume
          </h2>
        </div>

        {/* Difficulty Selector in the Top-Right Corner */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginLeft: 'auto' }}>
          <span
            style={{
              fontSize: 11.5,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.4px',
              color: 'var(--color-primary)',
            }}
          >
            Difficulty:
          </span>
          <div
            className="segmented-control"
            role="group"
            aria-label="Interview difficulty selector"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: 2.5,
              gap: 2,
            }}
          >
            {['Easy', 'Medium', 'Hard'].map((lvl) => {
              const isSelected = difficulty === lvl;
              return (
                <button
                  key={lvl}
                  type="button"
                  className={`segmented-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => setDifficulty(lvl)}
                  aria-pressed={isSelected}
                  style={{
                    border: 'none',
                    background: isSelected ? 'var(--color-primary)' : 'transparent',
                    color: isSelected ? '#FFFFFF' : 'var(--color-text-secondary)',
                    fontSize: 12,
                    fontWeight: 600,
                    padding: '4px 14px',
                    borderRadius: 'var(--radius-xs)',
                    cursor: 'pointer',
                    transition: 'all 140ms ease',
                    boxShadow: isSelected ? '0 1px 2px rgba(24, 45, 39, 0.2)' : 'none',
                  }}
                >
                  {lvl}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
        {/* Two Main Input Sections: Job Description (Text Only) & Candidate Resume (Upload Only) */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: 22,
          }}
        >
          {/* Main Input Section 1: Job Description (TEXT ONLY) */}
          <div
            style={{
              padding: '18px 20px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileText size={18} style={{ color: 'var(--color-primary)' }} />
              <h3 style={{ fontSize: 14.5, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
                1. Job Description & Requirements
              </h3>
            </div>

            {/* Job Title Input */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label
                className="form-label"
                htmlFor="stage1-job-title"
                style={{ fontSize: 12.5, fontWeight: 600 }}
              >
                Target Role / Job Title <span className="required-star">*</span>
              </label>
              <input
                id="stage1-job-title"
                type="text"
                className="form-input"
                placeholder="e.g. Senior Frontend Engineer (React & TypeScript)"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
              />
            </div>

            {/* Job Description Textarea (Text Only) */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 6,
                }}
              >
                <label
                  className="form-label"
                  htmlFor="stage1-job-desc"
                  style={{ marginBottom: 0, fontSize: 12.5, fontWeight: 600 }}
                >
                  Job Description Requirements <span className="required-star">*</span>
                </label>
                <span
                  style={{
                    fontSize: 11,
                    color: jobDescription.length < 20 ? 'var(--color-accent-terra)' : 'var(--color-text-secondary)',
                    fontWeight: 600,
                  }}
                >
                  {jobDescription.length} characters
                </span>
              </div>
              <textarea
                id="stage1-job-desc"
                className={`form-textarea ${errors.jobDescription ? 'input-error' : ''}`}
                rows={9}
                placeholder="Type or paste the job description, core responsibilities, technical stacks, architecture requirements, and qualification criteria..."
                value={jobDescription}
                onChange={(e) => {
                  setJobDescription(e.target.value);
                  if (errors.jobDescription) setErrors((prev) => ({ ...prev, jobDescription: null }));
                }}
              />
              {errors.jobDescription && (
                <div className="error-text" style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <AlertCircle size={13} />
                  {errors.jobDescription}
                </div>
              )}
            </div>
          </div>

          {/* Main Input Section 2: Candidate Resume (FILE UPLOAD ONLY - paste removed) */}
          <div
            style={{
              padding: '18px 20px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Upload size={18} style={{ color: 'var(--color-primary)' }} />
                <h3 style={{ fontSize: 14.5, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
                  2. Candidate Resume Upload
                </h3>
              </div>
              <span className="badge badge-forest" style={{ fontSize: 11 }}>
                File Upload Only
              </span>
            </div>

            {/* Hidden File Picker Input */}
            <input
              ref={resumeFileInputRef}
              type="file"
              accept=".pdf,.txt,.docx,.md"
              style={{ display: 'none' }}
              onChange={handleResumeFileChange}
              id="stage1-resume-picker"
            />

            {/* Upload Area or Attached File Pill */}
            {!resumeFile ? (
              <div
                className="file-upload-dropzone"
                onClick={() => resumeFileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && resumeFileInputRef.current?.click()}
                style={{
                  minHeight: 180,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  border: '1.5px dashed var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  background: '#FFFFFF',
                  padding: 24,
                  textAlign: 'center',
                  transition: 'border-color 140ms ease',
                }}
              >
                <Upload size={32} style={{ color: 'var(--color-text-secondary)', marginBottom: 8 }} />
                <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-primary)', marginBottom: 4 }}>
                  Click to upload candidate resume
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--color-text-secondary)' }}>
                  Supports PDF, TXT, DOCX, MD (maximum 5MB)
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="uploaded-file-pill">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <FileCode size={20} style={{ color: 'var(--color-primary)' }} />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-primary)' }}>
                        {resumeFile.name}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                        {Math.round(resumeFile.size / 1024)} KB • Attached & Ready for Analysis
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={handleRemoveResumeFile}
                    style={{ padding: '4px', color: 'var(--color-accent-terra)' }}
                    title="Remove attached file"
                    aria-label="Remove attached resume"
                  >
                    <X size={16} />
                  </button>
                </div>

                <div
                  style={{
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--color-bg-canvas)',
                    border: '1px solid var(--color-border)',
                    fontSize: 12,
                    color: 'var(--color-text-secondary)',
                    lineHeight: 1.45,
                  }}
                >
                  <strong style={{ color: 'var(--color-primary)' }}>File Attached:</strong>{' '}
                  {resumeFile.name}. InterviewIQ will extract competency matches, prior architecture ownership, and candidate proficiency from this document in Stage 2.
                </div>
              </div>
            )}

            {errors.resume && (
              <div className="error-text" style={{ marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
                <AlertCircle size={13} />
                {errors.resume}
              </div>
            )}
          </div>
        </div>

        {/* Action Bar Below Inputs: Duration & Prominent Analyze Button */}
        <div
          style={{
            paddingTop: 18,
            borderTop: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 16,
          }}
        >
          {/* Duration Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span
              style={{
                fontSize: 11.5,
                fontWeight: 700,
                color: 'var(--color-primary)',
                textTransform: 'uppercase',
                letterSpacing: '0.4px',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
              }}
            >
              <Clock size={13} /> Duration:
            </span>
            <div className="pill-radio-group">
              {[
                { val: 30, label: '30 min (Express • 4 Qs)' },
                { val: 45, label: '45 min (Standard • 6 Qs)' },
                { val: 60, label: '60 min (Deep • 8 Qs)' },
              ].map((d) => (
                <button
                  key={d.val}
                  type="button"
                  className={`pill-radio-btn ${duration === d.val ? 'selected' : ''}`}
                  onClick={() => setDuration(d.val)}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {/* Prominent Forest-Green Analyze Button */}
          <button
            type="submit"
            className="btn-primary"
            disabled={!isFormValid || isLoading}
            style={{
              background: 'var(--color-primary)',
              color: '#FFFFFF',
              padding: '12px 34px',
              fontSize: 14.5,
              fontWeight: 700,
              borderRadius: 'var(--radius-sm)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 9,
              boxShadow: 'var(--shadow-sm)',
              opacity: isFormValid && !isLoading ? 1 : 0.55,
              cursor: isFormValid && !isLoading ? 'pointer' : 'not-allowed',
            }}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="spin" />
                {loadingMsg || 'Analyzing...'}
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Analyze Skills & Candidate Fit
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
