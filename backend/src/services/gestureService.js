/**
 * Gesture Service
 * Implements gesture state machine logic and maps gestures to device actions.
 */

// Supported gesture types
const GESTURES = {
  THUMBS_UP: 'THUMBS_UP',
  THUMBS_DOWN: 'THUMBS_DOWN',
  PEACE: 'PEACE',
  OPEN_PALM: 'OPEN_PALM',
  FIST: 'FIST',
  INDEX: 'INDEX',
  ROCK: 'ROCK',
  TWO_FINGERS: 'TWO_FINGERS',
  NONE: 'NONE',
};

// Gesture → action mapping
const GESTURE_ACTION_MAP = {
  [GESTURES.THUMBS_UP]:   { action: 'VOLUME_UP',   device: 'all' },
  [GESTURES.THUMBS_DOWN]: { action: 'VOLUME_DOWN',  device: 'all' },
  [GESTURES.PEACE]:       { action: 'NEXT_TRACK',   device: 'all' },
  [GESTURES.OPEN_PALM]:   { action: 'RESET',        device: 'all' },
  [GESTURES.FIST]:        { action: 'PLAY_PAUSE',   device: 'all' },
  [GESTURES.INDEX]:       { action: 'TOGGLE_LED',   device: 'esp32' },
  [GESTURES.ROCK]:        { action: 'TOGGLE_MOTOR', device: 'esp32' },
  [GESTURES.TWO_FINGERS]: { action: 'SWIPE',        device: 'all' },
};

// State machine states
const SM_STATES = {
  IDLE: 'IDLE',
  DETECTING: 'DETECTING',
  CONFIRMED: 'CONFIRMED',
  COOLDOWN: 'COOLDOWN',
};

class GestureStateMachine {
  constructor(options = {}) {
    this.state = SM_STATES.IDLE;
    this.currentGesture = GESTURES.NONE;
    this.pendingGesture = GESTURES.NONE;
    this.consecutiveFrames = 0;
    this.requiredFrames = options.requiredFrames || 2;
    this.cooldownMs = options.cooldownMs || 300;
    this.lastActionAt = 0;
    this.sensitivity = options.sensitivity || 0.7;
    this.tremorFilter = options.tremorFilter || false;
    this.tremorWindowMs = 150;
    this.recentGestures = [];
  }

  /**
   * Process a new gesture frame.
   * Returns an action object if a gesture is confirmed, otherwise null.
   */
  process(gesture, confidence = 1.0) {
    const now = Date.now();

    // Confidence gate
    if (confidence < this.sensitivity) {
      return this._reset();
    }

    // Tremor filter: if too many different gestures in a short window, ignore
    if (this.tremorFilter) {
      this.recentGestures.push({ gesture, time: now });
      this.recentGestures = this.recentGestures.filter(
        (g) => now - g.time < this.tremorWindowMs
      );
      const unique = new Set(this.recentGestures.map((g) => g.gesture));
      if (unique.size > 2) {
        return this._reset();
      }
    }

    // Cooldown gate
    if (this.state === SM_STATES.COOLDOWN) {
      if (now - this.lastActionAt < this.cooldownMs) {
        return null;
      }
      this.state = SM_STATES.IDLE;
    }

    if (gesture === GESTURES.NONE) {
      return this._reset();
    }

    if (gesture !== this.pendingGesture) {
      // New gesture — start counting
      this.pendingGesture = gesture;
      this.consecutiveFrames = 1;
      this.state = SM_STATES.DETECTING;
      return null;
    }

    // Same gesture as pending
    this.consecutiveFrames += 1;

    if (this.consecutiveFrames >= this.requiredFrames) {
      // Gesture confirmed
      this.currentGesture = gesture;
      this.state = SM_STATES.COOLDOWN;
      this.lastActionAt = now;
      this.consecutiveFrames = 0;
      return this._buildAction(gesture);
    }

    return null;
  }

  _reset() {
    if (this.state !== SM_STATES.COOLDOWN) {
      this.pendingGesture = GESTURES.NONE;
      this.consecutiveFrames = 0;
      this.state = SM_STATES.IDLE;
    }
    return null;
  }

  _buildAction(gesture) {
    const mapping = GESTURE_ACTION_MAP[gesture];
    if (!mapping) return null;
    return {
      gesture,
      action: mapping.action,
      device: mapping.device,
      timestamp: Date.now(),
    };
  }

  updateSettings(settings) {
    if (settings.sensitivity !== undefined) this.sensitivity = settings.sensitivity;
    if (settings.cooldownMs !== undefined) this.cooldownMs = settings.cooldownMs;
    if (settings.tremorFilter !== undefined) this.tremorFilter = settings.tremorFilter;
    if (settings.requiredFrames !== undefined) this.requiredFrames = settings.requiredFrames;
  }

  getState() {
    return {
      state: this.state,
      currentGesture: this.currentGesture,
      pendingGesture: this.pendingGesture,
      consecutiveFrames: this.consecutiveFrames,
    };
  }
}

// Singleton per-user state machines
const userMachines = new Map();

function getMachine(userId, preferences = {}) {
  if (!userMachines.has(userId)) {
    userMachines.set(userId, new GestureStateMachine({
      sensitivity: preferences.sensitivity || 0.7,
      cooldownMs: preferences.gesture_delay_ms || 300,
      tremorFilter: preferences.tremor_filter === 1,
    }));
  }
  return userMachines.get(userId);
}

function removeMachine(userId) {
  userMachines.delete(userId);
}

module.exports = {
  GESTURES,
  GESTURE_ACTION_MAP,
  GestureStateMachine,
  getMachine,
  removeMachine,
};
