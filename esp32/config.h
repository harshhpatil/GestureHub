// GestureHub ESP32-S3 Configuration
// ⚠️  IMPORTANT: Update these values before uploading to your device.
//     Do NOT commit real WiFi credentials to version control.

#pragma once

// ── WiFi Configuration ─────────────────────────────────────────────────
#define WIFI_SSID        "YourWiFiSSID"
#define WIFI_PASSWORD    "YourWiFiPassword"

// ── GestureHub Backend WebSocket ───────────────────────────────────────
// Replace with your backend server IP or domain
#define SERVER_HOST      "192.168.1.100"
#define SERVER_PORT      3001
#define SERVER_WS_PATH   "/socket.io/?EIO=4&transport=websocket"

// ── Device Identity ────────────────────────────────────────────────────
#define DEVICE_ID        "esp32-s3-001"
#define DEVICE_NAME      "GestureHub ESP32-S3"

// ── GPIO Pin Assignments (ESP32-S3) ───────────────────────────────────
#define PIN_LED_RED      4
#define PIN_LED_BLUE     5
#define PIN_LED_GREEN    6
#define PIN_MOTOR_PWM    7
#define PIN_MOTOR_DIR1   8
#define PIN_MOTOR_DIR2   9
#define PIN_STATUS_LED   2   // Onboard LED

// ── Motor PWM ─────────────────────────────────────────────────────────
#define PWM_CHANNEL      0
#define PWM_FREQUENCY    5000
#define PWM_RESOLUTION   8   // 8-bit: 0-255
#define MOTOR_SPEED      200 // Default speed (0-255)

// ── Timing ────────────────────────────────────────────────────────────
#define WIFI_TIMEOUT_MS       10000
#define WS_RECONNECT_MS       3000
#define HEARTBEAT_INTERVAL_MS 5000
#define STATUS_BLINK_MS       500
