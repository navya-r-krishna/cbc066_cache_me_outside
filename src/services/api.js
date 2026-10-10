/**
 * InterviewIQ API Service Layer
 * 
 * Separated architecture for future FastAPI backend integration.
 * Currently defaults to Mock Engine with local question synthesis.
 * Clearly labeled mock dataset for demonstration and local development.
 * 
 * Future FastAPI Endpoints expected:
 *   POST /api/v1/generate-questions
 *   POST /api/v1/regenerate-question
 *   GET  /api/v1/health
 */

const DEFAULT_CONFIG = {
  apiBaseUrl: 'http://localhost:8000/api/v1',
  useMockApi: true,
  simulatedDelayMs: 1200,
  defaultDifficulty: 'Senior',
  defaultQuestionCount: 6,
  defaultWeights: {
    technical: 50,
    experience: 35,
    academic: 15,
  },
};

// Retrieve runtime config
export function getApiConfig() {
  try {
    const saved = localStorage.getItem('interviewiq_settings');
    if (saved) {
      return { ...DEFAULT_CONFIG, ...JSON.parse(saved) };
    }
  } catch (e) {
    console.warn('Could not read settings from localStorage, using defaults', e);
  }
  return DEFAULT_CONFIG;
}

export function saveApiConfig(newConfig) {
  try {
    localStorage.setItem('interviewiq_settings', JSON.stringify(newConfig));
  } catch (e) {
    console.error('Failed to save API config', e);
  }
}

/**
 * Local Mock Question Synthesizer
 * Synthesizes mock questions locally with demo rationales and rubrics.
 * Clearly tagged as mock/demo data.
 */
