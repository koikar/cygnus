import useAppStore from '../store/useAppStore.js';

const ZONE_COLORS = {
  A: '#3b82f6',
  B: '#8b5cf6',
  C: '#f59e0b',
  BIN: '#00d68f',
};

export default function PerceptionPanel() {
  const scene = useAppStore(s => s.scene);
  const connectionMode = useAppStore(s => s.connectionMode);

  const isLive = connectionMode === 'live';
  const label = isLive ? 'LIVE CAMERA' : 'SIMULATED PERCEPTION';
  const labelColor = isLive ? 'var(--accent-green)' : 'var(--accent-purple)';

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <div className="panel-title-dot" style={{ background: labelColor }} />
        {label}
        {isLive && <div className="pulse pulse-green" style={{ marginLeft: 'auto' }} />}
      </div>

      {/* Perception grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
        {['A', 'B', 'C', 'BIN'].map(zone => {
          const isCubeHere = !scene.cube_in_bin && scene.cube_zone === zone;
          const isBin = zone === 'BIN';
          const isInBin = scene.cube_in_bin && isBin;

          return (
            <div key={zone} style={{
              background: 'var(--bg-secondary)',
              border: `1px solid ${(isCubeHere || isInBin) ? ZONE_COLORS[zone] : 'var(--border)'}`,
              borderRadius: 6,
              padding: '10px 12px',
              position: 'relative',
              transition: 'border-color 0.3s',
            }}>
              <div style={{ fontSize: 9, letterSpacing: '0.1em', color: 'var(--text-muted)', marginBottom: 4 }}>
                ZONE {zone}
              </div>
              <div style={{
                fontSize: 12,
                fontWeight: 600,
                color: (isCubeHere || isInBin) ? ZONE_COLORS[zone] : 'var(--text-muted)',
              }}>
                {isInBin ? '📦 CUBE ✓' : isCubeHere ? '📦 CUBE' : isBin ? '[ empty ]' : '—'}
              </div>
              {(isCubeHere || isInBin) && (
                <div style={{
                  position: 'absolute', top: 6, right: 8,
                  width: 6, height: 6, borderRadius: '50%',
                  background: ZONE_COLORS[zone],
                  boxShadow: `0 0 8px ${ZONE_COLORS[zone]}`,
                  animation: 'pulse 1.2s ease-in-out infinite',
                }} />
              )}
            </div>
          );
        })}
      </div>

      {/* State rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {[
          { label: 'GRIPPER', value: scene.holding ? 'HOLDING' : 'OPEN', color: scene.holding ? 'var(--accent-green)' : 'var(--text-muted)' },
          { label: 'CUBE IN BIN', value: scene.cube_in_bin ? 'YES ✓' : 'NO', color: scene.cube_in_bin ? 'var(--accent-green)' : 'var(--text-muted)' },
          { label: 'ACTIVE ZONE', value: scene.cube_in_bin ? 'BIN' : scene.cube_zone, color: ZONE_COLORS[scene.cube_in_bin ? 'BIN' : scene.cube_zone] },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '5px 8px', background: 'var(--bg-secondary)', borderRadius: 4,
          }}>
            <span style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>{label}</span>
            <span style={{ fontSize: 11, fontWeight: 600, color }}>{value}</span>
          </div>
        ))}
      </div>

      {!isLive && (
        <div style={{ marginTop: 10, fontSize: 9, color: 'var(--text-muted)', textAlign: 'center' }}>
          Simulated perception — set VITE_BACKEND_URL for live camera
        </div>
      )}
    </div>
  );
}
