/**
 * Omni-Bridge Centralized Application State Manager
 */

export const state = {
  activeMainView: 'command',
  activeInputTab: 'text',
  recordedBlob: null,
  mediaRecorder: null,
  audioChunks: [],
  recordingInterval: null,
  recordingSeconds: 0,
  gcsSamplesLoaded: false,
  sessionFeed: [],
  hitlPendingCount: 0,
  hitlVerifiedCount: 0,

  listeners: new Set(),

  subscribe(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  },

  notify() {
    this.listeners.forEach(fn => fn(this));
  }
};
