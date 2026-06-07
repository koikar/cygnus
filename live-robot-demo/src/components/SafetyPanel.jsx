export default function SafetyPanel() {
  const items = [
    {
      icon: '🔒',
      title: 'No Raw Motor Commands',
      desc: 'This frontend never sends joint angles or motor commands. Only high-level demo actions (run, inject-failure, replay, reset) are sent to the backend.',
      color: 'var(--accent-blue)',
    },
    {
      icon: '🛡',
      title: 'Backend Owns Safety',
      desc: 'The robot teaching backend validates all movements, enforces workspace limits, and owns the motor safety layer. The frontend is UI-only.',
      color: 'var(--accent-green)',
    },
    {
      icon: '⚡',
      title: 'E-Stop Always Visible',
      desc: 'The Reset / E-Stop button is always accessible in the top navigation bar. It immediately halts the demo and returns to a safe neutral state.',
      color: 'var(--accent-orange)',
    },
    {
      icon: '🔄',
      title: 'Simulation Fallback',
      desc: 'If the physical robot is unavailable, the backend can run in simulation mode. The frontend shows a "simulation" badge and continues normally.',
      color: 'var(--accent-purple)',
    },
    {
      icon: '📡',
      title: 'Disconnected Safe State',
      desc: 'If the WebSocket or backend disconnects, the page immediately shows a "disconnected" warning and reverts to mock demo mode. The robot is not left in an unknown state.',
      color: 'var(--accent-red)',
    },
    {
      icon: '🔑',
      title: 'No Secrets in Frontend',
      desc: 'No API keys, credentials, or motor configurations are embedded in frontend code. The only configurable value is VITE_BACKEND_URL.',
      color: 'var(--accent-yellow)',
    },
  ];

  return (
    <div>
      <div className="section-title">Safety & Constraints</div>
      <div className="section-subtitle">
        Cygnus Mission Control is designed with a clear safety boundary between the UI and the robot.
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: 16,
      }}>
        {items.map(item => (
          <div key={item.title} style={{
            display: 'flex', gap: 14, padding: '16px 18px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
          }}>
            <div style={{ fontSize: 22, lineHeight: 1.2, flexShrink: 0 }}>{item.icon}</div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: item.color, marginBottom: 6 }}>
                {item.title}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {item.desc}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Safety banner */}
      <div style={{
        marginTop: 24,
        padding: '14px 20px',
        background: 'rgba(255, 140, 0, 0.06)',
        border: '1px solid rgba(255, 140, 0, 0.3)',
        borderRadius: 'var(--radius)',
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <div style={{ fontSize: 20 }}>⚠️</div>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          <strong style={{ color: 'var(--accent-orange)' }}>Frontend safety constraint: </strong>
          This page only sends <code style={{ color: 'var(--accent-blue)' }}>POST /demo/*</code> actions.
          It never sends <code style={{ color: 'var(--accent-red)' }}>/joints</code>,
          <code style={{ color: 'var(--accent-red)' }}>/motors</code>, or raw angle data.
          The backend robot layer enforces all physical safety limits.
        </div>
      </div>
    </div>
  );
}
