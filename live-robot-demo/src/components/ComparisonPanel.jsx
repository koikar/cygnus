import useAppStore from '../store/useAppStore.js';

export default function ComparisonPanel() {
  const metrics = useAppStore(s => s.metrics);
  const publicMode = useAppStore(s => s.publicMode);

  const first = metrics.first_attempt_cost;
  const second = metrics.second_attempt_cost;
  const improvement = first && second ? Math.round(((first - second) / first) * 100) : null;

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="panel-header">
        <div className="panel-title-dot" style={{ background: 'var(--accent-green)' }} />
        {publicMode ? 'BEFORE vs AFTER LEARNING' : 'FIRST TIME vs SECOND TIME'}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 8, alignItems: 'center' }}>
        {/* First attempt */}
        <AttemptCard
          label={publicMode ? 'First Try' : 'ATTEMPT 1 — HABIT FAILED'}
          subtitle={publicMode ? 'Robot did not know cube moved' : 'habit → failure → AI recovery'}
          cost={first ?? 8}
          costLabel="steps"
          mode="system2"
          modeLabel={publicMode ? 'Slow recovery' : 'SYSTEM 2 RECOVERY'}
          color="var(--accent-orange)"
          locked={!first}
        />

        {/* Arrow */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, padding: '0 4px' }}>
          <div style={{ fontSize: 20, color: 'var(--text-muted)' }}>→</div>
          {improvement !== null && (
            <div style={{
              fontSize: 18, fontWeight: 800, color: 'var(--accent-green)',
              textShadow: '0 0 20px var(--accent-green)',
              textAlign: 'center',
            }}>
              {improvement}%
              <div style={{ fontSize: 9, fontWeight: 400, color: 'var(--accent-green)', opacity: 0.8 }}>
                faster
              </div>
            </div>
          )}
        </div>

        {/* Second attempt */}
        <AttemptCard
          label={publicMode ? 'Next Try' : 'ATTEMPT 2 — REFLEX'}
          subtitle={publicMode ? 'Robot remembered and skipped wasted steps' : 'reflex recall → direct success'}
          cost={second ?? 4}
          costLabel="steps"
          mode="reflex"
          modeLabel={publicMode ? 'Memory shortcut' : 'REFLEX (MEMORY)'}
          color="var(--accent-green)"
          locked={!second}
        />
      </div>

      {/* Summary bar */}
      {improvement !== null ? (
        <div style={{
          padding: '12px 16px',
          background: 'rgba(0, 214, 143, 0.08)',
          border: '1px solid rgba(0, 214, 143, 0.25)',
          borderRadius: 'var(--radius)',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 11, color: 'var(--accent-green)', fontWeight: 600 }}>
            {publicMode
              ? `The robot saved ${first - second} steps by using its memory!`
              : `Antifragility score: +${metrics.antifragility_score}% — cost reduced ${first} → ${second} steps`
            }
          </div>
        </div>
      ) : (
        <div style={{
          padding: '12px 16px',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius)',
          textAlign: 'center',
          fontSize: 10, color: 'var(--text-muted)',
        }}>
          Run the demo to see the improvement after learning
        </div>
      )}
    </div>
  );
}

function AttemptCard({ label, subtitle, cost, costLabel, modeLabel, color, locked }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: `1px solid ${locked ? 'var(--border)' : color + '44'}`,
      borderRadius: 'var(--radius)',
      padding: '14px 12px',
      textAlign: 'center',
      opacity: locked ? 0.5 : 1,
      transition: 'all 0.4s',
    }}>
      <div style={{ fontSize: 8, letterSpacing: '0.1em', color: 'var(--text-muted)', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 800, color: locked ? 'var(--text-muted)' : color, lineHeight: 1 }}>
        {cost}
      </div>
      <div style={{ fontSize: 9, color: 'var(--text-muted)', marginBottom: 8 }}>{costLabel}</div>
      <div style={{
        fontSize: 9, fontWeight: 600, letterSpacing: '0.06em',
        color: locked ? 'var(--text-muted)' : color,
        padding: '3px 6px',
        background: locked ? 'transparent' : `${color}18`,
        borderRadius: 10,
        display: 'inline-block',
      }}>
        {modeLabel}
      </div>
      <div style={{ marginTop: 6, fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.4 }}>
        {subtitle}
      </div>
    </div>
  );
}
