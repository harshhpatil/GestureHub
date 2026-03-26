const { GestureStateMachine, GESTURES } = require('../src/services/gestureService');

describe('GestureStateMachine', () => {
  let machine;

  beforeEach(() => {
    machine = new GestureStateMachine({ requiredFrames: 2, cooldownMs: 100 });
  });

  test('returns null for single frame gesture', () => {
    const result = machine.process(GESTURES.THUMBS_UP, 1.0);
    expect(result).toBeNull();
  });

  test('confirms gesture after required consecutive frames', () => {
    machine.process(GESTURES.THUMBS_UP, 1.0);
    const result = machine.process(GESTURES.THUMBS_UP, 1.0);
    expect(result).not.toBeNull();
    expect(result.gesture).toBe(GESTURES.THUMBS_UP);
    expect(result.action).toBe('VOLUME_UP');
  });

  test('resets on different gesture mid-sequence', () => {
    machine.process(GESTURES.THUMBS_UP, 1.0);
    machine.process(GESTURES.FIST, 1.0);
    const result = machine.process(GESTURES.FIST, 1.0);
    expect(result).not.toBeNull();
    expect(result.gesture).toBe(GESTURES.FIST);
  });

  test('ignores low-confidence frames', () => {
    machine.process(GESTURES.THUMBS_UP, 1.0);
    const result = machine.process(GESTURES.THUMBS_UP, 0.3); // below default 0.7
    expect(result).toBeNull();
  });

  test('respects cooldown after confirmed gesture', () => {
    machine.process(GESTURES.INDEX, 1.0);
    machine.process(GESTURES.INDEX, 1.0); // confirmed
    // Immediately try another gesture
    machine.process(GESTURES.INDEX, 1.0);
    const result = machine.process(GESTURES.INDEX, 1.0);
    expect(result).toBeNull(); // still in cooldown
  });

  test('updateSettings changes sensitivity', () => {
    machine.updateSettings({ sensitivity: 0.9 });
    machine.process(GESTURES.THUMBS_UP, 1.0);
    const result = machine.process(GESTURES.THUMBS_UP, 0.85); // below new 0.9 threshold
    expect(result).toBeNull();
  });

  test('NONE gesture resets pending state', () => {
    machine.process(GESTURES.THUMBS_UP, 1.0);
    machine.process(GESTURES.NONE, 1.0);
    // Need 2 fresh frames
    machine.process(GESTURES.THUMBS_UP, 1.0);
    const result = machine.process(GESTURES.THUMBS_UP, 1.0);
    expect(result).not.toBeNull();
  });
});
