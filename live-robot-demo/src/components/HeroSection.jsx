import { lazy, Suspense } from 'react';
import useAppStore from '../store/useAppStore.js';
import DemoControls from './DemoControls.jsx';
import CodeStream from './CodeStream.jsx';
import ReasoningPanel from './ReasoningPanel.jsx';
import PerceptionPanel from './PerceptionPanel.jsx';

const Robot3D = lazy(() => import('./Robot3D.jsx'));

function MetricsBadge({ label, value, color = 'var(--text-primary)', large = false }) {
  return (
    <div style={{
      padding: large ? '10px 16px' : '8px 12px',
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius)',
      textAlign: 'center',
      flex: 1,
    }}>
      <div style={{
        fontSize: large ? 22 : 18,
        fontWeight: 800,
        color,
        lineHeight: 1,
        marginBottom: 3,
      }}>
        {value}
      </div>
      <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
        {label}
      </div>
    </div>
  );
}

function Robot3DFallback() {
  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-card)',
      borderRadius: 'var(--radius)',
      gap: 16, color: 'var(--text-muted)', fontSize: 12,
    }}>
      <div style={{ fontSize: 48 }}>🤖</div>
      <div>Loading 3D robot...</div>
    </div>
  );
}

export default function HeroSection({ onRunDemo, onInjectFailure, onReplayLearned, onReset }) {
  const metrics = useAppStore(s => s.metrics);
  const currentEvent = useAppStore(s => s.currentEvent);
  const publicMode = useAppStore(s => s.publicMode);

  const eventTypeColor = {
    black_swan_detected: 'var(--accent-red)',
    error: 'var(--accent-red)',
    failure: 'var(--accent-orange)',
    recovery: 'var(--accent-purple)',
    learn: 'var(--accent-green)',
    reflex: 'var(--accent-green)',
    success: 'var(--accent-green)',
  };

  return (
    <section style={{ padding: '16px 16px 24px', maxWidth: 1440, margin: '0 auto' }}>

      {/* Tagline */}
      <div style={{ marginBottom: 14 }}>
        <h1 style={{
          fontSize: 'clamp(18px, 2.5vw, 28px)',
          fontWeight: 800,
          letterSpacing: '0.02em',
          color: 'var(--text-primary)',
          marginBottom: 4,
        }}>
          <span style={{ color: '#f5f5f5' }}>Reflex</span>
          <span style={{ color: '#f59e0b' }}>OS</span>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 400, fontSize: '0.7em', marginLeft: 12 }}>
            A robot arm that learns from rare failures.
          </span>
        </h1>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', letterSpacing: '0.06em' }}>
          {publicMode
            ? 'The robot tries → fails → AI finds why → robot learns → next attempt is faster.'
            : 'habit_plan → black_swan_detector → system2_recovery → memory.upsert → reflex_recall'
          }
        </div>
      </div>

      {/* Live event banner */}
      {currentEvent && (
        <div style={{
          marginBottom: 12,
          padding: '8px 14px',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius)',
          border: `1px solid ${eventTypeColor[currentEvent.type] || 'var(--border)'}44`,
          borderLeft: `3px solid ${eventTypeColor[currentEvent.type] || 'var(--accent-blue)'}`,
          display: 'flex', alignItems: 'center', gap: 10,
          fontSize: 11, color: 'var(--text-primary)',
        }}>
          <div className="pulse" style={{
            background: eventTypeColor[currentEvent.type] || 'var(--accent-blue)',
            flexShrink: 0,
          }} />
          <span style={{ color: eventTypeColor[currentEvent.type] || 'var(--accent-blue)', fontWeight: 600 }}>
            {currentEvent.type?.toUpperCase().replace('_', ' ')}
          </span>
          <span style={{ color: 'var(--text-secondary)', fontSize: 10 }}>
            {currentEvent.message}
          </span>
        </div>
      )}

      {/* Main grid: 3D left, panels right */}
      <div className="hero-grid" style={{ marginBottom: 12 }}>

        {/* Left: 3D Robot */}
        <div style={{
          height: 'clamp(480px, 68vh, 700px)',
          borderRadius: 'var(--radius)',
          border: '1px solid var(--border)',
          overflow: 'hidden',
          position: 'relative',
        }}>
          <Suspense fallback={<Robot3DFallback />}>
            <Robot3D />
          </Suspense>

          {/* Bottom bar — model label + sim status, clearly separated */}
          <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0,
            background: 'linear-gradient(transparent, rgba(4,9,18,0.92))',
            padding: '28px 14px 10px',
            pointerEvents: 'none',
            display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '4px 10px',
              background: 'rgba(6,11,24,0.7)',
              borderRadius: 20,
              border: '1px solid rgba(45,140,240,0.2)',
              backdropFilter: 'blur(6px)',
            }}>
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <circle cx="5" cy="5" r="4" stroke="#2d8cf0" strokeWidth="1.2" />
                <circle cx="5" cy="5" r="1.8" fill="#2d8cf0" />
              </svg>
              <span style={{ fontSize: 9, color: 'var(--text-secondary)', letterSpacing: '0.1em' }}>
                SO-101 DIGITAL TWIN
              </span>
              <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>·</span>
              <span style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
                DRAG TO ROTATE
              </span>
            </div>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '4px 10px',
              background: 'rgba(6,11,24,0.7)',
              borderRadius: 20,
              border: '1px solid rgba(0,214,143,0.2)',
              backdropFilter: 'blur(6px)',
            }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: 'var(--accent-green)',
                animation: 'pulse 1.5s ease-in-out infinite',
              }} />
              <span style={{ fontSize: 9, color: 'var(--accent-green)', fontWeight: 600, letterSpacing: '0.08em' }}>
                SIMULATION
              </span>
            </div>
          </div>
        </div>

        {/* Right panel column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minWidth: 0 }}>

          {/* Metrics strip */}
          <div style={{ display: 'flex', gap: 8 }}>
            <MetricsBadge
              label="EPISODE"
              value={metrics.episode || '—'}
              color="var(--accent-blue)"
            />
            <MetricsBadge
              label="COST"
              value={metrics.cost ?? '—'}
              color={metrics.cost >= 6 ? 'var(--accent-orange)' : 'var(--accent-green)'}
            />
            <MetricsBadge
              label="ANTIFRAGILITY"
              value={metrics.antifragility_score ? `+${metrics.antifragility_score}%` : '—'}
              color="var(--accent-green)"
            />
          </div>

          {/* Demo Controls */}
          <div style={{ flex: '0 0 auto' }}>
            <DemoControls
              onRunDemo={onRunDemo}
              onInjectFailure={onInjectFailure}
              onReplayLearned={onReplayLearned}
              onReset={onReset}
            />
          </div>

          {/* Perception Panel */}
          <div style={{ flex: 1, minHeight: 160 }}>
            <PerceptionPanel />
          </div>
        </div>
      </div>

      {/* Bottom row: Code stream + Reasoning */}
      <div className="hero-bottom-grid">
        <CodeStream />
        <ReasoningPanel />
      </div>
    </section>
  );
}
