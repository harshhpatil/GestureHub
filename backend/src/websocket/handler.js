const jwt = require('jsonwebtoken');
const config = require('../config/env');
const { getDb } = require('../config/database');
const { getMachine, removeMachine } = require('../services/gestureService');
const esp32Service = require('../services/esp32Service');

// Connected socket sessions: socketId → { userId, username }
const sessions = new Map();

function setupWebSocket(io) {
  // Auth middleware for Socket.io
  io.use((socket, next) => {
    const token =
      socket.handshake.auth?.token ||
      socket.handshake.headers?.authorization?.split(' ')[1];

    if (!token) {
      // Allow unauthenticated for demo/guest mode
      socket.userId = null;
      socket.username = 'guest';
      return next();
    }

    try {
      const decoded = jwt.verify(token, config.JWT_SECRET);
      socket.userId = decoded.id;
      socket.username = decoded.username;
      next();
    } catch (err) {
      next(new Error('Invalid token'));
    }
  });

  io.on('connection', (socket) => {
    console.log(`[WS] Connected: ${socket.id} (${socket.username})`);
    sessions.set(socket.id, { userId: socket.userId, username: socket.username });

    // Send initial device state
    socket.emit('device:state', esp32Service.getState());

    // ── Gesture event ──────────────────────────────────────────────────
    socket.on('gesture:frame', (data) => {
      const { gesture, confidence = 1.0 } = data || {};
      if (!gesture) return;

      const userId = socket.userId || socket.id;
      let preferences = {};

      // Load user preferences if authenticated
      if (socket.userId) {
        try {
          const db = getDb();
          preferences = db
            .prepare('SELECT * FROM preferences WHERE user_id = ?')
            .get(socket.userId) || {};
        } catch (_) {}
      }

      const machine = getMachine(userId, preferences);
      const actionResult = machine.process(gesture, confidence);

      if (actionResult) {
        console.log(`[WS] Gesture action: ${actionResult.gesture} → ${actionResult.action}`);

        // Log to DB if authenticated
        if (socket.userId) {
          try {
            const db = getDb();
            db.prepare(
              'INSERT INTO gesture_log (user_id, gesture, action) VALUES (?, ?, ?)'
            ).run(socket.userId, actionResult.gesture, actionResult.action);
          } catch (_) {}
        }

        // Route to ESP32 if applicable
        if (actionResult.device === 'esp32' || actionResult.device === 'all') {
          const cmdResults = esp32Service.processGestureAction(actionResult.action);
          if (cmdResults) {
            io.emit('device:state', esp32Service.getState());
          }
        }

        // Broadcast confirmed action to all clients
        io.emit('gesture:action', actionResult);
        socket.emit('gesture:confirmed', {
          ...actionResult,
          machineState: machine.getState(),
        });
      } else {
        socket.emit('gesture:pending', machine.getState());
      }
    });

    // ── Direct device command ──────────────────────────────────────────
    socket.on('device:command', (data) => {
      const { command } = data || {};
      if (!command) return;

      try {
        const result = esp32Service.sendCommand(command);
        io.emit('device:state', esp32Service.getState());
        socket.emit('device:command:ack', { command, success: true, state: result.state });
      } catch (err) {
        socket.emit('device:command:ack', { command, success: false, error: err.message });
      }
    });

    // ── Settings update ───────────────────────────────────────────────
    socket.on('settings:update', (data) => {
      const userId = socket.userId || socket.id;
      const machine = getMachine(userId);
      machine.updateSettings(data || {});
      socket.emit('settings:updated', machine.getState());
    });

    // ── Ping / healthcheck ────────────────────────────────────────────
    socket.on('ping', () => {
      socket.emit('pong', { ts: Date.now() });
    });

    // ── Disconnect ────────────────────────────────────────────────────
    socket.on('disconnect', () => {
      console.log(`[WS] Disconnected: ${socket.id}`);
      sessions.delete(socket.id);
      // Clean up state machine for unauthenticated sessions
      if (!socket.userId) {
        removeMachine(socket.id);
      }
    });
  });

  // Propagate ESP32 events to all clients
  esp32Service.onEvent((event, data) => {
    if (event === 'stateUpdate') {
      io.emit('device:state', data);
    }
    if (event === 'connected' || event === 'disconnected') {
      io.emit('esp32:connection', { connected: event === 'connected', ...data });
    }
  });
}

module.exports = { setupWebSocket };
