import { useEffect, useRef, useCallback } from 'react';
import useAppStore from './store/useAppStore.js';
import { MockEngine } from './mock/mockEngine.js';
import { hasBackend, checkBackendHealth, connectWebSocket } from './client/backendClient.js';
import TopBar from './components/TopBar.jsx';
import HeroSection from './components/HeroSection.jsx';
import MemoryCards from './components/MemoryCards.jsx';
import AntifragilityChart from './components/AntifragilityChart.jsx';
import ComparisonPanel from './components/ComparisonPanel.jsx';
import ReplayScrubber from './components/ReplayScrubber.jsx';
import ArchitectureSection from './components/ArchitectureSection.jsx';
import SafetyPanel from './components/SafetyPanel.jsx';

export default function App() {
  const {
    applyFrame, applyLiveEvent, resetDemo, setConnectionMode,
    setBackendOnline, setIsRunning, setDemoComplete,
    isRunning, replayFrames, replayStep, replayPlaying,
    setReplayStep, setReplayPlaying,
  } = useAppStore();

  const engineRef = useRef(null);
  const wsRef = useRef(null);
  const replayTimerRef = useRef(null);

  // Initialize engine
  useEffect(() => {
    engineRef.current = new MockEngine(
      (frame) => applyFrame(frame),
      () => {
        setIsRunning(false);
        setDemoComplete(true);
      }
    );

    // Try backend connection
    if (hasBackend()) {
      checkBackendHealth().then((online) => {
        if (online) {
          setConnectionMode('live');
          setBackendOnline(true);
          wsRef.current = connectWebSocket(
            (payload) => applyLiveEvent(payload),
            () => { setConnectionMode('live'); setBackendOnline(true); },
            () => { setConnectionMode('disconnected'); setBackendOnline(false); }
          );
        } else {
          setConnectionMode('disconnected');
          setBackendOnline(false);
        }
      });
    }


    return () => {
      engineRef.current?.stop();
      wsRef.current?.close();
      clearInterval(replayTimerRef.current);
    };
  }, []);

  const startDemo = useCallback(() => {
    engineRef.current?.start(0);
    setIsRunning(true);
    setDemoComplete(false);
  }, [setIsRunning, setDemoComplete]);

  const injectFailure = useCallback((type) => {
    engineRef.current?.injectFailure(type);
    setIsRunning(true);
    setDemoComplete(false);
  }, [setIsRunning, setDemoComplete]);

  const replayLearned = useCallback(() => {
    engineRef.current?.replayLearned();
    setIsRunning(true);
    setDemoComplete(false);
  }, [setIsRunning, setDemoComplete]);

  const handleReset = useCallback(() => {
    engineRef.current?.reset();
    resetDemo();
  }, [resetDemo]);

  // Replay scrubber playback
  useEffect(() => {
    if (replayPlaying) {
      replayTimerRef.current = setInterval(() => {
        const current = useAppStore.getState().replayStep;
        const frames = useAppStore.getState().replayFrames;
        if (current < frames.length - 1) {
          setReplayStep(current + 1);
        } else {
          setReplayPlaying(false);
        }
      }, 300);
    } else {
      clearInterval(replayTimerRef.current);
    }
    return () => clearInterval(replayTimerRef.current);
  }, [replayPlaying, setReplayStep, setReplayPlaying]);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      <TopBar onReset={handleReset} />

      <HeroSection
        onRunDemo={startDemo}
        onInjectFailure={injectFailure}
        onReplayLearned={replayLearned}
        onReset={handleReset}
      />

      <hr className="divider" />

      <div className="section" id="memory">
        <div className="section-title">Learned Reflexes</div>
        <div className="section-subtitle">
          What the robot has saved to memory after recovering from failures.
        </div>
        <MemoryCards />
      </div>

      <hr className="divider" />

      <div className="section" id="chart">
        <div className="section-title">Antifragility Chart</div>
        <div className="section-subtitle">
          Episode cost over time — watch it drop after the reflex is learned.
        </div>
        <div className="chart-grid">
          <AntifragilityChart />
          <ComparisonPanel />
        </div>
      </div>

      <hr className="divider" />

      <div className="section" id="replay">
        <div className="section-title">Timeline Replay</div>
        <div className="section-subtitle">
          Scrub through the full fail → recover → learn sequence.
        </div>
        <ReplayScrubber />
      </div>

      <hr className="divider" />

      <div className="section" id="architecture">
        <ArchitectureSection />
      </div>

      <hr className="divider" />

      <div className="section" id="safety">
        <SafetyPanel />
      </div>

      <footer style={{
        textAlign: 'center',
        padding: '32px 24px',
        color: 'var(--text-muted)',
        fontSize: 11,
        letterSpacing: '0.08em',
        borderTop: '1px solid var(--border)',
      }}>
        ReflexOS · MISSION CONTROL · EUROTECH HACKATHON · FRONTEND ONLY · MOCK MODE
      </footer>
    </div>
  );
}
