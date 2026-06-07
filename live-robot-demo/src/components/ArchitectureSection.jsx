export default function ArchitectureSection() {
  const nodes = [
    {
      label: 'React Landing Page',
      sub: 'This page — 3D view, panels, mock demo',
      color: 'var(--accent-blue)',
    },
    {
      label: 'Robot Teaching Backend',
      sub: 'VITE_BACKEND_URL — REST + WebSocket',
      color: 'var(--accent-purple)',
    },
    {
      label: 'AI Reasoning + Memory',
      sub: 'Black-swan detection · reflex storage',
      color: 'var(--accent-orange)',
    },
    {
      label: 'SO-101 Robot / Simulator',
      sub: 'Physical arm or simulation mode',
      color: 'var(--accent-green)',
    },
  ];

  return (
    <div>
      <div className="section-title">System Architecture</div>
      <div className="section-subtitle">
        This landing page plugs into the robot teaching backend via a single URL.
        It works fully in mock mode and switches to live mode when the backend is available.
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 48, alignItems: 'start' }}>
        {/* Diagram */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>
          {nodes.map((node, i) => (
            <div key={node.label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
              <div style={{
                width: '100%', maxWidth: 260,
                padding: '14px 18px',
                background: 'var(--bg-card)',
                border: `1px solid ${node.color}55`,
                borderRadius: 'var(--radius)',
                textAlign: 'center',
                position: 'relative',
              }}>
                <div style={{
                  position: 'absolute', top: 0, left: 0, right: 0, height: 2,
                  background: node.color, borderRadius: '8px 8px 0 0',
                }} />
                <div style={{ fontWeight: 700, fontSize: 12, color: node.color, marginBottom: 4 }}>
                  {node.label}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.4 }}>
                  {node.sub}
                </div>
              </div>
              {i < nodes.length - 1 && (
                <div style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2px 0',
                }}>
                  <div style={{ width: 1.5, height: 12, background: 'var(--border)' }} />
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', padding: '2px 6px' }}>
                    {i === 0 ? 'REST + WebSocket' : i === 1 ? 'tool calls + memory' : 'joint commands'}
                  </div>
                  <div style={{ width: 1.5, height: 12, background: 'var(--border)' }} />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <DetailBlock
            title="Mock Mode (default)"
            color="var(--accent-purple)"
            items={[
              'Page loads immediately with simulated 3D robot, events, and metrics.',
              'Full 3-episode story plays automatically: success → failure → reflex.',
              'No backend URL required — works offline.',
              'All controls (Run Demo, Inject Failure, Replay, Reset) work in mock mode.',
            ]}
          />
          <DetailBlock
            title="Live Mode (when VITE_BACKEND_URL is set)"
            color="var(--accent-green)"
            items={[
              'Page calls GET /state on load to initialize robot joint state.',
              'WebSocket /events streams live joint positions, events, and metrics.',
              'Falls back to polling GET /state if WebSocket is unavailable.',
              'If backend goes offline, page switches to disconnected state and continues mock demo.',
            ]}
          />
          <DetailBlock
            title="Safety Boundary"
            color="var(--accent-orange)"
            items={[
              'Frontend never sends raw motor angles or direct joint commands.',
              'Only high-level demo actions: /demo/run, /demo/inject-failure, /demo/replay, /demo/reset.',
              'Backend owns all safety limits and motor validation.',
              'E-stop button always visible in the top bar.',
            ]}
          />
        </div>
      </div>
    </div>
  );
}

function DetailBlock({ title, color, items }) {
  return (
    <div style={{
      padding: '16px 18px',
      background: 'var(--bg-card)',
      border: `1px solid ${color}33`,
      borderRadius: 'var(--radius)',
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ fontSize: 12, fontWeight: 700, color, marginBottom: 10 }}>{title}</div>
      <ul style={{ paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 6 }}>
        {items.map(item => (
          <li key={item} style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
