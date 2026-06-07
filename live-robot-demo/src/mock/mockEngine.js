import { MOCK_SEQUENCE, INJECT_FAILURE_TYPES } from './mockSequence.js';

// Drives the mock demo sequence and calls store actions over time.
export class MockEngine {
  constructor(applyFrame, onComplete) {
    this.applyFrame = applyFrame;
    this.onComplete = onComplete;
    this.timer = null;
    this.currentIndex = 0;
    this.running = false;
    this.paused = false;
  }

  start(fromIndex = 0) {
    this.currentIndex = fromIndex;
    this.running = true;
    this.paused = false;
    this._scheduleNext();
  }

  pause() {
    this.paused = true;
    if (this.timer) clearTimeout(this.timer);
  }

  resume() {
    if (this.running && this.paused) {
      this.paused = false;
      this._scheduleNext();
    }
  }

  stop() {
    this.running = false;
    this.paused = false;
    if (this.timer) clearTimeout(this.timer);
  }

  reset() {
    this.stop();
    this.currentIndex = 0;
  }

  _scheduleNext() {
    if (!this.running || this.paused) return;
    if (this.currentIndex >= MOCK_SEQUENCE.length) {
      this.running = false;
      if (this.onComplete) this.onComplete();
      return;
    }
    const frame = MOCK_SEQUENCE[this.currentIndex];
    this.applyFrame(frame);
    this.currentIndex++;
    this.timer = setTimeout(() => this._scheduleNext(), frame.duration);
  }

  // Jump to episode 2 (failure sequence) for inject failure
  injectFailure(type) {
    this.stop();
    const ep2Start = MOCK_SEQUENCE.findIndex(f => f.id === 'ep2_start');
    if (ep2Start >= 0) {
      this.start(ep2Start);
    }
  }

  // Jump to episode 3 (reflex sequence)
  replayLearned() {
    this.stop();
    const ep3Start = MOCK_SEQUENCE.findIndex(f => f.id === 'ep3_start');
    if (ep3Start >= 0) {
      this.start(ep3Start);
    }
  }
}
