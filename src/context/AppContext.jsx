import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { INITIAL_MOCK_QUESTIONS, INITIAL_BATCHES } from '../services/mockData';
import { regenerateQuestion, getApiConfig, saveApiConfig } from '../services/api';

const AppContext = createContext(null);

const STORAGE_KEYS = {
  QUESTIONS: 'interviewiq_questions_v2',
  BATCHES: 'interviewiq_batches_v2',
  SETTINGS: 'interviewiq_settings_v2',
  PROFILE: 'interviewiq_profile_v2',
};

const DEFAULT_PROFILE = {
  name: 'Sarah Jenkins',
  email: 'sarah.jenkins@techflow.io',
  role: 'Staff Engineering Hiring Lead',
  company: 'TechFlow Systems',
  department: 'Platform & Infrastructure',
};

let toastCounter = 0;

export function AppProvider({ children }) {
  // Navigation State
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [globalSearch, setGlobalSearch] = useState('');

  // Profile Information State
  const [profile, setProfile] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.PROFILE);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.warn('Failed to load profile', e);
    }
    return DEFAULT_PROFILE;
  });

  // Questions and Batches State with LocalStorage persistence
  const [questions, setQuestions] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.QUESTIONS);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch (e) {
      console.warn('Failed to load questions from storage', e);
    }
    return [];
  });

  const [batches, setBatches] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.BATCHES);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch (e) {
      console.warn('Failed to load batches from storage', e);
    }
    return [];
  });

  const [activeBatchId, setActiveBatchId] = useState(INITIAL_BATCHES[0]?.id || null);

  // Settings State
  const [settings, setSettings] = useState(() => getApiConfig());

  // Toasts
  const [toasts, setToasts] = useState([]);

  // Sync to local storage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.QUESTIONS, JSON.stringify(questions));
    } catch (e) {
      console.error('Failed to sync questions to storage', e);
    }
  }, [questions]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.BATCHES, JSON.stringify(batches));
    } catch (e) {
      console.error('Failed to sync batches to storage', e);
    }
  }, [batches]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.PROFILE, JSON.stringify(profile));
    } catch (e) {
      console.error('Failed to sync profile to storage', e);
    }
  }, [profile]);

  // Workflow Wizard State (1. Input -> 2. Skills -> 3. Interview Plan -> 4. Final Kit)
  const [workflowStep, setWorkflowStep] = useState('input');
  const [workflowData, setWorkflowData] = useState({
    jobTitle: 'Senior Frontend Engineer (React & TypeScript)',
    jobDescription: '',
    candidateProfile: '',
    resumeFileName: null,
    duration: 45,
    difficulty: 'Auto',
    skills: [],
    weights: { technical: 50, experience: 35, academic: 15 },
    candidateSummary: null,
    lowInfo: false,
    generatedQuestions: [],
    batchId: null,
  });

  const updateWorkflowData = (patch) => {
    setWorkflowData((prev) => ({ ...prev, ...patch }));
  };

  const resetWorkflow = () => {
    setWorkflowStep('input');
    setWorkflowData({
      jobTitle: '',
      jobDescription: '',
      candidateProfile: '',
      resumeFileName: null,
      duration: 45,
      difficulty: 'Auto',
      skills: [],
      weights: { technical: 50, experience: 35, academic: 15 },
      candidateSummary: null,
      lowInfo: false,
      generatedQuestions: [],
      batchId: null,
    });
  };

  // Toast dispatcher
  const addToast = (toast) => {
    toastCounter++;
    const id = `toast-${toastCounter}-${Date.now()}`;
    const newToast = {
      id,
      type: toast.type || 'info', // 'success' | 'error' | 'warning' | 'info'
      title: toast.title || 'Notification',
      message: toast.message || '',
      duration: toast.duration || 4000,
    };

    setToasts((prev) => [...prev, newToast]);

    if (newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }
    return id;
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Question actions
  const acceptQuestion = (questionId) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === questionId ? { ...q, status: 'accepted', rejectionReason: null } : q))
    );
    setWorkflowData((prev) => ({
      ...prev,
      generatedQuestions: prev.generatedQuestions.map((q) =>
        q.id === questionId ? { ...q, status: 'accepted', rejectionReason: null } : q
      ),
    }));
    addToast({
      type: 'success',
      title: 'Question Accepted',
      message: 'Added to approved questions kit. Competency coverage updated.',
    });
  };

  const rejectQuestion = (questionId, reason = '') => {
    setQuestions((prev) =>
      prev.map((q) =>
        q.id === questionId
          ? {
              ...q,
              status: 'rejected',
              rejectionReason: reason || 'Flagged as low relevance or already evaluated',
            }
          : q
      )
    );
    setWorkflowData((prev) => ({
      ...prev,
      generatedQuestions: prev.generatedQuestions.map((q) =>
        q.id === questionId
          ? {
              ...q,
              status: 'rejected',
              rejectionReason: reason || 'Flagged as low relevance or already evaluated',
            }
          : q
      ),
    }));
    addToast({
      type: 'info',
      title: 'Question Rejected',
      message: 'Question marked as rejected and excluded from active sets.',
    });
  };

  const regenerateQuestionItem = async (questionId, hint = '') => {
    // Find in workflow questions or general questions
    const target =
      workflowData.generatedQuestions.find((q) => q.id === questionId) ||
      questions.find((q) => q.id === questionId);

    if (!target) return;

    try {
      addToast({
        type: 'info',
        title: 'Regenerating Question',
        message: hint ? `Refining prompt targeting "${hint}"...` : 'Synthesizing an alternative prompt locally...',
        duration: 1800,
      });

      const result = await regenerateQuestion(target, { hint });
      if (result.success && result.question) {
        setQuestions((prev) =>
          prev.map((q) => (q.id === questionId ? result.question : q))
        );
        setWorkflowData((prev) => ({
          ...prev,
          generatedQuestions: prev.generatedQuestions.map((q) =>
            q.id === questionId ? result.question : q
          ),
        }));
        addToast({
          type: 'success',
          title: 'Question Regenerated',
          message: hint ? `Prompt updated with hint: "${hint}"` : 'Alternative mock question created successfully.',
        });
      }
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Regeneration Failed',
        message: err.message,
      });
    }
  };

  const updateQuestionNotes = (questionId, notes) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === questionId ? { ...q, interviewerNotes: notes } : q))
    );
    addToast({
      type: 'success',
      title: 'Notes Saved',
      message: 'Interviewer evaluation notes updated.',
      duration: 2500,
    });
  };

  const deleteQuestion = (questionId) => {
    setQuestions((prev) => prev.filter((q) => q.id !== questionId));
    addToast({
      type: 'info',
      title: 'Question Removed',
      message: 'Question deleted from repository.',
    });
  };

  // Add a newly generated batch
  const addNewBatch = (batchMeta, newQuestions) => {
    const batchId = batchMeta.id || `batch-${Date.now().toString(36)}`;
    const candidateName = batchMeta.candidateName || 'Candidate';
    const questionsWithCandidate = newQuestions.map((q) => ({
      ...q,
      candidateName: q.candidateName || candidateName,
    }));
    const fullBatch = {
      ...batchMeta,
      id: batchId,
      createdAt: new Date().toISOString(),
      questionCount: newQuestions.length,
      acceptedCount: 0,
      rejectedCount: 0,
      pendingCount: newQuestions.length,
      status: 'Ready',
    };

    setBatches((prev) => [fullBatch, ...prev]);
    setQuestions((prev) => [...questionsWithCandidate, ...prev]);
    setActiveBatchId(batchId);
    return batchId;
  };

  const handleUpdateSettings = (newConfig) => {
    const merged = { ...settings, ...newConfig };
    setSettings(merged);
    saveApiConfig(merged);
    addToast({
      type: 'success',
      title: 'Settings Saved',
      message: 'Configuration parameters and default weights updated.',
    });
  };

  const handleUpdateProfile = (newProfile) => {
    const merged = { ...profile, ...newProfile };
    setProfile(merged);
    addToast({
      type: 'success',
      title: 'Profile Updated',
      message: 'Interviewer profile details saved locally.',
    });
  };

  const resetToMockDefaults = () => {
    setQuestions(INITIAL_MOCK_QUESTIONS);
    setBatches(INITIAL_BATCHES);
    setActiveBatchId(INITIAL_BATCHES[0]?.id || null);
    try {
      localStorage.removeItem(STORAGE_KEYS.QUESTIONS);
      localStorage.removeItem(STORAGE_KEYS.BATCHES);
    } catch (e) {
      console.warn(e);
    }
    addToast({
      type: 'info',
      title: 'Reset to Sample Data',
      message: 'Restored preloaded sample questions, roles, and batches.',
    });
  };

  // Derived statistics computed efficiently
  const stats = useMemo(() => {
    const total = questions.length;
    const accepted = questions.filter((q) => q.status === 'accepted').length;
    const rejected = questions.filter((q) => q.status === 'rejected').length;
    const pending = questions.filter((q) => q.status === 'pending' || !q.status).length;
    const acceptanceRate = total > 0 ? Math.round((accepted / total) * 100) : 0;

    const byCompetency = {};
    const byDifficulty = {
      Junior: 0,
      Mid: 0,
      Senior: 0,
      Staff: 0,
    };

    questions.forEach((q) => {
      // Competency count
      const comp = q.competency || 'General Technical';
      byCompetency[comp] = (byCompetency[comp] || 0) + 1;

      // Difficulty count
      const diff = q.difficulty || 'Senior';
      if (byDifficulty[diff] !== undefined) {
        byDifficulty[diff]++;
      } else {
        byDifficulty[diff] = 1;
      }
    });

    return {
      total,
      accepted,
      rejected,
      pending,
      acceptanceRate,
      byCompetency,
      byDifficulty,
    };
  }, [questions]);

  const value = {
    currentTab,
    setCurrentTab,
    globalSearch,
    setGlobalSearch,
    profile,
    updateProfile: handleUpdateProfile,
    questions,
    batches,
    activeBatchId,
    setActiveBatchId,
    stats,
    toasts,
    addToast,
    removeToast,
    acceptQuestion,
    rejectQuestion,
    regenerateQuestionItem,
    updateQuestionNotes,
    deleteQuestion,
    addNewBatch,
    settings,
    updateSettings: handleUpdateSettings,
    resetToMockDefaults,
    workflowStep,
    setWorkflowStep,
    workflowData,
    updateWorkflowData,
    resetWorkflow,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
