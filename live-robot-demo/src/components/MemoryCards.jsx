import useAppStore from '../store/useAppStore.js';

// Pre-seeded mock card shown even before the demo completes episode 2
const SEED_CARD = {
  signature: 'cube@A',
  why: 'Default starting habit — robot was trained with cube at zone A.',
  plan: 'look() → move_to(A) → grip → move_to(bin) → release',
  uses: 12,
  costSaved: 0,
  isHabit: true,
};

export default function MemoryCards() {
  const memoryCards = useAppStore(s => s.memoryCards);
  const learnedReflexes = useAppStore(s => s.learnedReflexes);
  const publicMode = useAppStore(s => s.publicMode);

  const allCards = [SEED_CARD, ...memoryCards];

  return (
    <div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20,
        fontSize: 12, color: 'var(--text-secondary)',
      }}>
        <span>
          <span style={{ color: 'var(--accent-green)', fontWeight: 700, fontSize: 22 }}>
            {learnedReflexes}
          </span>
          {' '}reflex{learnedReflexes !== 1 ? 'es' : ''} learned from failure
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 16,
      }}>
        {allCards.map((card) => (
          <MemoryCard key={card.signature} card={card} publicMode={publicMode} />
        ))}
      </div>
    </div>
  );
}

function MemoryCard({ card, publicMode }) {
  const isReflex = !card.isHabit;
  const borderColor = isReflex ? 'var(--accent-green)' : 'var(--accent-blue)';
  const tagLabel = isReflex ? 'REFLEX' : 'HABIT';
  const tagColor = isReflex ? 'var(--accent-green)' : 'var(--accent-blue)';

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: `1px solid ${isReflex ? 'rgba(0, 214, 143, 0.3)' : 'var(--border)'}`,
      borderRadius: 'var(--radius-lg)',
      padding: 18,
      position: 'relative',
      overflow: 'hidden',
      boxShadow: isReflex ? '0 0 20px rgba(0, 214, 143, 0.08)' : 'none',
    }}>
      {/* Top accent bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 2,
        background: borderColor,
      }} />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: 3 }}>
            SIGNATURE
          </div>
          <div style={{ fontSize: 16, fontWeight: 700, color: tagColor }}>
            {card.signature}
          </div>
        </div>
        <span style={{
          fontSize: 9, fontWeight: 700, padding: '3px 8px',
          borderRadius: 12, letterSpacing: '0.08em',
          background: `${tagColor}1a`, color: tagColor,
          border: `1px solid ${tagColor}44`,
        }}>
          {tagLabel}
        </span>
      </div>

      {/* Why */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 9, color: 'var(--text-muted)', marginBottom: 3, letterSpacing: '0.08em' }}>
          {publicMode ? 'REASON' : 'WHY LEARNED'}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          {card.why}
        </div>
      </div>

      {/* Plan */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 9, color: 'var(--text-muted)', marginBottom: 3, letterSpacing: '0.08em' }}>
          {publicMode ? 'SHORTCUT' : 'REFLEX PLAN'}
        </div>
        <code style={{
          fontSize: 10, color: tagColor, lineHeight: 1.8,
          display: 'block',
          padding: '6px 8px',
          background: 'var(--bg-secondary)',
          borderRadius: 4,
        }}>
          {card.plan}
        </code>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', gap: 12 }}>
        <Stat label={publicMode ? 'Times Used' : 'USES'} value={card.uses} />
        {card.costSaved > 0 && (
          <Stat
            label={publicMode ? 'Steps Saved' : 'COST SAVED'}
            value={`-${card.costSaved}`}
            valueColor="var(--accent-green)"
          />
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, valueColor = 'var(--text-primary)' }) {
  return (
    <div style={{
      flex: 1, textAlign: 'center',
      padding: '6px 8px',
      background: 'var(--bg-secondary)', borderRadius: 6,
    }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: valueColor }}>{value}</div>
      <div style={{ fontSize: 8, color: 'var(--text-muted)', letterSpacing: '0.08em', marginTop: 2 }}>{label}</div>
    </div>
  );
}
