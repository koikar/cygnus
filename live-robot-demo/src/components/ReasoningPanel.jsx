import useAppStore from '../store/useAppStore.js';

const PUBLIC_LABELS = {
  observe: 'Robot scans the workspace',
  detect: 'Something went wrong!',
  compare: 'Checking what was expected vs what happened',
  locate: 'AI searches for the missing object',
  plan: 'AI creates a new plan',
  validate: 'Checking if the fix worked',
  save: 'Saving the fix to memory',
};

const STEP_COLORS = {
  observe: 'var(--accent-blue)',
  detect: 'var(--accent-red)',
  compare: 'var(--accent-orange)',
  locate: 'var(--accent-yellow)',
  plan: 'var(--accent-purple)',
  validate: 'var(--accent-green)',
  save: 'var(--accent-green)',
};

export default function ReasoningPanel() {
  const reasoningSteps = useAppStore(s => s.reasoningSteps);
  const reasoningRationale = useAppStore(s => s.reasoningRationale);
  const currentReasoningId = useAppStore(s => s.currentReasoningId);
  const publicMode = useAppStore(s => s.publicMode);

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div className="panel-title-dot" style={{ background: 'var(--accent-purple)' }} />
        {publicMode ? 'AI THINKING STEPS' : 'AI REASONING TIMELINE'}
      </div>

      {/* Step indicators */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
        {reasoningSteps.map((step, i) => {
          const color = STEP_COLORS[step.id] || 'var(--accent-blue)';
          const label = publicMode ? (PUBLIC_LABELS[step.id] || step.label) : step.label;
          return (
            <div key={step.id} style={{
              display: 'flex', alignItems: 'center', gap: 8,
              opacity: step.done || step.active ? 1 : 0.35,
              transition: 'opacity 0.3s',
            }}>
              {/* Connector line */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 14 }}>
                <div style={{
                  width: 14, height: 14, borderRadius: '50%',
                  background: step.done ? 'var(--accent-green)' : step.active ? color : 'var(--bg-surface)',
                  border: `2px solid ${step.active ? color : step.done ? 'var(--accent-green)' : 'var(--border)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: step.active ? `0 0 10px ${color}` : 'none',
                  transition: 'all 0.3s',
                }}>
                  {step.done && (
                    <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                      <path d="M1.5 4L3.5 6L6.5 2" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                  )}
                  {step.active && (
                    <div style={{
                      width: 5, height: 5, borderRadius: '50%',
                      background: color,
                      animation: 'pulse 1s ease-in-out infinite',
                    }} />
                  )}
                </div>
                {i < reasoningSteps.length - 1 && (
                  <div style={{
                    width: 1.5, height: 8,
                    background: step.done ? 'var(--accent-green)' : 'var(--border)',
                    marginTop: 2,
                  }} />
                )}
              </div>
              <div style={{
                fontSize: 11,
                fontWeight: step.active ? 600 : 400,
                color: step.active ? color : step.done ? 'var(--accent-green)' : 'var(--text-secondary)',
                transition: 'color 0.3s',
                lineHeight: 1.3,
              }}>
                {label}
              </div>
            </div>
          );
        })}
      </div>

      {/* Current rationale */}
      {reasoningRationale && (
        <div style={{
          marginTop: 'auto',
          padding: '8px 10px',
          background: 'var(--bg-secondary)',
          borderRadius: 6,
          borderLeft: '3px solid var(--accent-purple)',
          fontSize: 10,
          color: 'var(--text-secondary)',
          lineHeight: 1.6,
        }}>
          {reasoningRationale}
        </div>
      )}
    </div>
  );
}
