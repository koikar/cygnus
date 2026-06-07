import useAppStore from '../store/useAppStore.js';

const MODE_CONFIG = {
  mock: { label: 'MOCK MODE', cls: 'badge-mock', pulse: 'pulse-purple' },
  live: { label: 'LIVE BACKEND', cls: 'badge-live', pulse: 'pulse-green' },
  disconnected: { label: 'DISCONNECTED', cls: 'badge-disconnected', pulse: 'pulse-red' },
};

// Matches the logo from the screenshot: rounded square + arc shape, orange/amber
function ReflexOSLogo({ size = 36 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" fill="none">
      {/* Rounded square background */}
      <rect x="1" y="1" width="34" height="34" rx="8" fill="#1a110a" stroke="#f59e0b" strokeWidth="1.4" />
      {/* Arc / house-roof shape in orange */}
      <path
        d="M10 24 C10 24 10 16 18 11 C26 16 26 24 26 24"
        stroke="#f59e0b"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Small dot at apex */}
      <circle cx="18" cy="11" r="1.8" fill="#fbbf24" />
    </svg>
  );
}

export default function TopBar({ onReset }) {
  const { connectionMode, isRunning, publicMode, setPublicMode } = useAppStore();
  const modeConf = MODE_CONFIG[connectionMode] || MODE_CONFIG.mock;

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      background: 'rgba(6, 11, 24, 0.95)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border)',
      padding: '10px 20px',
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      flexWrap: 'wrap',
    }}>
      {/* Logo + wordmark */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginRight: 'auto' }}>
        <ReflexOSLogo size={36} />
        <div>
          <div style={{ fontSize: 15, fontWeight: 800, letterSpacing: '0.02em', lineHeight: 1.1 }}>
            <span style={{ color: '#f5f5f5' }}>Reflex</span>
            <span style={{ color: '#f59e0b' }}>OS</span>
          </div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.14em', marginTop: 1 }}>
            MISSION CONTROL
          </div>
        </div>
      </div>

      {/* Status row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        {isRunning && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--accent-green)' }}>
            <div className="pulse pulse-green" />
            RUNNING
          </div>
        )}

        <div className={`badge ${modeConf.cls}`}>
          <div className={`pulse ${modeConf.pulse}`} />
          {modeConf.label}
        </div>

        {/* Public/Technical toggle */}
        <button
          className="btn"
          style={{ fontSize: 10, padding: '5px 12px' }}
          onClick={() => setPublicMode(!publicMode)}
          aria-label="Toggle public/technical mode"
        >
          {publicMode ? '[ PUBLIC MODE ]' : '[ TECHNICAL MODE ]'}
        </button>

        {/* E-stop */}
        <button
          className="btn btn-stop"
          style={{ fontSize: 10, padding: '5px 12px' }}
          onClick={onReset}
          aria-label="Emergency stop and reset"
        >
          ⬛ E-STOP
        </button>
      </div>
    </header>
  );
}
