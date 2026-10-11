/**
 * InterviewIQ - Answer Evaluation & Comparison Utility
 * 
 * Compares candidate answers against expected original answers/rubrics
 * and allocates a transparent evaluation score.
 */

/**
 * Derives the clean expected answer / benchmark criteria for a question.
 */
export function getExpectedAnswer(question) {
  if (!question) return '';
  if (question.expectedAnswer) return question.expectedAnswer;
  if (question.expected_answer) return question.expected_answer;
  if (question.ideal_answer) return question.ideal_answer;
  
  // Use key_points if available from Backend B / Gemini
  if (Array.isArray(question.key_points) && question.key_points.length > 0) {
    return question.key_points.join('. ');
  }
  
  // Use evaluation rubric if available
  if (question.evaluationRubric) {
    return question.evaluationRubric.replace(/^Evaluates:\s*/i, '');
  }
  if (question.rubric) {
    return question.rubric.replace(/^Evaluates:\s*/i, '');
  }

  const skill = question.skillName || question.skill || question.competency || 'the target concept';
  return `A strong response demonstrates production expertise in ${skill}, detailing architectural trade-offs, runtime error handling, and telemetry monitoring strategies.`;
}

/**
 * Evaluates candidate answer against the question's expected answer.
 * Returns { score, answered, expectedAnswer, candidateAnswer, feedback, matchPercentage }
 */
export function evaluateCandidateAnswer(candidateAnswer, question) {
  const answerText = (candidateAnswer || '').trim();
  const expectedText = getExpectedAnswer(question);

  if (!answerText) {
    return {
      score: 0,
      answered: false,
      expectedAnswer: expectedText,
      candidateAnswer: '',
      feedback: 'No response provided by candidate.',
      matchPercentage: 0,
    };
  }

  // 1. Length & depth score (up to 40 points)
  const charLen = answerText.length;
  const depthScore = Math.min(40, Math.max(10, Math.round((charLen / 220) * 40)));

  // 2. Keyword & concept matching (up to 55 points)
  const sourceConcepts = [
    expectedText,
    question.question || question.text || '',
    question.skill || question.skillName || '',
    ...(Array.isArray(question.key_points) ? question.key_points : []),
  ].join(' ');

  const stopWords = new Set([
    'that', 'this', 'with', 'from', 'have', 'were', 'will', 'your', 'what',
    'when', 'where', 'which', 'their', 'there', 'about', 'would', 'could',
    'should', 'explain', 'detail', 'strong', 'candidate', 'covers', 'evaluates',
    'response', 'using', 'into', 'over', 'more', 'some', 'such', 'than', 'them',
    'then', 'these', 'they', 'very', 'also', 'most', 'only', 'interviewer',
    'listens', 'looks'
  ]);

  const rawWords = sourceConcepts.toLowerCase().match(/\b[a-z]{4,}\b/g) || [];
  const keyTokens = Array.from(new Set(rawWords.filter((w) => !stopWords.has(w))));

  const lowerCandidate = answerText.toLowerCase();
  let matches = 0;
  keyTokens.forEach((token) => {
    if (lowerCandidate.includes(token)) {
      matches++;
    }
  });

  const totalTokens = Math.max(1, Math.min(keyTokens.length, 12));
  const matchRatio = Math.min(1, matches / totalTokens);
  const matchScore = Math.round(matchRatio * 55);

  // Baseline credit for a written response
  const baseline = 12;
  const calculatedScore = Math.min(97, Math.max(30, baseline + matchScore + depthScore));

  let feedback = '';
  if (calculatedScore >= 85) {
    feedback = `High technical alignment (${matches} key concepts matched) with clear architectural depth.`;
  } else if (calculatedScore >= 70) {
    feedback = `Good coverage of core fundamentals; could expand on telemetry or edge-case handling.`;
  } else {
    feedback = `Introductory response; lacks deeper production and failure-isolation criteria.`;
  }

  return {
    score: calculatedScore,
    answered: true,
    expectedAnswer: expectedText,
    candidateAnswer: answerText,
    feedback,
    matchPercentage: Math.round(matchRatio * 100),
  };
}