function synthesizeMockQuestions({
  jobTitle = 'Software Engineer',
  jobDescription: _jobDescription,
  candidateProfile: _candidateProfile,
  experienceLevel = 'Senior (6-8 yrs)',
  difficulty = 'Senior',
  questionCount = 6,
  weights = { technical: 50, experience: 35, academic: 15 },
  competencies = [],
}) {
  const batchId = `batch-${Date.now().toString(36)}`;
  const defaultCompetencies = [
    'Technical Skills',
    'Problem Solving',
    'Behavioural Skills',
    'System Design',
  ];

  const targetCompetencies = competencies.length > 0 ? competencies : defaultCompetencies;
  const questions = [];

  // Question templates bank categorized by competency
  const bank = {
    'Technical Skills': [
      {
        q: (title) =>
          `In your primary tech stack for ${title}, how do you manage memory lifecycle, prevent goroutine/thread leaks, and monitor connection pool starvation in long-running services?`,
        why: (title, exp, w) =>
          `[Demo Rationale] Evaluates concrete language runtime depth for ${title} at ${exp} level based on Technical Skills weight of ${w.technical}%.`,
        rubric:
          'Evaluates: Deep understanding of runtime internals (event loop / memory allocation / connection pool checkout), heap dumps, and connection timeouts.',
        followUps: [
          'What tools do you use to capture production heap dumps with minimal performance overhead?',
          'How do you tune TCP keepalive and connection reuse across microservices?',
        ],
      },
      {
        q: (title) =>
          `How would you design a strongly-typed schema validation and serialization layer for ${title} that guards against malformed payloads and injection before hitting business logic?`,
        why: (title, exp, w) =>
          `[Demo Rationale] Measures defensive API contract hygiene and strong type-safety discipline (Weighted: ${w.technical}%).`,
        rubric:
          'Evaluates: Runtime validation schemas (Zod / Pydantic), type inference, rate limiting, and parameter sanitization.',
        followUps: [
          'How do you manage backward compatibility when deprecating required contract fields?',
        ],
      },
      {
        q: (title) =>
          `Explain how you handle concurrency, optimistic vs. pessimistic locking, and race conditions during high-volume transactional mutations in ${title}.`,
        why: (title, exp, w) =>
          `[Demo Rationale] Assesses technical rigor in handling concurrent state changes safely under load (Technical Weight: ${w.technical}%).`,
        rubric:
          'Evaluates: Isolation levels (SERIALIZABLE vs REPEATABLE READ), atomic CAS operations, distributed redis locks, or event queues.',
        followUps: [
          'When would you deliberately choose optimistic concurrency over database record locks?',
        ],
      },
    ],
    'Problem Solving': [
      {
        q: () =>
          `Users report that search and analytics endpoints are experiencing intermittent 3-second latency spikes during peak traffic hours. Walk through your systematic root-cause investigation steps.`,
        why: (title, exp, w) =>
          `[Demo Rationale] Tests hypothesis-driven debugging and performance triage at ${exp} level (Technical: ${w.technical}%, Experience: ${w.experience}%).`,
        rubric:
          'Evaluates: Structured diagnostic methodology, distributed tracing (OpenTelemetry), query explain plans (seq scans vs index scans), and database lock contention checks.',
        followUps: [
          'If application metrics show normal CPU/RAM, what operating system or network metrics would you inspect next?',
        ],
      },
      {
        q: () =>
          `Suppose you need to compute 24-hour rolling unique visitor metrics across 50 million daily records with strict memory constraints. What algorithmic data structures would you consider?`,
        why: (title, exp, w) =>
          `[Demo Rationale] Evaluates algorithmic problem solving and memory trade-offs (Academic: ${w.academic}%, Technical: ${w.technical}%).`,
        rubric:
          'Evaluates: HyperLogLog probabilistic cardinality counting, Redis bitmaps, sliding window time-buckets, and error tolerance understanding.',
        followUps: [
          'How would you explain the 1-2% probabilistic error margin of HyperLogLog to non-technical stakeholders?',
        ],
      },
    ],
    'Behavioural Skills': [
      {
        q: () =>
          `Tell me about a time when business priorities demanded a rapid delivery deadline that conflicted with your architectural standards or technical debt threshold. How did you negotiate?`,
        why: (title, exp, w) =>
          `[Demo Rationale] Measures pragmatic engineering leadership and cross-functional communication based on Relevant Experience weight of ${w.experience}%.`,
        rubric:
          'Evaluates: Articulating business risk of tech debt, proposing phased rollout or MVP compromises, and documenting future remediation objectively.',
        followUps: [
          'Did that technical debt ever get repaid? What was your plan to ensure it was prioritized on the product roadmap?',
        ],
      },
      {
        q: () =>
          `Describe a situation where a critical regression made it past code review and automated CI into production. How did you lead the post-mortem without assigning blame?`,
        why: (title, exp, w) =>
          `[Demo Rationale] Assesses blameless post-mortem culture and systemic prevention mindset (Experience: ${w.experience}%).`,
        rubric:
          'Evaluates: Focus on process/tooling failure rather than human error, actionable preventive measures (guardrails, synthetic monitors, canary deployments).',
        followUps: [
          'How do you balance adding guardrails with keeping engineering velocity fast?',
        ],
      },
    ],
    'System Design': [
      {
        q: (title) =>
          `How would you architect a fault-tolerant, horizontally scalable service for ${title} handling unexpected 10x traffic spikes while maintaining sub-100ms p99 latency?`,
        why: (title, exp, w) =>
          `[Demo Rationale] Validates high-scale architectural design depth at ${exp} level (Technical: ${w.technical}%, Experience: ${w.experience}%).`,
        rubric:
          'Evaluates: Caching layers (Redis), backpressure/load-shedding, asynchronous message queues, database indexing and read replicas, and circuit-breaker patterns.',
        followUps: [
          'What telemetry metrics would trigger an automated fallback degradation?',
          'How do you prevent cache stampedes during sudden traffic bursts?',
        ],
      },
      {
        q: () =>
          `Design an idempotent event consumer pipeline handling 50M events per day with Kafka and PostgreSQL, guaranteeing exactly-once semantics during network partitions.`,
        why: (title, exp, w) =>
          `[Demo Rationale] Validates distributed systems architecture, state consensus, and deduplication keys (Experience: ${w.experience}%).`,
        rubric:
          'Evaluates: Transactional outbox pattern, deduplication key storage, idempotent consumer design, and dead-letter queues.',
        followUps: [
          'What happens if the deduplication cache in Redis fails or evicts keys under memory pressure?',
        ],
      },
    ],
  };

  let count = 0;
  let compIndex = 0;

  while (count < questionCount) {
    const comp = targetCompetencies[compIndex % targetCompetencies.length];
    const compPool = bank[comp] || bank['Technical Skills'];
    const template = compPool[count % compPool.length];

    const questionText = template.q(jobTitle);
    const whyText = template.why(jobTitle, experienceLevel, weights);
    const rubricText = template.rubric;
    const followUps = template.followUps;

    questions.push({
      id: `iq-${Date.now().toString(36)}-${count + 1}`,
      batchId,
      jobTitle,
      competency: comp,
      difficulty,
      experienceLevel,
      question: questionText,
      whyRelevant: whyText,
      evaluationRubric: rubricText,
      followUps,
      status: 'pending',
      createdAt: new Date(Date.now() + count * 1000).toISOString(),
      interviewerNotes: '',
    });

    count++;
    compIndex++;
  }

  return questions;
}

