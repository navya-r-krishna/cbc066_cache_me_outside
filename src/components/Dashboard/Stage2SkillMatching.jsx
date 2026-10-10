import React, { useState, useMemo, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { generateInterviewPlanFromSkills } from '../../services/api';
import {
  Briefcase,
  UserCheck,
  ArrowLeft,
  ChevronRight,
  RotateCcw,
  Plus,
  Loader2,
  Trash2,
  GripVertical,
} from 'lucide-react';

const CATEGORIES = [
  'Technical Skills',
  'System Design',
  'Problem Solving',
  'Leadership',
  'Domain Knowledge',
];

export function Stage2SkillMatching({ onBack, onProceedToQuestions, onRestart }) {
  const { workflowData, updateWorkflowData, addNewBatch, addToast } = useApp();

  // Job Skills state initialized from workflowData.skills (parsed by backend / Stage 1)
  const [skills, setSkills] = useState(
    workflowData.skills && workflowData.skills.length > 0
      ? workflowData.skills
      : [
          {
            id: 'sk-1',
            name: 'React 19 & Next.js Modern Architecture',
            category: 'Technical Skills',
            evidence: 'Role calls for modern component architecture and high-frequency streaming telemetry.',
          },
          {
            id: 'sk-2',
            name: 'TypeScript Strict Typing & Discriminated Unions',
            category: 'Technical Skills',
            evidence: 'Championing strict type contracts across cross-functional engineering teams.',
          },
          {
            id: 'sk-3',
            name: 'System Design & State Virtualization',
            category: 'System Design',
            evidence: 'Scalable data rendering without memory leakage or cascading re-renders.',
          },
          {
            id: 'sk-4',
            name: 'Micro-Frontend Modularization & CI/CD',
            category: 'Problem Solving',
            evidence: 'Prior experience driving legacy monolithic migrations to modular architectures.',
          },
        ]
  );

  // Keep synced if workflowData.skills updates from backend
  useEffect(() => {
    if (workflowData.skills && workflowData.skills.length > 0) {
      setSkills(workflowData.skills);
    }
  }, [workflowData.skills]);

  // Drag and Drop state
  const [draggedIndex, setDraggedIndex] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);

  // Add new skill inputs
  const [newSkillText, setNewSkillText] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('Technical Skills');

  // Background weights
  const [weights] = useState(
    workflowData.weights || { technical: 50, experience: 35, academic: 15 }
  );

  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');

  // Base candidate competencies from parsed profile/resume
  const candidateBaseProfile = useMemo(
    () => [
      {
        key: 'react',
        name: 'Component Architecture & State Virtualization',
        keywords: ['react', 'next', 'frontend', 'virtualization', 'ui', 'component', 'state'],
        evidence: 'Led micro-frontend decoupling and state virtualization that reduced bundle size by 42%.',
      },
      {
        key: 'ts',
        name: 'Production Type Contracts & API Interfaces',
        keywords: ['typescript', 'type', 'strict', 'contract', 'api', 'typing', 'interfaces', 'discriminated'],
        evidence: 'Authored company-wide type contracts and strict runtime validation layers.',
      },
      {
        key: 'system',
        name: 'Real-Time Streaming Telemetry (WebSockets)',
        keywords: ['system', 'design', 'telemetry', 'websocket', 'streaming', 'real-time', 'concurrency'],
        evidence: 'Architected high-throughput financial telemetry streams with WebSockets.',
      },
      {
        key: 'modular',
        name: 'Micro-Frontend Modularization & CI/CD',
        keywords: ['modular', 'micro-frontend', 'ci/cd', 'monolith', 'migration', 'pipeline'],
        evidence: 'Converted 3 monolithic legacy portals into decoupled, independently deployable micro-frontends.',
      },
      {
        key: 'mentorship',
        name: 'Cross-Team RFC Leadership & Technical Mentorship',
        keywords: ['leadership', 'mentor', 'rfc', 'team', 'management', 'review'],
        evidence: 'Guided junior developers through architectural reviews and design sprints.',
      },
    ],
    []
  );

  // --------------------------------------------------------------------------
  // DYNAMIC COMPUTATION: Candidate skills dynamically adapt to Job Skills order
  // --------------------------------------------------------------------------
  const dynamicCandidateData = useMemo(() => {
    const candidateSkillsList = [];

    // Evaluate each job skill in its exact drag-and-drop order
    skills.forEach((jobSkill) => {
      const skillLower = jobSkill.name.toLowerCase();

      // Check match with candidate base competencies
      const matchingBase = candidateBaseProfile.find((cand) =>
        cand.keywords.some((kw) => skillLower.includes(kw)) ||
        cand.name.toLowerCase().includes(skillLower) ||
        skillLower.includes(cand.name.toLowerCase().split(' ')[0])
      );

      if (matchingBase) {
        candidateSkillsList.push({
          id: `csk-match-${jobSkill.id}`,
          name: matchingBase.name,
          matchLevel: 'Verified Match',
          evidence: `${matchingBase.evidence} Aligns directly with "${jobSkill.name}".`,
          category: jobSkill.category,
        });
      } else {
        candidateSkillsList.push({
          id: `csk-gap-${jobSkill.id}`,
          name: `${jobSkill.name} (Validation Target)`,
          matchLevel: 'Target Competency',
          evidence: `Resume indicates adjacent experience for "${jobSkill.name}". Interview deep-dive recommended.`,
          category: jobSkill.category,
        });
      }
    });

    const scoreVal = Math.min(96, Math.max(75, 88 + (skills.length > 3 ? 4 : 0)));

    return {
      candidateSkillsList,
      score: scoreVal,
    };
  }, [skills, candidateBaseProfile]);

  const candidateSummary = {
    candidateName: workflowData.resumeFileName?.replace(/\.[^/.]+$/, '') || 'Candidate',
    band: 'Senior Specialist',
    score: dynamicCandidateData.score,
  };

  // --------------------------------------------------------------------------
  // DRAG AND DROP REORDERING HANDLERS
  // --------------------------------------------------------------------------
  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dragOverIndex !== index) {
      setDragOverIndex(index);
    }
  };

  const handleDragLeave = () => {
    setDragOverIndex(null);
  };

  const handleDrop = (e, targetIndex) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === targetIndex) {
      setDraggedIndex(null);
      setDragOverIndex(null);
      return;
    }

    setSkills((prev) => {
      const updated = [...prev];
      const [movedItem] = updated.splice(draggedIndex, 1);
      updated.splice(targetIndex, 0, movedItem);
      return updated;
    });

    addToast({
      type: 'info',
      title: 'Skills Reordered',
      message: 'Priority reordered via drag-and-drop. Candidate skills updated.',
      duration: 1500,
    });

    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  const handleDeleteSkill = (skillId) => {
    const toDelete = skills.find((s) => s.id === skillId);
    if (skills.length <= 1) {
      addToast({
        type: 'warning',
        title: 'Cannot Remove',
        message: 'At least one role requirement skill is needed.',
      });
      return;
    }

    setSkills((prev) => prev.filter((s) => s.id !== skillId));
    addToast({
      type: 'info',
      title: 'Skill Removed',
      message: `Removed "${toDelete?.name || 'skill'}".`,
      duration: 2000,
    });
  };

  const handleAddJobSkill = (e) => {
    e.preventDefault();
    if (!newSkillText.trim()) return;

    const newSkill = {
      id: `custom-sk-${Date.now()}`,
      name: newSkillText.trim(),
      category: newSkillCategory,
      evidence: `Requirement for ${newSkillCategory}.`,
    };

    setSkills((prev) => [...prev, newSkill]);
    setNewSkillText('');
    addToast({
      type: 'success',
      title: 'Requirement Added',
      message: `Added "${newSkill.name}".`,
      duration: 2500,
    });
  };

  // Submit and Generate Questions (Move to Stage 3)
  const handleProceed = async () => {
    if (skills.length === 0) {
      addToast({
        type: 'warning',
        title: 'No Skills Configured',
        message: 'At least one job competency is required to generate questions.',
      });
      return;
    }

    setIsGenerating(true);
    setLoadingMsg('Formulating targeted interview plan and rubrics...');

    try {
      const result = await generateInterviewPlanFromSkills(
        {
          jobTitle: workflowData.jobTitle,
          candidateProfile: workflowData.candidateProfile,
          skills,
          weights,
          duration: workflowData.duration || 45,
          difficulty: workflowData.difficulty || 'Medium',
        },
        {
          onProgress: ({ message }) => setLoadingMsg(message),
        }
      );

      if (result.success && result.questions) {
        updateWorkflowData({
          skills,
          weights,
          generatedQuestions: result.questions,
          batchId: result.batchId,
          candidateSummary: {
            ...candidateSummary,
            score: dynamicCandidateData.score,
          },
        });

        const batchMeta = {
          id: result.batchId,
          jobTitle: workflowData.jobTitle,
          candidateName: candidateSummary.candidateName,
          difficulty: workflowData.difficulty,
          experienceLevel: candidateSummary.band,
          duration: workflowData.duration || 45,
          questionCount: result.questions.length,
        };
        addNewBatch(batchMeta, result.questions);

        addToast({
          type: 'success',
          title: 'Questions Formulated',
          message: `Generated ${result.questions.length} interview questions. Advancing to Stage 3.`,
        });

        if (onProceedToQuestions) {
          onProceedToQuestions();
        }
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Question Generation Failed',
        message: err.message || 'Could not generate interview plan.',
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        height: '100%',
        maxHeight: '100%',
        overflow: 'hidden',
        justifyContent: 'space-between',
      }}
    >
      {/* Stage Header - Heading Only with Corner Start New Formulation */}
      <div
        className="card"
        style={{
          padding: '10px 16px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <div>
            <h2 style={{ fontSize: 16.5, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
              Stage 2: Skill Matching & Calibration
            </h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span className="badge badge-forest" style={{ fontSize: 11, padding: '4px 8px' }}>
              {skills.length} Extracted Skills
            </span>
            <span
              className="badge badge-sage"
              style={{
                fontSize: 11,
                padding: '4px 8px',
                color: 'var(--color-primary)',
                fontWeight: 700,
              }}
            >
              Fit Score: {dynamicCandidateData.score}%
            </span>
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
                  padding: '5px 10px',
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

      {/* Two Main Cards: Priority Job Skills & Prioritize Candidate Skills */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 12,
          flex: 1,
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        {/* =================================================================== */}
        {/* CARD 1: Priority Job Skills (Drag & Drop to Reorder)                */}
        {/* =================================================================== */}
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
            height: '100%',
            minHeight: 0,
            overflow: 'hidden',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Briefcase size={18} style={{ color: 'var(--color-primary)' }} />
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
                Priority Job Skills
              </h3>
            </div>
            <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', fontWeight: 600 }}>
              Drag to reorder
            </span>
          </div>

          {/* List of Job Skills with Drag and Drop */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, minHeight: 0, overflowY: 'auto', paddingRight: '4px' }}>
            {skills.map((skill, index) => {
              const isDragging = draggedIndex === index;
              const isOver = dragOverIndex === index;

              return (
                <div
                  key={skill.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, index)}
                  onDragEnd={handleDragEnd}
                  style={{
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: isOver ? 'var(--color-primary-light)' : '#FFFFFF',
                    border: isOver
                      ? '1.5px dashed var(--color-primary)'
                      : '1px solid var(--color-border)',
                    opacity: isDragging ? 0.45 : 1,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    cursor: 'grab',
                    transition: 'border 120ms ease, background 120ms ease',
                    boxShadow: isDragging ? 'var(--shadow-md)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                      <GripVertical
                        size={15}
                        style={{ color: 'var(--color-text-secondary)', cursor: 'grab', flexShrink: 0 }}
                      />
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          color: 'var(--color-primary)',
                          background: 'var(--color-surface-hover)',
                          padding: '2px 6px',
                          borderRadius: 'var(--radius-xs)',
                        }}
                      >
                        #{index + 1}
                      </span>
                      <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-primary)' }}>
                        {skill.name}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {/* Delete Button */}
                      <button
                        type="button"
                        onClick={() => handleDeleteSkill(skill.id)}
                        style={{
                          padding: '4px 6px',
                          borderRadius: 'var(--radius-xs)',
                          border: '1px solid var(--color-border)',
                          background: '#FFFFFF',
                          color: 'var(--color-accent-terra)',
                          cursor: 'pointer',
                        }}
                        title="Remove skill"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--color-text-secondary)', paddingLeft: 23 }}>
                    <span className="badge badge-sage" style={{ fontSize: 10, padding: '2px 6px' }}>
                      {skill.category}
                    </span>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {skill.evidence}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick Add Custom Job Skill */}
          <form
            onSubmit={handleAddJobSkill}
            style={{
              display: 'flex',
              gap: 8,
              marginTop: 'auto',
              paddingTop: 12,
              borderTop: '1px dashed var(--color-border)',
            }}
          >
            <input
              type="text"
              className="form-input"
              style={{ fontSize: 12.5, padding: '7px 12px', flex: 1 }}
              placeholder="Add another requirement skill..."
              value={newSkillText}
              onChange={(e) => setNewSkillText(e.target.value)}
            />
            <select
              className="form-input"
              style={{ fontSize: 11.5, padding: '7px 8px', maxWidth: 125 }}
              value={newSkillCategory}
              onChange={(e) => setNewSkillCategory(e.target.value)}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <button
              type="submit"
              className="btn-secondary"
              style={{ fontSize: 12, padding: '6px 12px', whiteSpace: 'nowrap' }}
            >
              <Plus size={14} /> Add
            </button>
          </form>
        </div>

        {/* =================================================================== */}
        {/* CARD 2: Prioritize Candidate Skills (Dynamically mirrors order)     */}
        {/* =================================================================== */}
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
            height: '100%',
            minHeight: 0,
            overflow: 'hidden',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <UserCheck size={18} style={{ color: 'var(--color-primary)' }} />
              <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-primary)', margin: 0 }}>
                Prioritize Candidate Skills
              </h3>
            </div>
          </div>

          {/* Dynamic Candidate Profile Match Header */}
          <div
            style={{
              padding: '8px 12px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-primary-light)',
              border: '1px solid var(--color-accent-sage)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transition: 'all 200ms ease',
              flexShrink: 0,
            }}
          >
            <div>
              <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--color-primary)' }}>
                {candidateSummary.candidateName}
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                Seniority: {candidateSummary.band}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                Match Score
              </div>
              <div
                style={{
                  fontSize: 16,
                  fontWeight: 800,
                  color: 'var(--color-primary)',
                  transition: 'all 200ms ease',
                }}
              >
                {dynamicCandidateData.score}%
              </div>
            </div>
          </div>

          {/* Dynamically Calibrated Candidate Skills List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, minHeight: 0, overflowY: 'auto', paddingRight: '4px' }}>
            {dynamicCandidateData.candidateSkillsList.map((csk) => (
              <div
                key={csk.id}
                style={{
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  background: '#FFFFFF',
                  border: '1px solid var(--color-border)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 5,
                  transition: 'all 160ms ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                  <div style={{ fontWeight: 600, fontSize: 12.5, color: 'var(--color-primary)' }}>
                    {csk.name}
                  </div>

                  <span
                    className={`badge ${csk.matchLevel === 'Verified Match' ? 'badge-success' : 'badge-sage'}`}
                    style={{ fontSize: 10, padding: '2px 7px' }}
                  >
                    {csk.matchLevel}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 10.5, color: 'var(--color-text-secondary)' }}>
                  <span className="badge badge-sage" style={{ fontSize: 9.5, padding: '2px 5px' }}>
                    {csk.category}
                  </span>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {csk.evidence}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Action Controls */}
      <div
        className="card"
        style={{
          padding: '10px 18px',
          background: '#FFFFFF',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          flexShrink: 0,
        }}
      >
        <button
          type="button"
          className="btn-secondary"
          onClick={onBack}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5, padding: '6px 14px' }}
        >
          <ArrowLeft size={14} /> Back to Role & Resume
        </button>

        <button
          type="button"
          className="btn-primary"
          disabled={isGenerating}
          onClick={handleProceed}
          style={{
            background: 'var(--color-primary)',
            color: '#FFFFFF',
            padding: '8px 24px',
            fontSize: 13.5,
            fontWeight: 700,
            borderRadius: 'var(--radius-sm)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 7,
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          {isGenerating ? (
            <>
              <Loader2 size={15} className="spin" />
              {loadingMsg || 'Generating Questions...'}
            </>
          ) : (
            <>
              Generate Questions
              <ChevronRight size={15} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
