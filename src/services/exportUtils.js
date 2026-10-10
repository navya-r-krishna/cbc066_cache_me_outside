/**
 * Utility functions for exporting InterviewIQ questions to CSV and JSON formats
 */

function sanitizeForCsv(text) {
  if (text === null || text === undefined) return '""';
  const str = String(text).replace(/"/g, '""');
  return `"${str}"`;
}

/**
 * Trigger download of a Blob file in browser
 */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

/**
 * Export questions array to CSV format
 */
export function exportToCsv(questions, filenamePrefix = 'interviewiq_questions') {
  if (!questions || questions.length === 0) {
    throw new Error('No questions available to export.');
  }

  const headers = [
    'Question ID',
    'Candidate Name',
    'Status',
    'Competency',
    'Difficulty',
    'Job Title',
    'Interview Question',
    'Why Relevant (Demo Rationale)',
    'Evaluation Rubric',
    'Follow-Up Probes',
    'Interviewer Notes',
    'Created Date',
  ];

  const rows = questions.map((q) => [
    sanitizeForCsv(q.id),
    sanitizeForCsv(q.candidateName || 'Candidate'),
    sanitizeForCsv(q.status ? q.status.toUpperCase() : 'PENDING'),
    sanitizeForCsv(q.competency),
    sanitizeForCsv(q.difficulty),
    sanitizeForCsv(q.jobTitle),
    sanitizeForCsv(q.question),
    sanitizeForCsv(q.whyRelevant),
    sanitizeForCsv(q.evaluationRubric),
    sanitizeForCsv(Array.isArray(q.followUps) ? q.followUps.join(' | ') : ''),
    sanitizeForCsv(q.interviewerNotes || ''),
    sanitizeForCsv(q.createdAt || new Date().toISOString()),
  ]);

  // Include UTF-8 BOM so Microsoft Excel renders characters correctly
  const csvContent = '\uFEFF' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\r\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const filename = `${filenamePrefix}_${timestamp}.csv`;

  downloadBlob(blob, filename);
  return { filename, count: questions.length };
}

/**
 * Export questions array to JSON format
 */
export function exportToJson(questions, filenamePrefix = 'interviewiq_questions') {
  if (!questions || questions.length === 0) {
    throw new Error('No questions available to export.');
  }

  const exportPayload = {
    generator: 'InterviewIQ AI Interview Generator',
    mode: 'Demo / Mock Data',
    exportedAt: new Date().toISOString(),
    totalQuestions: questions.length,
    questions: questions.map((q) => ({
      id: q.id,
      candidateName: q.candidateName || 'Candidate',
      jobTitle: q.jobTitle,
      competency: q.competency,
      difficulty: q.difficulty,
      status: q.status,
      question: q.question,
      whyRelevant: q.whyRelevant,
      evaluationRubric: q.evaluationRubric,
      followUps: q.followUps || [],
      interviewerNotes: q.interviewerNotes || '',
      createdAt: q.createdAt,
    })),
  };

  const jsonContent = JSON.stringify(exportPayload, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const filename = `${filenamePrefix}_${timestamp}.json`;

  downloadBlob(blob, filename);
  return { filename, count: questions.length };
}

/**
 * Specifically export only accepted questions
 */
export function exportAcceptedToCsv(questions, filenamePrefix = 'interviewiq_accepted_questions') {
  const accepted = (questions || []).filter((q) => q.status === 'accepted');
  if (accepted.length === 0) {
    throw new Error('No accepted questions to export. Please accept at least one question first.');
  }
  return exportToCsv(accepted, filenamePrefix);
}

export function exportAcceptedToJson(questions, filenamePrefix = 'interviewiq_accepted_questions') {
  const accepted = (questions || []).filter((q) => q.status === 'accepted');
  if (accepted.length === 0) {
    throw new Error('No accepted questions to export. Please accept at least one question first.');
  }
  return exportToJson(accepted, filenamePrefix);
}