/**
 * Generate Questions API
 * Coordinates with mock engine or future FastAPI endpoint
 */
export async function generateQuestions(payload, { onProgress } = {}) {
  const config = getApiConfig();

  // If connected to future FastAPI backend
  if (!config.useMockApi) {
    if (onProgress) onProgress({ step: 1, message: 'Connecting to FastAPI backend...' });
    try {
      const response = await fetch(`${config.apiBaseUrl}/generate-questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Backend returned status ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        success: true,
        isMock: false,
        questions: data.questions || data,
        batchId: data.batchId || `batch-${Date.now().toString(36)}`,
      };
    } catch (err) {
      console.warn('FastAPI backend request failed:', err);
      throw new Error(`FastAPI backend unreachable at ${config.apiBaseUrl}. Please verify server status in Settings.`);
    }
  }

  // --- LOCAL MOCK ENGINE SIMULATION ---
  const delay = config.simulatedDelayMs || 1200;
  const stepDelay = Math.max(200, Math.floor(delay / 4));

  if (onProgress) onProgress({ step: 1, message: 'Parsing role requirements & seniority...' });
  await new Promise((r) => setTimeout(r, stepDelay));

  if (onProgress) onProgress({ step: 2, message: 'Balancing evaluation weights (Tech, Exp, Acad)...' });
  await new Promise((r) => setTimeout(r, stepDelay));

  if (onProgress) onProgress({ step: 3, message: 'Synthesizing competency-targeted demo questions...' });
  await new Promise((r) => setTimeout(r, stepDelay));

  if (onProgress) onProgress({ step: 4, message: 'Formulating evaluation rubrics and rationales...' });
  await new Promise((r) => setTimeout(r, stepDelay));

  const questions = synthesizeMockQuestions(payload);

  return {
    success: true,
    isMock: true,
    questions,
    batchId: questions[0]?.batchId || `batch-${Date.now().toString(36)}`,
  };
}

/**
 * Regenerate a single question with alternative mock prompt
 */
export async function regenerateQuestion(question, context = {}) {
  const config = getApiConfig();

  if (!config.useMockApi) {
    try {
      const response = await fetch(`${config.apiBaseUrl}/regenerate-question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questionId: question.id, competency: question.competency, context }),
      });
      if (!response.ok) throw new Error('Failed to regenerate via FastAPI backend');
      const data = await response.json();
      return { success: true, question: data };
    } catch (err) {
      throw new Error(`Failed to regenerate via backend: ${err.message}`);
    }
  }

  // Mock regeneration simulation
  await new Promise((r) => setTimeout(r, 600));

  const alternativeQuestions = [
    {
      question: `Deep dive: Can you describe a critical production incident where an unforeseen bottleneck occurred in ${question.competency.toLowerCase()}? How did you isolate root causes under pressure?`,
      whyRelevant: `[Demo Rationale] Alternative angle emphasizing live debugging and incident recovery for ${question.jobTitle}.`,
      rubric: `Interviewer listens for: Immediate triage actions, containment strategy, root cause analysis, and post-incident blameless culture.`,
    },
    {
      question: `If you were tasked with establishing company-wide engineering standards for ${question.competency.toLowerCase()}, what 3 non-negotiable guidelines would you enforce in CI/CD?`,
      whyRelevant: `[Demo Rationale] Tests engineering leadership and organizational scale standards appropriate for ${question.difficulty} level.`,
      rubric: `Looks for: Automated static analysis, security scans, unit & integration test coverage thresholds, and deployment canary stages.`,
    },
    {
      question: `Compare and contrast two competing architectural or implementation approaches you evaluated for ${question.competency.toLowerCase()}. What specific trade-offs governed your choice?`,
      whyRelevant: `[Demo Rationale] Focuses on objective evaluation frameworks and trade-off balance over dogmatic opinions.`,
      rubric: `Looks for: Nuanced trade-off balance (latency vs throughput, operational complexity vs development speed, cost vs performance).`,
    },
  ];

  let questionText = randomAlt.question;
  let whyRelevantText = randomAlt.whyRelevant;
  if (context && context.hint && context.hint.trim()) {
    questionText = `Targeting "${context.hint.trim()}": ${randomAlt.question}`;
    whyRelevantText = `[Interviewer Hint Applied: "${context.hint.trim()}"] ${randomAlt.whyRelevant}`;
  }

  const updatedQuestion = {
    ...question,
    question: questionText,
    whyRelevant: whyRelevantText,
    evaluationRubric: randomAlt.rubric,
    status: 'pending',
    rejectionReason: null,
    interviewerHint: context?.hint || null,
    updatedAt: new Date().toISOString(),
  };

  return {
    success: true,
    isMock: true,
    question: updatedQuestion,
  };
}

