import React from 'react';
import { QuestionCard } from './QuestionCard';
import { CheckCircle2, Layers } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export function QuestionGroup({ competency, questions }) {
  const { acceptQuestion, addToast } = useApp();

  const handleAcceptAllInGroup = () => {
    let acceptedCount = 0;
    questions.forEach((q) => {
      if (q.status !== 'accepted') {
        acceptQuestion(q.id);
        acceptedCount++;
      }
    });
    if (acceptedCount > 0) {
      addToast({
        type: 'success',
        title: `Approved ${acceptedCount} Questions`,
        message: `All questions under ${competency} marked as accepted.`,
      });
    }
  };

  const allAccepted = questions.every((q) => q.status === 'accepted');

  return (
    <div style={{ marginBottom: 28 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 14,
          padding: '8px 12px',
          background: 'var(--color-primary-light)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-accent-sage)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Layers size={17} style={{ color: 'var(--color-primary)' }} />
          <h3
            style={{
              fontSize: 15,
              fontWeight: 700,
              color: 'var(--color-primary)',
              margin: 0,
            }}
          >
            {competency}
          </h3>
          <span className="badge badge-forest">{questions.length} questions</span>
        </div>

        {!allAccepted && (
          <button
            className="btn-ghost"
            style={{ fontSize: 12, padding: '4px 8px', color: 'var(--success-text)' }}
            onClick={handleAcceptAllInGroup}
            title="Approve all questions in this competency group"
          >
            <CheckCircle2 size={13} />
            Accept All in Group
          </button>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {questions.map((q) => (
          <QuestionCard key={q.id} question={q} />
        ))}
      </div>
    </div>
  );
}
