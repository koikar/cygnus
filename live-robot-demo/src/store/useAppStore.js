import { create } from 'zustand';
import {
  INITIAL_JOINTS,
  INITIAL_SCENE,
  INITIAL_METRICS,
  INITIAL_MEMORY,
  INITIAL_REASONING_STEPS,
} from '../mock/mockSequence.js';

const MAX_STREAM_ENTRIES = 80;

const useAppStore = create((set, get) => ({
  // Connection state
  connectionMode: 'mock', // 'mock' | 'live' | 'disconnected'
  backendOnline: false,
  isRunning: false,
  demoComplete: false,

  // Robot state
  joints: { ...INITIAL_JOINTS },
  scene: { ...INITIAL_SCENE },

  // Current event
  currentEvent: null,

  // Code/tool-call stream
  eventStream: [],

  // AI reasoning
  reasoningSteps: INITIAL_REASONING_STEPS.map(s => ({ ...s })),
  currentReasoningId: null,
  reasoningRationale: '',

  // Memory cards
  memoryCards: [],
  learnedReflexes: 0,

  // Metrics
  metrics: { ...INITIAL_METRICS },
  episodeHistory: [],

  // Public/technical mode
  publicMode: false,

  // Replay scrubber
  replayFrames: [],
  replayStep: 0,
  replayPlaying: false,

  // ── Actions ───────────────────────────────────────────────────────────────

  setConnectionMode: (mode) => set({ connectionMode: mode }),
  setBackendOnline: (v) => set({ backendOnline: v }),
  setIsRunning: (v) => set({ isRunning: v }),
  setPublicMode: (v) => set({ publicMode: v }),

  // Apply a frame from the mock engine or backend WebSocket
  applyFrame: (frame) => set((state) => {
    const next = { currentEvent: frame.event || state.currentEvent };

    // Joints
    if (frame.joints) next.joints = { ...state.joints, ...frame.joints };

    // Scene
    if (frame.scene) next.scene = { ...state.scene, ...frame.scene };

    // Tool-call stream
    if (frame.toolCall) {
      const entry = {
        id: Date.now() + Math.random(),
        ...frame.toolCall,
        timestamp: new Date().toISOString(),
        isNew: true,
      };
      const stream = [...state.eventStream, entry].slice(-MAX_STREAM_ENTRIES);
      next.eventStream = stream;
    }

    // Reasoning
    if (frame.reasoningStep || frame.resetReasoning) {
      let steps = frame.resetReasoning
        ? INITIAL_REASONING_STEPS.map(s => ({ ...s }))
        : state.reasoningSteps.map(s => ({ ...s }));

      if (frame.reasoningStep) {
        const idx = steps.findIndex(s => s.id === frame.reasoningStep);
        steps = steps.map((s, i) => ({
          ...s,
          done: i < idx,
          active: i === idx,
        }));
        next.currentReasoningId = frame.reasoningStep;
      }
      next.reasoningSteps = steps;
      if (frame.reasoning) next.reasoningRationale = frame.reasoning.rationale || '';
    }

    // Metrics
    if (frame.metrics) {
      next.metrics = { ...state.metrics, ...frame.metrics };
    }

    // Episode result → history
    if (frame.episodeResult) {
      const exists = state.episodeHistory.find(e => e.episode === frame.episodeResult.episode);
      if (!exists) {
        next.episodeHistory = [...state.episodeHistory, frame.episodeResult];
      }
    }

    // New memory card
    if (frame.newMemoryCard) {
      const exists = state.memoryCards.find(c => c.signature === frame.newMemoryCard.signature);
      if (!exists) {
        next.memoryCards = [...state.memoryCards, { ...frame.newMemoryCard, uses: 0 }];
        next.learnedReflexes = state.learnedReflexes + 1;
      }
    }

    // Update memory card usage count
    if (frame.updateMemoryCardUses) {
      next.memoryCards = state.memoryCards.map(c =>
        c.signature === frame.updateMemoryCardUses
          ? { ...c, uses: c.uses + 1 }
          : c
      );
    }

    // Snapshot for replay
    const replayFrame = {
      joints: next.joints || state.joints,
      scene: next.scene || state.scene,
      reasoningSteps: next.reasoningSteps || state.reasoningSteps,
      metrics: next.metrics || state.metrics,
      streamLength: (next.eventStream || state.eventStream).length,
      currentReasoningId: next.currentReasoningId || state.currentReasoningId,
    };
    next.replayFrames = [...state.replayFrames, replayFrame];
    next.replayStep = next.replayFrames.length - 1;

    return next;
  }),

  // Reset everything
  resetDemo: () => set({
    joints: { ...INITIAL_JOINTS },
    scene: { ...INITIAL_SCENE },
    currentEvent: null,
    eventStream: [],
    reasoningSteps: INITIAL_REASONING_STEPS.map(s => ({ ...s })),
    currentReasoningId: null,
    reasoningRationale: '',
    memoryCards: [],
    learnedReflexes: 0,
    metrics: { ...INITIAL_METRICS },
    episodeHistory: [],
    isRunning: false,
    demoComplete: false,
    replayFrames: [],
    replayStep: 0,
    replayPlaying: false,
  }),

  setDemoComplete: (v) => set({ demoComplete: v }),

  // Replay scrubber
  setReplayStep: (n) => set((state) => {
    const frame = state.replayFrames[n];
    if (!frame) return {};
    return {
      replayStep: n,
      joints: frame.joints,
      scene: frame.scene,
      reasoningSteps: frame.reasoningSteps,
      metrics: frame.metrics,
      currentReasoningId: frame.currentReasoningId,
    };
  }),

  toggleReplayPlay: () => set((state) => ({ replayPlaying: !state.replayPlaying })),
  setReplayPlaying: (v) => set({ replayPlaying: v }),

  // Apply live backend event payload
  applyLiveEvent: (payload) => set((state) => {
    const next = {};
    if (payload.joints) next.joints = { ...state.joints, ...payload.joints };
    if (payload.scene) next.scene = { ...state.scene, ...payload.scene };
    if (payload.metrics) next.metrics = { ...state.metrics, ...payload.metrics };
    if (payload.event) {
      next.currentEvent = payload.event;
      const entry = {
        id: Date.now() + Math.random(),
        cmd: payload.event.message,
        type: payload.event.type,
        timestamp: new Date().toISOString(),
        isNew: true,
      };
      next.eventStream = [...state.eventStream, entry].slice(-MAX_STREAM_ENTRIES);
    }
    if (payload.memory?.latest_reflex) {
      next.learnedReflexes = payload.memory.learned_reflexes || state.learnedReflexes;
    }
    return next;
  }),
}));

export default useAppStore;