/**
 * Backend Analysis A: Perform Unified Candidate & Job Analysis
 * Calls FastAPI POST /api/analysis/candidate
 */
export async function analyzeCandidateBackend({ role_title, job_description, resume_text, resume_pdf_path }) {
  const config = getApiConfig();
  const baseUrl = (config.apiBaseUrl || 'http://localhost:8000').replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');

  const response = await fetch(`${baseUrl}/api/analysis/candidate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ role_title, job_description, resume_text, resume_pdf_path }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Candidate analysis failed with status ${response.status}`);
  }

  return await response.json();
}

/**
 * Backend Analysis A: Update Job Skill Weights
 * Calls FastAPI PATCH /api/jobs/{job_id}/skills
 */
export async function updateJobSkillsBackend(jobId, skillsList) {
  const config = getApiConfig();
  const baseUrl = (config.apiBaseUrl || 'http://localhost:8000').replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');

  const response = await fetch(`${baseUrl}/api/jobs/${jobId}/skills`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ skills: skillsList }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Skill update failed with status ${response.status}`);
  }

  return await response.json();
}

/**
 * Stage 2: Extract Skills, Evaluate Evidence & Fit Summary
 */
export async function extractSkillsAndProfile({
  jobTitle = 'Software Engineer',
  jobDescription = '',
  candidateProfile = '',
  resumeFileName = null,
  duration = 45,
  difficulty = 'Auto',
}, { onProgress } = {}) {
  const config = getApiConfig();

  // Try connecting to Analysis A backend API first!
  try {
    if (onProgress) onProgress({ step: 1, message: 'Connecting to Analysis A backend (FastAPI)...' });

    const backendResult = await analyzeCandidateBackend({
      role_title: jobTitle,
      job_description: jobDescription,
      resume_text: candidateProfile || 'Candidate experience in software engineering.',
    });

    if (backendResult?.success && backendResult?.data) {
      const { candidate_profile, job_analysis, comparison } = backendResult.data;

      const weightedSkills = job_analysis?.weighted_skills || [];
      const skills = weightedSkills.map((sk, idx) => {
        const evMatch = candidate_profile?.skill_evidence?.find(
          (e) => e.skill.toLowerCase() === sk.name.toLowerCase()
        );
        return {
          id: `sk-${idx + 1}`,
          name: sk.name,
          category: sk.competency || 'Technical Skills',
          status: sk.weight >= 0.8 ? 'required' : 'preferred',
          weight: sk.weight,
          normalized_weight: sk.normalized_weight,
          evidence: evMatch
            ? `Evidence (${evMatch.confidence} confidence): ${evMatch.evidence}`
            : `Extracted requirement for ${sk.competency || 'Role'}.`,
        };
      });

      const candidateSummary = {
        candidateName: resumeFileName ? resumeFileName.replace(/\.[^/.]+$/, '') : 'Candidate',
        score: comparison?.overall_score != null ? Math.round(comparison.overall_score) : 88,
        band: comparison?.candidate_band ? comparison.candidate_band.replace(/_/g, ' ').toUpperCase() : 'PROVISIONAL MATCH',
        strengths: comparison?.strengths || [],
        gaps: (comparison?.skill_gaps || []).map((g) => `${g.name} (${g.competency})`),
        lowInfo: job_analysis?.low_info || false,
        comparison: comparison,
        candidate_profile: candidate_profile,
        job_analysis: job_analysis,
      };

      if (onProgress) onProgress({ step: 3, message: 'Analysis A complete! Syncing candidate profile...' });

      return {
        success: true,
        isMock: false,
        skills,
        candidateSummary,
        comparison,
        jobAnalysis: job_analysis,
        candidateProfile: candidate_profile,
        defaultWeights: {
          technical: 50,
          experience: 35,
          academic: 15,
        },
      };
    }
  } catch (backendErr) {
    console.warn('Backend Analysis A endpoint unreachable, using local processing:', backendErr.message);
  }

  if (onProgress) onProgress({ step: 1, message: 'Analyzing job description requirements...' });
  await new Promise((r) => setTimeout(r, 300));

  if (onProgress) onProgress({ step: 2, message: 'Parsing candidate resume & profile...' });
  await new Promise((r) => setTimeout(r, 350));

  if (onProgress) onProgress({ step: 3, message: 'Extracting competency evidence and candidate alignment...' });
  await new Promise((r) => setTimeout(r, 300));

  const textLower = `${jobTitle} ${jobDescription} ${candidateProfile}`.toLowerCase();
  const isLowInfo = jobDescription.trim().length < 120;

  // Derive candidate name
  const nameMatch = candidateProfile.match(/Candidate:\s*([^\n\r,]+)/i);
  const candidateName = nameMatch ? nameMatch[1].trim() : resumeFileName ? resumeFileName.replace(/\.[^/.]+$/, '') : 'Candidate';


  // Domain skills synthesis
  let skills = [];
  if (textLower.includes('react') || textLower.includes('frontend') || textLower.includes('typescript') || textLower.includes('ui') || textLower.includes('css')) {
    skills = [
      {
        id: 'sk-1',
        name: 'React 19 & State Architecture',
        category: 'Technical Skills',
        status: 'required',
        weight: 35,
        evidence: 'Job requires architecting scalable design systems; candidate has 6 yrs modular micro-frontend experience.',
      },
      {
        id: 'sk-2',
        name: 'Strict TypeScript & Generic Types',
        category: 'Technical Skills',
        status: 'required',
        weight: 25,
        evidence: 'Role emphasizes strict typing standards; candidate profile lists daily TypeScript & Next.js usage.',
      },
      {
        id: 'sk-3',
        name: 'Real-time WebSockets & Telemetry',
        category: 'Problem Solving',
        status: 'required',
        weight: 15,
        evidence: 'Job posting mentions low-latency streaming telemetry; candidate built WebSocket data feeds.',
      },
      {
        id: 'sk-4',
        name: 'Core Web Vitals & Caching Strategy',
        category: 'Problem Solving',
        status: 'preferred',
        weight: 10,
        evidence: 'Requirements state client caching optimization (React Query / TanStack); profile notes 42% bundle reduction.',
      },
      {
        id: 'sk-5',
        name: 'Micro-Frontend Modular Scalability',
        category: 'System Design',
        status: 'required',
        weight: 10,
        evidence: 'Enterprise SaaS scale requirements; candidate led migration from monolithic Redux to micro-frontends.',
      },
      {
        id: 'sk-6',
        name: 'Engineering Mentorship & Cross-Team RFCs',
        category: 'Behavioural Skills',
        status: 'preferred',
        weight: 5,
        evidence: 'Required to mentor junior engineers; candidate background notes team leadership in high-growth startups.',
      },
    ];
  } else if (textLower.includes('python') || textLower.includes('go') || textLower.includes('backend') || textLower.includes('kafka') || textLower.includes('distributed')) {
    skills = [
      {
        id: 'sk-1',
        name: 'Distributed Concurrency & Async Runtimes',
        category: 'Technical Skills',
        status: 'required',
        weight: 30,
        evidence: 'Job specifies AsyncIO/Go concurrency; candidate built $10M/day payment worker.',
      },
      {
        id: 'sk-2',
        name: 'Kafka Partitioning & Idempotent Processing',
        category: 'System Design',
        status: 'required',
        weight: 25,
        evidence: 'High throughput event pipelines (200M+ events/day); candidate lists Kafka & Redis Cluster.',
      },
      {
        id: 'sk-3',
        name: 'High-Volume Production Incident Triage',
        category: 'Problem Solving',
        status: 'required',
        weight: 20,
        evidence: 'Zero-downtime SLA requirements; candidate maintained 99.999% uptime in fintech.',
      },
      {
        id: 'sk-4',
        name: 'PostgreSQL Locking & Schema Evolution',
        category: 'Technical Skills',
        status: 'preferred',
        weight: 15,
        evidence: 'Zero-downtime database migrations required; candidate profile lists relational schema optimization.',
      },
      {
        id: 'sk-5',
        name: 'Technical Leadership & Blameless Post-Mortems',
        category: 'Behavioural Skills',
        status: 'required',
        weight: 10,
        evidence: 'Authoring RFC specs and cross-team alignment; candidate has 9 years engineering experience.',
      },
    ];
  } else if (textLower.includes('ml') || textLower.includes('ai') || textLower.includes('llm') || textLower.includes('pytorch')) {
    skills = [
      {
        id: 'sk-1',
        name: 'LLM Serving & Low-Latency Inference',
        category: 'Technical Skills',
        status: 'required',
        weight: 35,
        evidence: 'Serving with Triton/vLLM/FastAPI; candidate deployed semantic caching assistants.',
      },
      {
        id: 'sk-2',
        name: 'Vector Indexing & Semantic Search (Qdrant)',
        category: 'Technical Skills',
        status: 'required',
        weight: 25,
        evidence: 'Vector search & RAG pipelines in job requirements; candidate lists Qdrant and LangChain.',
      },
      {
        id: 'sk-3',
        name: 'Hallucination Mitigation & Evaluation Benchmarks',
        category: 'Problem Solving',
        status: 'required',
        weight: 20,
        evidence: 'Evaluation frameworks for hallucinations & token costs required in posting.',
      },
      {
        id: 'sk-4',
        name: 'Stakeholder Expectation Management for AI',
        category: 'Behavioural Skills',
        status: 'preferred',
        weight: 20,
        evidence: 'Translating probabilistic model bounds to product teams; candidate supported 1,500 employees.',
      },
    ];
  } else {
    // General engineering defaults
    skills = [
      {
        id: 'sk-1',
        name: 'Core Language Fundamentals & System Design',
        category: 'Technical Skills',
        status: 'required',
        weight: 40,
        evidence: 'Core technical requirements from role description.',
      },
      {
        id: 'sk-2',
        name: 'Production Debugging & Root Cause Analysis',
        category: 'Problem Solving',
        status: 'required',
        weight: 30,
        evidence: 'Hypothesis testing and production issue resolution.',
      },
      {
        id: 'sk-3',
        name: 'Team Collaboration & Technical Communication',
        category: 'Behavioural Skills',
        status: 'required',
        weight: 20,
        evidence: 'Cross-functional engineering communication and planning.',
      },
      {
        id: 'sk-4',
        name: 'Architectural Scaling & Maintainability',
        category: 'System Design',
        status: 'preferred',
        weight: 10,
        evidence: 'Long-term maintainability and system modularity.',
      },
    ];
  }

  // Calculate candidate fit score
  const score = Math.min(95, Math.max(76, Math.floor(82 + (candidateProfile.length % 14))));

  const candidateSummary = {
    candidateName,
    score,
    band: difficulty === 'Auto' ? 'Senior Specialist (L5)' : `${difficulty} Alignment`,
    strengths: [
      `Direct hands-on experience in ${skills[0].name} and production architecture`,
      'Demonstrated ownership of high-impact engineering milestones',
      'Solid alignment between prior project scope and team technical requirements',
    ],
    gaps: [
      'Limited formal documentation of multi-region disaster recovery in profile',
      ...(isLowInfo ? ['Job description lacks explicit performance thresholds or tooling constraints'] : []),
    ],
    lowInfo: isLowInfo,
  };

  return {
    success: true,
    isMock: true,
    skills,
    candidateSummary,
    defaultWeights: {
      technical: 50,
      experience: 35,
      academic: 15,
    },
  };
}

/**
 * Stage 3: Generate Interview Plan from Calibrated Skills & Weights
 */
export async function generateInterviewPlanFromSkills({
  jobTitle,
  candidateProfile,
  skills,
  weights = { technical: 50, experience: 35, academic: 15 },
  duration = 45,
  difficulty = 'Auto',
}, { onProgress } = {}) {
  if (onProgress) onProgress({ step: 1, message: 'Mapping calibrated skills to evaluation rubrics...' });
  await new Promise((r) => setTimeout(r, 350));

  if (onProgress) onProgress({ step: 2, message: 'Calibrating question difficulty & time budget...' });
  await new Promise((r) => setTimeout(r, 350));

  if (onProgress) onProgress({ step: 3, message: 'Synthesizing competency questions and follow-ups...' });
  await new Promise((r) => setTimeout(r, 400));

  // Determine target question count based on duration
  const targetCount = duration === 30 ? 4 : duration === 60 ? 8 : 6;

  // Difficulty mapping: Easy -> Medium -> Hard
  const difficulties = ['Easy', 'Medium', 'Medium', 'Hard', 'Medium', 'Hard', 'Easy', 'Hard'];

  const batchId = `plan-${Date.now().toString(36)}`;
  const questions = [];

  for (let i = 0; i < targetCount; i++) {
    const skill = skills[i % skills.length];
    const diff = difficulty === 'Auto' ? difficulties[i % difficulties.length] : difficulty;

    const questionTemplates = [
      {
        q: `Walk me through your end-to-end approach to designing ${skill.name}. What runtime safeguards, failure isolation mechanisms, and telemetry metrics do you establish first?`,
        why: `Evaluates ${skill.name} (${skill.status === 'required' ? 'Required Skill' : 'Preferred Skill'}) with weighted focus of ${weights.technical}% on technical depth.`,
        rubric: `Interviewer looks for: Concrete implementation trade-offs, defensive design, latency considerations, and familiarity with production failure modes.`,
        followUps: [
          'What happens if the primary dependency fails or times out under peak load?',
          'How do you verify this in automated regression tests before shipping?',
        ],
      },
      {
        q: `Describe a complex problem or latency spike you investigated involving ${skill.name}. Walk me through your hypothesis testing and how you proved the root cause.`,
        why: `Assesses problem solving and diagnostic rigor in ${skill.name} (weighted: ${weights.experience}% relevant experience).`,
        rubric: `Interviewer evaluates: Structured triage methodology (metrics, logs, traces) over random guessing, and systemic prevention steps.`,
        followUps: [
          'If initial metrics show normal CPU/RAM, what deeper system telemetry do you check?',
          'What guardrail was added to prevent recurrence?',
        ],
      },
      {
        q: `When balancing rapid feature delivery against architectural purity in ${skill.name}, how do you decide when to take on technical debt vs. push back on timelines?`,
        why: `Measures engineering leadership, pragmatic delivery trade-offs, and communication around ${skill.name}.`,
        rubric: `Interviewer listens for: Clear business articulation of technical risk, phased delivery proposals, and proactive debt documentation.`,
        followUps: [
          'How did you ensure that compromise got prioritized later on the product roadmap?',
        ],
      },
    ];

    const template = questionTemplates[i % questionTemplates.length];

    questions.push({
      id: `plan-q-${Date.now().toString(36)}-${i + 1}`,
      batchId,
      jobTitle,
      skillId: skill.id,
      skillName: skill.name,
      competency: skill.category,
      difficulty: diff,
      question: template.q,
      whyRelevant: template.why,
      evaluationRubric: template.rubric,
      followUps: template.followUps,
      status: 'pending',
      createdAt: new Date().toISOString(),
      interviewerNotes: '',
    });
  }

  return {
    success: true,
    isMock: true,
    batchId,
    questions,
  };
}

/**
 * Test FastAPI Backend Health
 */
export async function testBackendConnection(baseUrl) {
  try {
    const url = baseUrl.replace(/\/+$/, '');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3500);

    const response = await fetch(`${url}/health`, {
      method: 'GET',
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (response.ok) {
      const data = await response.json().catch(() => ({}));
      return { success: true, message: 'Connected to FastAPI backend service', data };
    }
    return { success: false, message: `Server replied with HTTP status ${response.status}` };
  } catch (err) {
    if (err.name === 'AbortError') {
      return { success: false, message: 'Connection timed out after 3.5s' };
    }
    return { success: false, message: `Backend offline: ${err.message}` };
  }
}
