import useAppStore from '../store/useAppStore.js';

export default function ReplayScrubber() {
  const {
    replayFrames, replayStep, replayPlaying,
    setReplayStep, toggleReplayPlay, setReplayPlaying,
  } = useAppStore();

  const total = replayFrames.length;
  const pct = total > 1 ? (replayStep / (total - 1)) * 100 : 0;
  const frame = replayFrames[replayStep];

  if (total === 0) {
    return (
      <div className="panel" style={{ textAlign: 'center', padding: 32 }}>
        <div style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 8 }}>
          No replay data yet
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>
          Run the demo to record episode frames for replay.
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title-dot" style={{ background: 'var(--accent-purple)' }} />
        TIME-SYNCED REPLAY
        <div style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--text-secondary)' }}>
          Frame {replayStep + 1} / {total}
        </div>
      </div>

      {/* Scrubber */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ position: 'relative', height: 24, display: 'flex', alignItems: 'center' }}>
          {/* Track */}
          <div style={{
            position: 'absolute', left: 0, right: 0, height: 4,
            background: 'var(--bg-surface)', borderRadius: 2,
          }} />
          {/* Progress */}
          <div style={{
            position: 'absolute', left: 0, height: 4,
            width: `${pct}%`,
            background: 'linear-gradient(90deg, var(--accent-blue), var(--accent-green))',
            borderRadius: 2,
            transition: 'width 0.1s',
          }} />
          {/* Draggable input */}
          <input
            type="range"
            min={0}
            max={Math.max(0, total - 1)}
            value={replayStep}
            onChange={e => {
              setReplayPlaying(false);
              setReplayStep(Number(e.target.value));
            }}
            style={{
              position: 'absolute', left: 0, right: 0, width: '100%',
              height: '100%', opacity: 0, cursor: 'pointer', zIndex: 1,
            }}
            aria-label="Replay timeline"
          />
          {/* Thumb */}
          <div style={{
            position: 'absolute',
            left: `calc(${pct}% - 8px)`,
            width: 16, height: 16, borderRadius: '50%',
            background: 'var(--accent-blue)',
            border: '2px solid #fff',
            boxShadow: 'var(--glow-blue)',
            transition: 'left 0.1s',
            pointerEvents: 'none',
          }} />
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button
          className="btn"
          style={{ padding: '6px 12px' }}
          onClick={() => { setReplayPlaying(false); setReplayStep(0); }}
          aria-label="Rewind to start"
        >
          ⏮
        </button>
        <button
          className={`btn ${replayPlaying ? '' : 'btn-primary'}`}
          style={{ padding: '6px 16px' }}
          onClick={toggleReplayPlay}
          aria-label={replayPlaying ? 'Pause replay' : 'Play replay'}
        >
          {replayPlaying ? '⏸ Pause' : '▶ Play'}
        </button>
        <button
          className="btn"
          style={{ padding: '6px 12px' }}
          onClick={() => { setReplayPlaying(false); setReplayStep(Math.max(0, replayStep - 1)); }}
          aria-label="Step back"
        >
          ←
        </button>
        <button
          className="btn"
          style={{ padding: '6px 12px' }}
          onClick={() => { setReplayPlaying(false); setReplayStep(Math.min(total - 1, replayStep + 1)); }}
          aria-label="Step forward"
        >
          →
        </button>
      </div>

      {/* Frame data preview */}
      {frame && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          <FrameStat label="Episode" value={frame.metrics?.episode ?? '—'} />
          <FrameStat label="Cost" value={frame.metrics?.cost ?? '—'} />
          <FrameStat
            label="Reasoning"
            value={frame.currentReasoningId || '—'}
            color="var(--accent-purple)"
          />
          <FrameStat
            label="Cube Zone"
            value={frame.scene?.cube_in_bin ? 'BIN ✓' : (frame.scene?.cube_zone ?? '—')}
            color="var(--accent-blue)"
          />
          <FrameStat
            label="Holding"
            value={frame.scene?.holding ? 'YES' : 'NO'}
            color={frame.scene?.holding ? 'var(--accent-green)' : 'var(--text-muted)'}
          />
          <FrameStat
            label="Score"
            value={frame.metrics?.antifragility_score ? `+${frame.metrics.antifragility_score}%` : '—'}
            color="var(--accent-green)"
          />
        </div>
      )}
    </div>
  );
}

function FrameStat({ label, value, color = 'var(--text-primary)' }) {
  return (
    <div style={{
      padding: '8px 10px', background: 'var(--bg-secondary)',
      borderRadius: 6, textAlign: 'center',
    }}>
      <div style={{ fontSize: 13, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 8, color: 'var(--text-muted)', letterSpacing: '0.08em', marginTop: 2 }}>{label}</div>
    </div>
  );
}
