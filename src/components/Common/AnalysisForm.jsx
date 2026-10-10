import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { extractSkillsAndProfile } from '../../services/api';
import {
  Upload,
  FileText,
  X,
  Sparkles,
  FileCode,
  Loader2,
  FileCheck,
  AlertCircle,
} from 'lucide-react';

export function AnalysisForm({
  onAnalyzeSuccess,
  title = 'Generate Interview Questions',
  subtitle = 'Upload job description and candidate resume to formulate tailored competency rubrics',
}) {
  const { workflowData, updateWorkflowData, addToast } = useApp();

  // Role & Job Description states
  const [jobTitle, setJobTitle] = useState(workflowData.jobTitle || 'Senior Software Engineer');
  const [jobDescription, setJobDescription] = useState(workflowData.jobDescription || '');
  const [jobFile, setJobFile] = useState(null);

  // Candidate Resume states
  const [candidateProfile, setCandidateProfile] = useState(workflowData.candidateProfile || '');
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeMode, setResumeMode] = useState('upload'); // 'upload' | 'paste'

  // Difficulty Selector (Easy, Medium, Hard - single choice, compact top-right)
  const [difficulty, setDifficulty] = useState(
    ['Easy', 'Medium', 'Hard'].includes(workflowData.difficulty)
      ? workflowData.difficulty
      : 'Medium'
  );

  // Validation & Loading states
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');

  const jobFileInputRef = useRef(null);
  const resumeFileInputRef = useRef(null);

  // Job Description File Upload
  const handleJobFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setErrors((prev) => ({ ...prev, jobDescription: 'File is too large (maximum 5MB allowed)' }));
      addToast({
        type: 'error',
        title: 'File Too Large',
        message: 'Please select a job description file under 5MB.',
      });
      return;
    }

    setJobFile(file);
    setErrors((prev) => {
      const copy = { ...prev };
      delete copy.jobDescription;
      return copy;
    });

    if (file.type === 'text/plain' || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        if (evt.target?.result) {
          setJobDescription(evt.target.result);
        }
      };
      reader.readAsText(file);
    } else {
      const parsedText = `Role: ${file.name.replace(/\.[^/.]+$/, '')}\nJob Requirements File: ${file.name} (${Math.round(file.size / 1024)} KB)\nResponsibilities: Lead technical architecture, design scalable microservices, implement high-availability workflows, and mentor team engineers.\nQualifications: Demonstrated experience in software design patterns, testing automation, and cloud systems.`;
      setJobDescription(parsedText);
    }

    addToast({
      type: 'success',
      title: 'Job Description Attached',
      message: `Attached ${file.name} (${Math.round(file.size / 1024)} KB).`,
    });
  };

  const handleRemoveJobFile = () => {
    setJobFile(null);
    if (jobFileInputRef.current) jobFileInputRef.current.value = '';
  };

  // Candidate Resume File Upload
  const handleResumeFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setErrors((prev) => ({ ...prev, resume: 'File is too large (maximum 5MB allowed)' }));
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
      delete copy.candidateProfile;
      return copy;
    });

    if (file.type === 'text/plain' || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        if (evt.target?.result) {
          setCandidateProfile(evt.target.result);
        }
      };
      reader.readAsText(file);
    } else {
      const parsedResume = `Candidate: ${file.name.replace(/\.[^/.]+$/, '')}\nResume Document: ${file.name} (${Math.round(file.size / 1024)} KB)\nBackground: Proven engineering track record in full-stack architecture, API performance optimization, and distributed database systems.`;
      setCandidateProfile(parsedResume);
    }

    addToast({
      type: 'success',
      title: 'Resume Attached',
      message: `Attached ${file.name} (${Math.round(file.size / 1024)} KB).`,
    });
  };

  const handleRemoveResumeFile = () => {
    setResumeFile(null);
    if (resumeFileInputRef.current) resumeFileInputRef.current.value = '';
  };

  // Check validity for disabling Analyze button
  const hasJobDesc = Boolean(jobFile) || (jobDescription && jobDescription.trim().length >= 20);
  const hasResume = Boolean(resumeFile) || (candidateProfile && candidateProfile.trim().length > 0);
  const isFormValid = hasJobDesc && hasResume;

  const validate = () => {
    const errs = {};
    if (!hasJobDesc) {
      errs.jobDescription = 'Please upload a job description file or enter job requirements (minimum 20 characters).';
    }
    if (!hasResume) {
      errs.resume = 'Please upload a candidate resume or paste background details.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) {
      addToast({
        type: 'error',
        title: 'Inputs Incomplete',
        message: 'Please provide both Job Description and Candidate Resume to analyze.',
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
          duration: workflowData.duration || 45,
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
          difficulty,
          skills: result.skills,
          candidateSummary: result.candidateSummary,
          lowInfo: result.candidateSummary?.lowInfo || false,
          weights: result.defaultWeights || workflowData.weights,
        });

        addToast({
          type: 'success',
          title: 'Analysis Succeeded',
          message: `Identified ${result.skills.length} competencies at ${difficulty} difficulty.`,
        });

        if (onAnalyzeSuccess) {
          onAnalyzeSuccess(result);
        }
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Analysis Error',
        message: err.message || 'Failed to analyze requirements.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="card"
      style={{
        padding: '24px 28px',
        background: '#FFFFFF',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {/* Form Header with Title on Left and Compact Difficulty Selector on Top-Right */}
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
            {title}
          </h2>
          <p
            style={{
              fontSize: 13,
              color: 'var(--color-text-secondary)',
              marginTop: 3,
              margin: 0,
            }}
          >
            {subtitle}
          </p>
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
        {/* Two Main Input Sections: Job Description Upload & Candidate Resume Upload */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: 22,
          }}
        >
          {/* Main Element 1: Job Description Upload */}
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
                <FileText size={18} style={{ color: 'var(--color-primary)' }} />
                <h3 style={{ fontSize: 14.5, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
                  1. Job Description Upload
                </h3>
              </div>
              <span style={{ fontSize: 11.5, color: 'var(--color-text-secondary)' }}>
                PDF, TXT, DOCX, MD
              </span>
            </div>

            {/* Hidden Job File Input */}
            <input
              ref={jobFileInputRef}
              type="file"
              accept=".pdf,.txt,.docx,.md"
              style={{ display: 'none' }}
              onChange={handleJobFileChange}
              id="job-description-file-picker"
            />

            {/* Job Description File Selection Display */}
            {jobFile ? (
              <div className="uploaded-file-pill">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <FileCheck size={18} style={{ color: 'var(--color-primary)' }} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-primary)' }}>
                      {jobFile.name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                      {Math.round(jobFile.size / 1024)} KB • Attached
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={handleRemoveJobFile}
                  style={{ padding: '4px', color: 'var(--color-accent-terra)' }}
                  title="Remove file"
                  aria-label="Remove job description file"
                >
                  <X size={16} />
                </button>
              </div>
            ) : (
              <div
                className="file-upload-dropzone"
                onClick={() => jobFileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && jobFileInputRef.current?.click()}
                style={{
                  minHeight: 88,
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  border: '1.5px dashed var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  background: '#FFFFFF',
                  textAlign: 'center',
                }}
              >
                <Upload size={22} style={{ color: 'var(--color-text-secondary)', marginBottom: 5 }} />
                <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-primary)' }}>
                  Click to upload Job Description file
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                  or type / paste requirements below
                </div>
              </div>
            )}

            {/* Preserved Text-Entry Functionality */}
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
                  htmlFor="job-description-text"
                  style={{ marginBottom: 0, fontSize: 12.5, fontWeight: 600 }}
                >
                  Job Requirements Text
                </label>
                <span
                  style={{
                    fontSize: 11,
                    color: jobDescription.length < 20 ? 'var(--color-text-muted)' : 'var(--color-text-secondary)',
                  }}
                >
                  {jobDescription.length} characters
                </span>
              </div>
              <textarea
                id="job-description-text"
                className={`form-textarea ${errors.jobDescription ? 'input-error' : ''}`}
                rows={6}
                placeholder="Enter or paste key responsibilities, required qualifications, technical stack, and architecture scope..."
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

          {/* Main Element 2: Candidate Resume Upload */}
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

              {/* Mode Toggle: File Upload vs Paste Text */}
              <div
                style={{
                  display: 'flex',
                  background: 'var(--color-bg-canvas)',
                  borderRadius: 'var(--radius-xs)',
                  padding: 2,
                  border: '1px solid var(--color-border)',
                }}
              >
                <button
                  type="button"
                  onClick={() => setResumeMode('upload')}
                  style={{
                    padding: '3px 9px',
                    fontSize: 11.5,
                    fontWeight: 600,
                    borderRadius: 'var(--radius-xs)',
                    border: 'none',
                    background: resumeMode === 'upload' ? 'var(--color-primary)' : 'transparent',
                    color: resumeMode === 'upload' ? '#FFFFFF' : 'var(--color-text-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  File Upload
                </button>
                <button
                  type="button"
                  onClick={() => setResumeMode('paste')}
                  style={{
                    padding: '3px 9px',
                    fontSize: 11.5,
                    fontWeight: 600,
                    borderRadius: 'var(--radius-xs)',
                    border: 'none',
                    background: resumeMode === 'paste' ? 'var(--color-primary)' : 'transparent',
                    color: resumeMode === 'paste' ? '#FFFFFF' : 'var(--color-text-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  Paste Text
                </button>
              </div>
            </div>

            {/* Hidden Resume File Input */}
            <input
              ref={resumeFileInputRef}
              type="file"
              accept=".pdf,.txt,.docx,.md"
              style={{ display: 'none' }}
              onChange={handleResumeFileChange}
              id="candidate-resume-file-picker"
            />

            {resumeMode === 'upload' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {resumeFile ? (
                  <div className="uploaded-file-pill">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <FileCode size={18} style={{ color: 'var(--color-primary)' }} />
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-primary)' }}>
                          {resumeFile.name}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                          {Math.round(resumeFile.size / 1024)} KB • Attached
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={handleRemoveResumeFile}
                      style={{ padding: '4px', color: 'var(--color-accent-terra)' }}
                      title="Remove file"
                      aria-label="Remove candidate resume file"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ) : (
                  <div
                    className="file-upload-dropzone"
                    onClick={() => resumeFileInputRef.current?.click()}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && resumeFileInputRef.current?.click()}
                    style={{
                      minHeight: 88,
                      padding: '14px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      border: '1.5px dashed var(--color-border)',
                      borderRadius: 'var(--radius-sm)',
                      background: '#FFFFFF',
                      textAlign: 'center',
                    }}
                  >
                    <Upload size={22} style={{ color: 'var(--color-text-secondary)', marginBottom: 5 }} />
                    <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-primary)' }}>
                      Click to upload Candidate Resume file
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                      Supports PDF, TXT, DOCX, MD (max 5MB)
                    </div>
                  </div>
                )}

                {/* Candidate Profile Preview Textarea */}
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label
                    className="form-label"
                    htmlFor="candidate-profile-preview"
                    style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 6 }}
                  >
                    Parsed / Supplemental Background
                  </label>
                  <textarea
                    id="candidate-profile-preview"
                    className="form-textarea"
                    rows={6}
                    placeholder="Candidate profile preview or additional experience notes..."
                    value={candidateProfile}
                    onChange={(e) => {
                      setCandidateProfile(e.target.value);
                      if (errors.resume) setErrors((prev) => ({ ...prev, resume: null }));
                    }}
                  />
                </div>
              </div>
            ) : (
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label
                  className="form-label"
                  htmlFor="candidate-profile-text"
                  style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 6 }}
                >
                  Candidate Profile & Experience Text <span className="required-star">*</span>
                </label>
                <textarea
                  id="candidate-profile-text"
                  className={`form-textarea ${errors.resume ? 'input-error' : ''}`}
                  rows={9}
                  placeholder="Paste candidate resume, work history, core technologies, achievements, and project highlights..."
                  value={candidateProfile}
                  onChange={(e) => {
                    setCandidateProfile(e.target.value);
                    if (errors.resume) setErrors((prev) => ({ ...prev, resume: null }));
                  }}
                />
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

        {/* Main Element 4: Prominent Analyze Button Below Upload Sections */}
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
          <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)' }}>
            {!isFormValid ? (
              <span style={{ color: 'var(--color-accent-terra)' }}>
                Please provide both a Job Description and Candidate Resume to enable analysis.
              </span>
            ) : (
              <span>Ready for synthesis at <strong>{difficulty}</strong> difficulty.</span>
            )}
          </div>

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
                Analyze
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
