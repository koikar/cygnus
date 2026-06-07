import { useState, useRef, useEffect } from 'react';
import useAppStore from '../store/useAppStore.js';
import { INJECT_FAILURE_TYPES } from '../mock/mockSequence.js';
import {
  hasBackend, postDemoRun, postInjectFailure, postReplay, postReset,
} from '../client/backendClient.js';

export default function DemoControls({ onRunDemo, onInjectFailure, onReplayLearned, onReset }) {
  const { connectionMode, isRunning, demoComplete, backendOnline } = useAppStore();
  const [loading, setLoading] = useState(null);
  const [showFailureMenu, setShowFailureMenu] = useState(false);
  const [showBackendInfo, setShowBackendInfo] = useState(false);
  const menuRef = useRef();
  const isLive = connectionMode === 'live' && backendOnline;

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowFailureMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const withLoading = (key, fn) => async () => {
    if (loading) return;
    setLoading(key);
    try { await fn(); } catch (e) { console.warn('Action error:', e); }
    finally { setLoading(null); }
  };

  const handleRun = withLoading('run', async () => {
    if (isLive) await postDemoRun();
    onRunDemo();
  });

  const handleFailure = (type) => withLoading('failure', async () => {
    setShowFailureMenu(false);
    if (isLive) await postInjectFailure(type.id);
    onInjectFailure(type.id);
  })();

  const handleReplay = withLoading('replay', async () => {
    if (isLive) await postReplay();
    onReplayLearned();
  });

  const handleReset = withLoading('reset', async () => {
    if (isLive) await postReset();
    onReset();
  });

  const Btn = ({ id, label, cls = '', onClick, disabled, icon }) => (
    <button
      className={`btn ${cls}`}
      onClick={onClick}
      disabled={disabled || loading === id}
      aria-label={label}
      style={{ justifyContent: 'center' }}
    >
      {loading === id ? <div className="spinner" /> : icon}
      {label}
    </button>
  );

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 0 }}>
      <div className="panel-header">
        <div className="panel-title-dot" />
        DEMO CONTROLS
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
        <Btn
          id="run"
          label="Run Demo"
          cls="btn-primary"
          onClick={handleRun}
          disabled={isRunning}
          icon="▶"
        />

        {/* Inject Failure with dropdown */}
        <div ref={menuRef} style={{ position: 'relative' }}>
          <button
            className="btn btn-danger"
            onClick={() => setShowFailureMenu(v => !v)}
            disabled={!!loading}
            style={{ width: '100%', justifyContent: 'space-between' }}
            aria-label="Inject failure"
            aria-expanded={showFailureMenu}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {loading === 'failure' ? <div className="spinner" /> : '⚡'}
              Inject Failure
            </span>
            <span style={{ fontSize: 10, opacity: 0.7 }}>{showFailureMenu ? '▲' : '▼'}</span>
          </button>

          {showFailureMenu && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 4px)',
              left: 0, right: 0,
              background: 'var(--bg-card)',
              border: '1px solid var(--accent-orange)',
              borderRadius: 'var(--radius)',
              overflow: 'hidden',
              zIndex: 50,
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}>
              {INJECT_FAILURE_TYPES.map(type => (
                <button
                  key={type.id}
                  onClick={() => handleFailure(type)}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    padding: '10px 14px', background: 'transparent',
                    border: 'none', borderBottom: '1px solid var(--border)',
                    color: 'var(--text-primary)', fontFamily: 'inherit',
                    cursor: 'pointer', fontSize: 11,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-surface)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ fontWeight: 600, marginBottom: 2 }}>{type.label}</div>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{type.description}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        <Btn
          id="replay"
          label="Replay Learned Fix"
          cls="btn-success"
          onClick={handleReplay}
          disabled={!!loading}
          icon="⚡"
        />

        <Btn
          id="reset"
          label="Reset"
          onClick={handleReset}
          disabled={!!loading}
          icon="↺"
        />

        {/* Backend connect area */}
        <div style={{ marginTop: 'auto', paddingTop: 8, borderTop: '1px solid var(--border)' }}>
          <button
            className="btn"
            style={{ width: '100%', justifyContent: 'space-between', fontSize: 10 }}
            onClick={() => setShowBackendInfo(v => !v)}
          >
            <span>Connect Backend</span>
            <span style={{
              fontSize: 9,
              color: backendOnline ? 'var(--accent-green)' : hasBackend() ? 'var(--accent-red)' : 'var(--text-muted)',
            }}>
              {backendOnline ? '● LIVE' : hasBackend() ? '● OFFLINE' : '● MOCK'}
            </span>
          </button>

          {showBackendInfo && (
            <div style={{
              marginTop: 8, padding: 10,
              background: 'var(--bg-secondary)', borderRadius: 6,
              fontSize: 10, color: 'var(--text-secondary)', lineHeight: 1.8,
            }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>Set env variable:</div>
              <code style={{ color: 'var(--accent-green)', display: 'block', marginBottom: 6 }}>
                VITE_BACKEND_URL=https://your-backend.url
              </code>
              <div style={{ color: 'var(--text-muted)' }}>
                Then rebuild. The page will use REST + WebSocket automatically.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
