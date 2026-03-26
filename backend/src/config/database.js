const Database = require('better-sqlite3');
const path = require('path');
const config = require('../config/env');

let db;

function getDb() {
  if (!db) {
    const dbPath = path.resolve(config.DB_PATH);
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    initSchema(db);
  }
  return db;
}

function initSchema(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      username   TEXT    UNIQUE NOT NULL,
      email      TEXT    UNIQUE NOT NULL,
      password   TEXT    NOT NULL,
      created_at TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS preferences (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      sensitivity      REAL    NOT NULL DEFAULT 0.7,
      tremor_filter    INTEGER NOT NULL DEFAULT 0,
      gesture_delay_ms INTEGER NOT NULL DEFAULT 300,
      updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS devices (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      device_id   TEXT    UNIQUE NOT NULL,
      name        TEXT    NOT NULL,
      ip_address  TEXT,
      status      TEXT    NOT NULL DEFAULT 'offline',
      last_seen   TEXT,
      registered_at TEXT  NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS gesture_log (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
      gesture    TEXT    NOT NULL,
      action     TEXT,
      device_id  TEXT,
      created_at TEXT    NOT NULL DEFAULT (datetime('now'))
    );
  `);
}

module.exports = { getDb };
