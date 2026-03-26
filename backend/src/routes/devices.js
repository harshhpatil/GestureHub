const express = require('express');
const { body, validationResult } = require('express-validator');
const { getDb } = require('../config/database');
const { authenticateToken } = require('../middleware/auth');
const esp32Service = require('../services/esp32Service');

const router = express.Router();

// GET /api/devices — list all registered devices
router.get('/', authenticateToken, (req, res) => {
  try {
    const db = getDb();
    const devices = db.prepare('SELECT * FROM devices ORDER BY registered_at DESC').all();
    return res.json({ devices });
  } catch (err) {
    console.error('[Devices] List error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/devices/register — register a new device
router.post(
  '/register',
  authenticateToken,
  [
    body('device_id').trim().notEmpty().isLength({ max: 64 }),
    body('name').trim().notEmpty().isLength({ max: 64 }),
    body('ip_address').optional().isIP(),
  ],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { device_id, name, ip_address } = req.body;

    try {
      const db = getDb();
      const existing = db
        .prepare('SELECT id FROM devices WHERE device_id = ?')
        .get(device_id);

      if (existing) {
        // Update existing
        db.prepare(
          "UPDATE devices SET name = ?, ip_address = ?, status = 'online', last_seen = datetime('now') WHERE device_id = ?"
        ).run(name, ip_address || null, device_id);
      } else {
        db.prepare(
          "INSERT INTO devices (device_id, name, ip_address, status, last_seen) VALUES (?, ?, ?, 'online', datetime('now'))"
        ).run(device_id, name, ip_address || null);
      }

      const device = db.prepare('SELECT * FROM devices WHERE device_id = ?').get(device_id);
      return res.status(201).json({ device });
    } catch (err) {
      console.error('[Devices] Register error:', err);
      return res.status(500).json({ error: 'Internal server error' });
    }
  }
);

// GET /api/devices/state — get current ESP32 hardware state
router.get('/state', authenticateToken, (_req, res) => {
  return res.json({ state: esp32Service.getState() });
});

// POST /api/devices/command — send a direct command to ESP32
router.post(
  '/command',
  authenticateToken,
  [
    body('command').trim().notEmpty().isIn([
      'LED_RED_ON', 'LED_RED_OFF',
      'LED_BLUE_ON', 'LED_BLUE_OFF',
      'LED_GREEN_ON', 'LED_GREEN_OFF',
      'MOTOR_ON', 'MOTOR_OFF',
      'RESET',
    ]),
  ],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    try {
      const result = esp32Service.sendCommand(req.body.command);
      return res.json(result);
    } catch (err) {
      return res.status(400).json({ error: err.message });
    }
  }
);

// DELETE /api/devices/:id — remove a device
router.delete('/:id', authenticateToken, (req, res) => {
  try {
    const db = getDb();
    const device = db
      .prepare('SELECT id FROM devices WHERE device_id = ?')
      .get(req.params.id);

    if (!device) {
      return res.status(404).json({ error: 'Device not found' });
    }

    db.prepare('DELETE FROM devices WHERE device_id = ?').run(req.params.id);
    return res.json({ message: 'Device removed' });
  } catch (err) {
    console.error('[Devices] Delete error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
