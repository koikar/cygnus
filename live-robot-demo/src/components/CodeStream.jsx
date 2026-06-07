import { useEffect, useRef } from 'react';
import useAppStore from '../store/useAppStore.js';

const TYPE_STYLE = {
  action:    { color: 'var(--accent-blue)',   prefix: '→' },
  system:    { color: 'var(--text-muted)',     prefix: '#' },
  error:     { color: 'var(--accent-red)',     prefix: '✗' },
  failure:   { color: 'var(--accent-orange)',  prefix: '!' },
  reasoning: { color: 'var(--accent-yellow)',  prefix: '?' },
  recovery:  { color: 'var(--accent-purple)',  prefix: '↺' },
  learn:     { color: 'var(--accent-green)',   prefix: '★' },
  reflex:    { color: 'var(--accent-green)',   prefix: '⚡' },
  success:   { color: 'var(--accent-green)',   prefix: '✓' },
};

function StreamEntry({ entry, isLatest }) {
  const style = TYPE_STYLE[entry.type] || TYPE_STYLE.action;
  return (
    <div
      className={isLatest ? 'slide-in' : ''}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 8,
        padding: '4px 8px',
        borderRadius: 4,
        background: isLatest ? 'rgba(45, 140, 240, 0.06)' : 'transparent',
        borderLeft: isLatest ? `2px solid ${style.color}` : '2px solid transparent',
        transition: 'all 0.2s',
      }}
    >
      <span style={{ color: style.color, fontSize: 10, minWidth: 12, paddingTop: 1 }}>
        {style.prefix}
      </span>
      <span style={{ color: isLatest ? style.color : 'var(--text-secondary)', fontSize: 11, flex: 1, lineHeight: 1.5 }}>
        {entry.cmd}
      </span>
    </div>
  );
}

export default function CodeStream() {
  const eventStream = useAppStore(s => s.eventStream);
  const publicMode = useAppStore(s => s.publicMode);
  const scrollRef = useRef();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [eventStream]);

  const publicTranslations = {
    'look()': 'The robot scans the workspace',
    'move_to(zone_A)': 'Moving to expected position A',
    'move_to(zone_A)  [habit]': 'Using remembered habit to move to A',
    'move_to(zone_B)': 'Redirecting to zone B',
    'move_to(zone_B)  [reflex direct]': 'Going straight to B — memory shortcut!',
    'grip(close)  ✓': 'Gripper closed successfully',
    'grip(close)  ✗  EMPTY GRIPPER': 'Failure! Gripper closed on nothing',
    'grip(close)  ✓  [zone B]': 'Gripper closed — cube found at B',
    'move_to(bin)': 'Moving cube to the bin',
    'release()  ✓': 'Released cube in bin',
    'black_swan_detected: empty_gripper': 'Unexpected failure detected',
    'system2_reasoning(active)': 'AI is thinking hard to find a solution',
    'recover: move_to(zone_B)': 'AI found it! Going to zone B instead',
    'memory.upsert(signature="cube@B")': 'Saving this fix to long-term memory',
    'reflex_recall(signature="cube@B")  ⚡': 'Memory found! Using shortcut instead of thinking',
    'antifragility_demonstrated: cost 8→4 (-50%)': 'System is now 50% faster than before!',
  };

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div className="panel-title-dot" style={{ background: 'var(--accent-blue)' }} />
        {publicMode ? 'WHAT IS HAPPENING' : 'LIVE TOOL-CALL STREAM'}
        <div style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--text-muted)' }}>
          {eventStream.length} events
        </div>
      </div>

      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          maxHeight: 220,
        }}
      >
        {eventStream.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 11, padding: '12px 8px' }}>
            Waiting for demo to start...
          </div>
        ) : eventStream.map((entry, i) => {
          const isLatest = i === eventStream.length - 1;
          const displayEntry = publicMode
            ? { ...entry, cmd: publicTranslations[entry.cmd] || entry.cmd }
            : entry;
          return (
            <StreamEntry key={entry.id} entry={displayEntry} isLatest={isLatest} />
          );
        })}
      </div>
    </div>
  );
}
