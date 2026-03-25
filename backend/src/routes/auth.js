const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const { getDb } = require('../config/database');
const config = require('../config/env');

const router = express.Router();

// POST /api/auth/register
router.post(
  '/register',
  [
    body('username').trim().isLength({ min: 3, max: 30 }).escape(),
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 }),
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { username, email, password } = req.body;

    try {
      const db = getDb();

      const existing = db
        .prepare('SELECT id FROM users WHERE username = ? OR email = ?')
        .get(username, email);

      if (existing) {
        return res.status(409).json({ error: 'Username or email already taken' });
      }

      const hashed = await bcrypt.hash(password, 12);
      const result = db
        .prepare('INSERT INTO users (username, email, password) VALUES (?, ?, ?)')
        .run(username, email, hashed);

      // Create default preferences
      db.prepare(
        'INSERT INTO preferences (user_id) VALUES (?)'
      ).run(result.lastInsertRowid);

      const token = jwt.sign(
        { id: result.lastInsertRowid, username },
        config.JWT_SECRET,
        { expiresIn: config.JWT_EXPIRES_IN }
      );

      return res.status(201).json({
        token,
        user: { id: result.lastInsertRowid, username, email },
      });
    } catch (err) {
      console.error('[Auth] Register error:', err);
      return res.status(500).json({ error: 'Internal server error' });
    }
  }
);

// POST /api/auth/login
router.post(
  '/login',
  [
    body('username').trim().notEmpty().escape(),
    body('password').notEmpty(),
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { username, password } = req.body;

    try {
      const db = getDb();
      const user = db
        .prepare('SELECT * FROM users WHERE username = ?')
        .get(username);

      if (!user) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const valid = await bcrypt.compare(password, user.password);
      if (!valid) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const token = jwt.sign(
        { id: user.id, username: user.username },
        config.JWT_SECRET,
        { expiresIn: config.JWT_EXPIRES_IN }
      );

      const prefs = db
        .prepare('SELECT * FROM preferences WHERE user_id = ?')
        .get(user.id);

      return res.json({
        token,
        user: { id: user.id, username: user.username, email: user.email },
        preferences: prefs || {},
      });
    } catch (err) {
      console.error('[Auth] Login error:', err);
      return res.status(500).json({ error: 'Internal server error' });
    }
  }
);

// GET /api/auth/me
const { authenticateToken } = require('../middleware/auth');

router.get('/me', authenticateToken, (req, res) => {
  try {
    const db = getDb();
    const user = db
      .prepare('SELECT id, username, email, created_at FROM users WHERE id = ?')
      .get(req.user.id);

    if (!user) return res.status(404).json({ error: 'User not found' });

    const prefs = db
      .prepare('SELECT * FROM preferences WHERE user_id = ?')
      .get(req.user.id);

    return res.json({ user, preferences: prefs || {} });
  } catch (err) {
    console.error('[Auth] Me error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// PUT /api/auth/preferences
router.put(
  '/preferences',
  authenticateToken,
  [
    body('sensitivity').optional().isFloat({ min: 0.1, max: 1.0 }),
    body('tremor_filter').optional().isBoolean(),
    body('gesture_delay_ms').optional().isInt({ min: 100, max: 2000 }),
  ],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { sensitivity, tremor_filter, gesture_delay_ms } = req.body;

    try {
      const db = getDb();
      const existing = db
        .prepare('SELECT id FROM preferences WHERE user_id = ?')
        .get(req.user.id);

      if (existing) {
        db.prepare(`
          UPDATE preferences
          SET sensitivity = COALESCE(?, sensitivity),
              tremor_filter = COALESCE(?, tremor_filter),
              gesture_delay_ms = COALESCE(?, gesture_delay_ms),
              updated_at = datetime('now')
          WHERE user_id = ?
        `).run(
          sensitivity ?? null,
          tremor_filter !== undefined ? (tremor_filter ? 1 : 0) : null,
          gesture_delay_ms ?? null,
          req.user.id
        );
      } else {
        db.prepare(
          'INSERT INTO preferences (user_id, sensitivity, tremor_filter, gesture_delay_ms) VALUES (?, ?, ?, ?)'
        ).run(
          req.user.id,
          sensitivity ?? 0.7,
          tremor_filter ? 1 : 0,
          gesture_delay_ms ?? 300
        );
      }

      const prefs = db
        .prepare('SELECT * FROM preferences WHERE user_id = ?')
        .get(req.user.id);

      return res.json({ preferences: prefs });
    } catch (err) {
      console.error('[Auth] Preferences error:', err);
      return res.status(500).json({ error: 'Internal server error' });
    }
  }
);

module.exports = router;
