import React from 'react';
import { RotateCcw, Sliders, Cpu, Briefcase, GraduationCap } from 'lucide-react';

export const DEFAULT_WEIGHTS = {
  technical: 50,
  experience: 35,
  academic: 15,
};

export function WeightSliders({ weights, onChange, onReset, defaultWeights = DEFAULT_WEIGHTS, title = 'Evaluation Weight Configuration' }) {
  const currentWeights = weights || defaultWeights;

  const handleSliderChange = (changedKey, rawValue) => {
    const newVal = Math.max(0, Math.min(100, parseInt(rawValue, 10) || 0));
    const keys = ['technical', 'experience', 'academic'];
    const otherKeys = keys.filter((k) => k !== changedKey);

    const remaining = 100 - newVal;
    const [k1, k2] = otherKeys;
    const v1 = currentWeights[k1] || 0;
    const v2 = currentWeights[k2] || 0;
    const otherSum = v1 + v2;

    let newV1, newV2;
    if (otherSum > 0) {
      newV1 = Math.round((v1 / otherSum) * remaining);
      newV2 = remaining - newV1;
    } else {
      newV1 = Math.floor(remaining / 2);
      newV2 = remaining - newV1;
    }

    // Guard against negatives
    if (newV1 < 0) {
      newV2 += newV1;
      newV1 = 0;
    }
    if (newV2 < 0) {
      newV1 += newV2;
      newV2 = 0;
    }

    const updated = {
      [changedKey]: newVal,
      [k1]: Math.max(0, newV1),
      [k2]: Math.max(0, newV2),
    };

    // Guarantee exact 100 sum
    const total = updated.technical + updated.experience + updated.academic;
    if (total !== 100) {
      updated[k2] += 100 - total;
    }

    onChange(updated);
  };

  const handleReset = () => {
    if (onReset) {
      onReset(defaultWeights);
    } else {
      onChange(defaultWeights);
    }
  };

  const total =
    (currentWeights.technical || 0) +
    (currentWeights.experience || 0) +
    (currentWeights.academic || 0);

  const sliderConfigs = [
    {
      key: 'technical',
      label: 'Technical Skills',
      desc: 'Coding depth, frameworks, and architecture problem solving',
      icon: Cpu,
      color: 'var(--color-primary)',
      val: currentWeights.technical || 0,
    },
    {
      key: 'experience',
      label: 'Relevant Experience',
      desc: 'Past project track record, production war stories, leadership',
      icon: Briefcase,
      color: 'var(--color-accent-sage-dark)',
      val: currentWeights.experience || 0,
    },
    {
      key: 'academic',
      label: 'Academic Performance',
      desc: 'Computer science foundations, algorithm theory, coursework',
      icon: GraduationCap,
      color: 'var(--color-accent-terra)',
      val: currentWeights.academic || 0,
    },
  ];

  return (
    <div className="card weight-sliders-card" style={{ padding: '18px 20px', background: '#ffffff' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 14,
          flexWrap: 'wrap',
          gap: 8,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sliders size={17} style={{ color: 'var(--primary)' }} />
          <span style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--text-main)' }}>
            {title}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span
            className="badge badge-forest"
            style={{
              fontWeight: 700,
              fontSize: 12,
              background: total === 100 ? 'var(--color-primary-light)' : 'var(--color-danger-bg)',
              color: total === 100 ? 'var(--color-primary)' : 'var(--color-danger-text)',
              border: total === 100 ? '1px solid var(--color-accent-sage)' : '1px solid var(--color-danger-border)',
            }}
          >
            Total: {total}%
          </span>
          <button
            type="button"
            className="btn-ghost"
            style={{ fontSize: 12, padding: '4px 8px' }}
            onClick={handleReset}
            title="Reset weights to default distribution (50% / 35% / 15%)"
          >
            <RotateCcw size={13} />
            Reset Weights
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {sliderConfigs.map((cfg) => {
          const Icon = cfg.icon;
          return (
            <div key={cfg.key} style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Icon size={15} style={{ color: cfg.color }} />
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-main)' }}>
                    {cfg.label}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    color: cfg.color,
                    minWidth: 42,
                    textAlign: 'right',
                  }}
                >
                  {cfg.val}%
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={cfg.val}
                  onChange={(e) => handleSliderChange(cfg.key, e.target.value)}
                  style={{
                    flex: 1,
                    accentColor: cfg.color,
                    height: 6,
                    cursor: 'pointer',
                  }}
                />
              </div>

              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 21 }}>
                {cfg.desc}
              </span>
            </div>
          );
        })}
      </div>

      {/* Visual Balanced Distribution Bar */}
      <div
        style={{
          marginTop: 14,
          height: 8,
          borderRadius: 999,
          overflow: 'hidden',
          display: 'flex',
          background: 'var(--color-border)',
        }}
      >
        <div
          style={{
            width: `${currentWeights.technical}%`,
            background: 'var(--color-primary)',
            transition: 'width 0.2s ease',
          }}
          title={`Technical Skills: ${currentWeights.technical}%`}
        />
        <div
          style={{
            width: `${currentWeights.experience}%`,
            background: 'var(--color-accent-sage)',
            transition: 'width 0.2s ease',
          }}
          title={`Relevant Experience: ${currentWeights.experience}%`}
        />
        <div
          style={{
            width: `${currentWeights.academic}%`,
            background: 'var(--color-accent-terra)',
            transition: 'width 0.2s ease',
          }}
          title={`Academic Performance: ${currentWeights.academic}%`}
        />
      </div>
    </div>
  );
}
