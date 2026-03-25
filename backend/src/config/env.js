require('dotenv').config();

const config = {
  // Server
  PORT: parseInt(process.env.PORT || '3001', 10),
  NODE_ENV: process.env.NODE_ENV || 'development',

  // JWT
  JWT_SECRET: process.env.JWT_SECRET || 'gesturehub-secret-change-in-production',
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '7d',

  // Database
  DB_PATH: process.env.DB_PATH || './gesturehub.db',

  // CORS
  CORS_ORIGIN: process.env.CORS_ORIGIN || 'http://localhost:5173',

  // ESP32
  ESP32_HOST: process.env.ESP32_HOST || null,
  ESP32_PORT: parseInt(process.env.ESP32_PORT || '81', 10),
  ESP32_WS_PATH: process.env.ESP32_WS_PATH || '/ws',
  ESP32_SECURE: process.env.ESP32_SECURE === 'true',

  // Rate limiting
  RATE_LIMIT_WINDOW_MS: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000', 10),
  RATE_LIMIT_MAX: parseInt(process.env.RATE_LIMIT_MAX || '100', 10),
};

module.exports = config;
