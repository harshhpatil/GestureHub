const WebSocket = require('ws');
const config = require('../config/env');

const DEVICE_COMMANDS = {
  LED_RED_ON:    { type: 'LED', pin: 'RED',   state: true },
  LED_RED_OFF:   { type: 'LED', pin: 'RED',   state: false },
  LED_BLUE_ON:   { type: 'LED', pin: 'BLUE',  state: true },
  LED_BLUE_OFF:  { type: 'LED', pin: 'BLUE',  state: false },
  LED_GREEN_ON:  { type: 'LED', pin: 'GREEN', state: true },
  LED_GREEN_OFF: { type: 'LED', pin: 'GREEN', state: false },
  MOTOR_ON:      { type: 'MOTOR', speed: 200, direction: 'forward' },
  MOTOR_OFF:     { type: 'MOTOR', speed: 0,   direction: 'stop' },
  RESET:         { type: 'RESET' },
};

// Map gesture actions to ESP32 commands
const ACTION_TO_COMMAND = {
  TOGGLE_LED:   ['LED_RED_ON', 'LED_BLUE_ON', 'LED_GREEN_ON'],
  TOGGLE_MOTOR: ['MOTOR_ON'],
  RESET:        ['RESET'],
  PLAY_PAUSE:   ['LED_BLUE_ON'],
  VOLUME_UP:    ['LED_GREEN_ON'],
  VOLUME_DOWN:  ['LED_RED_ON'],
};

class ESP32Service {
  constructor() {
    this.ws = null;
    this.deviceState = {
      led_red: false,
      led_blue: false,
      led_green: false,
      motor: false,
      connected: false,
    };
    this.reconnectTimer = null;
    this.reconnectDelay = 3000;
    this.maxReconnectDelay = 30000;
    this.listeners = new Set();
  }

  connect(host, port, secure = false) {
    if (!host) return;

    const protocol = secure ? 'wss' : 'ws';
    const url = `${protocol}://${host}:${port}${config.ESP32_WS_PATH}`;
    console.log(`[ESP32] Connecting to ${url}`);

    try {
      this.ws = new WebSocket(url);

      this.ws.on('open', () => {
        console.log('[ESP32] Connected');
        this.deviceState.connected = true;
        this.reconnectDelay = 3000;
        this._emit('connected', { host, port });
        // Request current state
        this._send({ type: 'GET_STATE' });
      });

      this.ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data.toString());
          this._handleMessage(msg);
        } catch (e) {
          console.warn('[ESP32] Invalid message:', data.toString());
        }
      });

      this.ws.on('close', () => {
        console.log('[ESP32] Disconnected');
        this.deviceState.connected = false;
        this._emit('disconnected', {});
        this._scheduleReconnect(host, port, secure);
      });

      this.ws.on('error', (err) => {
        console.error('[ESP32] Error:', err.message);
        this._emit('error', { message: err.message });
      });
    } catch (err) {
      console.error('[ESP32] Connection error:', err.message);
      this._scheduleReconnect(host, port, secure);
    }
  }

  _scheduleReconnect(host, port, secure = false) {
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
      this.connect(host, port, secure);
    }, this.reconnectDelay);
  }

  _handleMessage(msg) {
    if (msg.type === 'STATE_UPDATE') {
      Object.assign(this.deviceState, msg.state);
      this._emit('stateUpdate', this.deviceState);
    }
    if (msg.type === 'ACK') {
      this._emit('ack', msg);
    }
  }

  _send(payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }

  sendCommand(commandName, params = {}) {
    const cmd = DEVICE_COMMANDS[commandName];
    if (!cmd) {
      throw new Error(`Unknown command: ${commandName}`);
    }
    const payload = { ...cmd, ...params, id: Date.now() };
    const sent = this._send(payload);
    if (!sent) {
      console.warn('[ESP32] Command dropped (not connected):', commandName);
    }
    // Optimistically update local state
    this._applyLocalState(commandName);
    return { command: commandName, sent, state: this.deviceState };
  }

  processGestureAction(action) {
    const commands = ACTION_TO_COMMAND[action];
    if (!commands) return null;

    const results = [];
    for (const cmdName of commands) {
      // Toggle logic for LED/MOTOR
      const toggled = this._toggleCommand(cmdName);
      results.push(this.sendCommand(toggled));
    }
    return results;
  }

  _toggleCommand(commandName) {
    if (commandName === 'LED_RED_ON')   return this.deviceState.led_red   ? 'LED_RED_OFF'   : 'LED_RED_ON';
    if (commandName === 'LED_BLUE_ON')  return this.deviceState.led_blue  ? 'LED_BLUE_OFF'  : 'LED_BLUE_ON';
    if (commandName === 'LED_GREEN_ON') return this.deviceState.led_green ? 'LED_GREEN_OFF' : 'LED_GREEN_ON';
    if (commandName === 'MOTOR_ON')     return this.deviceState.motor     ? 'MOTOR_OFF'      : 'MOTOR_ON';
    return commandName;
  }

  _applyLocalState(commandName) {
    switch (commandName) {
      case 'LED_RED_ON':    this.deviceState.led_red   = true;  break;
      case 'LED_RED_OFF':   this.deviceState.led_red   = false; break;
      case 'LED_BLUE_ON':   this.deviceState.led_blue  = true;  break;
      case 'LED_BLUE_OFF':  this.deviceState.led_blue  = false; break;
      case 'LED_GREEN_ON':  this.deviceState.led_green = true;  break;
      case 'LED_GREEN_OFF': this.deviceState.led_green = false; break;
      case 'MOTOR_ON':      this.deviceState.motor     = true;  break;
      case 'MOTOR_OFF':     this.deviceState.motor     = false; break;
      case 'RESET':
        this.deviceState.led_red = this.deviceState.led_blue = this.deviceState.led_green = this.deviceState.motor = false;
        break;
    }
  }

  getState() {
    return { ...this.deviceState };
  }

  onEvent(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  _emit(event, data) {
    for (const l of this.listeners) {
      try { l(event, data); } catch (_) {}
    }
  }

  disconnect() {
    clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.removeAllListeners();
      this.ws.close();
      this.ws = null;
    }
  }
}

// Singleton
const esp32Service = new ESP32Service();

if (config.ESP32_HOST) {
  esp32Service.connect(config.ESP32_HOST, config.ESP32_PORT, config.ESP32_SECURE);
}

module.exports = esp32Service;
