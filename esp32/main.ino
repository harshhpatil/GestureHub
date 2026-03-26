/*
 * GestureHub ESP32-S3 Firmware
 *
 * Controls LEDs (Red, Blue, Green) and a DC Motor via WebSocket commands
 * from the GestureHub backend server.
 *
 * Hardware:
 *   - ESP32-S3 DevKit
 *   - 3x LEDs (Red GPIO4, Blue GPIO5, Green GPIO6)
 *   - DC Motor with L298N driver (PWM GPIO7, DIR1 GPIO8, DIR2 GPIO9)
 *
 * Dependencies (install via Arduino Library Manager):
 *   - ArduinoWebsockets by Gil Maimon
 *   - ArduinoJson by Benoit Blanchon
 *   - WiFi (built-in ESP32)
 *
 * Board: ESP32S3 Dev Module
 */

#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include <ArduinoJson.h>
#include "config.h"

using namespace websockets;

WebsocketsClient wsClient;

// ── Device State ──────────────────────────────────────────────────────
struct DeviceState {
  bool led_red   = false;
  bool led_blue  = false;
  bool led_green = false;
  bool motor     = false;
};

DeviceState state;

// ── Timers ────────────────────────────────────────────────────────────
unsigned long lastHeartbeat    = 0;
unsigned long lastReconnect    = 0;
unsigned long lastStatusBlink  = 0;
bool statusLedOn = false;

// ── Prototypes ────────────────────────────────────────────────────────
void connectWifi();
void connectWebSocket();
void onMessage(WebsocketsMessage msg);
void onEvent(WebsocketsEvent event, String data);
void handleCommand(JsonDocument& doc);
void setLED(const char* pin, bool on);
void setMotor(bool on, int speed = MOTOR_SPEED);
void sendStateUpdate();
void sendHeartbeat();
void applyState();

// ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println(F("\n[GestureHub] ESP32-S3 Firmware v1.0"));

  // GPIO setup
  pinMode(PIN_LED_RED,    OUTPUT);
  pinMode(PIN_LED_BLUE,   OUTPUT);
  pinMode(PIN_LED_GREEN,  OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_MOTOR_DIR1, OUTPUT);
  pinMode(PIN_MOTOR_DIR2, OUTPUT);

  // Motor PWM
  ledcSetup(PWM_CHANNEL, PWM_FREQUENCY, PWM_RESOLUTION);
  ledcAttachPin(PIN_MOTOR_PWM, PWM_CHANNEL);
  ledcWrite(PWM_CHANNEL, 0);

  // Initial state
  applyState();

  // Connect
  connectWifi();
  connectWebSocket();
}

// ─────────────────────────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  // WebSocket poll
  if (wsClient.available()) {
    wsClient.poll();
  }

  // Reconnect if needed
  if (!wsClient.available() && (now - lastReconnect > WS_RECONNECT_MS)) {
    Serial.println(F("[WS] Reconnecting..."));
    connectWebSocket();
    lastReconnect = now;
  }

  // Heartbeat
  if (wsClient.available() && (now - lastHeartbeat > HEARTBEAT_INTERVAL_MS)) {
    sendHeartbeat();
    lastHeartbeat = now;
  }

  // Status LED blink (slow = connected, fast = disconnected)
  unsigned long blinkInterval = wsClient.available() ? 2000 : 250;
  if (now - lastStatusBlink > blinkInterval) {
    statusLedOn = !statusLedOn;
    digitalWrite(PIN_STATUS_LED, statusLedOn);
    lastStatusBlink = now;
  }
}

// ─────────────────────────────────────────────────────────────────────
void connectWifi() {
  Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - start > WIFI_TIMEOUT_MS) {
      Serial.println(F("\n[WiFi] Timeout! Restarting..."));
      ESP.restart();
    }
    delay(500);
    Serial.print('.');
  }

  Serial.println();
  Serial.printf("[WiFi] Connected. IP: %s\n", WiFi.localIP().toString().c_str());
}

// ─────────────────────────────────────────────────────────────────────
void connectWebSocket() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWifi();
  }

  wsClient.onMessage(onMessage);
  wsClient.onEvent(onEvent);

  String url = String("ws://") + SERVER_HOST + ":" + SERVER_PORT + SERVER_WS_PATH;
  Serial.printf("[WS] Connecting to %s\n", url.c_str());

  bool connected = wsClient.connect(SERVER_HOST, SERVER_PORT, SERVER_WS_PATH);
  if (connected) {
    Serial.println(F("[WS] Connected!"));
    // Register device
    StaticJsonDocument<256> doc;
    doc["type"]      = "device:register";
    doc["device_id"] = DEVICE_ID;
    doc["name"]      = DEVICE_NAME;
    doc["ip"]        = WiFi.localIP().toString();
    String msg;
    serializeJson(doc, msg);
    wsClient.send(msg);
    sendStateUpdate();
  } else {
    Serial.println(F("[WS] Connection failed, will retry"));
  }
}

// ─────────────────────────────────────────────────────────────────────
void onMessage(WebsocketsMessage msg) {
  Serial.printf("[WS] Message: %s\n", msg.data().c_str());

  StaticJsonDocument<512> doc;
  DeserializationError err = deserializeJson(doc, msg.data());
  if (err) {
    Serial.printf("[WS] JSON parse error: %s\n", err.c_str());
    return;
  }

  handleCommand(doc);
}

void onEvent(WebsocketsEvent event, String data) {
  switch (event) {
    case WebsocketsEvent::ConnectionOpened:
      Serial.println(F("[WS] Connection opened"));
      break;
    case WebsocketsEvent::ConnectionClosed:
      Serial.println(F("[WS] Connection closed"));
      break;
    case WebsocketsEvent::GotPing:
      wsClient.pong();
      break;
    default:
      break;
  }
}

// ─────────────────────────────────────────────────────────────────────
void handleCommand(JsonDocument& doc) {
  const char* type = doc["type"];
  if (!type) return;

  if (strcmp(type, "LED") == 0) {
    const char* pin = doc["pin"];
    bool on = doc["state"].as<bool>();
    setLED(pin, on);
    sendStateUpdate();

  } else if (strcmp(type, "MOTOR") == 0) {
    int speed = doc["speed"] | MOTOR_SPEED;
    bool running = speed > 0;
    setMotor(running, speed);
    sendStateUpdate();

  } else if (strcmp(type, "RESET") == 0) {
    setLED("RED",   false);
    setLED("BLUE",  false);
    setLED("GREEN", false);
    setMotor(false, 0);
    sendStateUpdate();

  } else if (strcmp(type, "GET_STATE") == 0) {
    sendStateUpdate();
  }
}

// ─────────────────────────────────────────────────────────────────────
void setLED(const char* pin, bool on) {
  if (strcmp(pin, "RED") == 0) {
    state.led_red = on;
    digitalWrite(PIN_LED_RED, on ? HIGH : LOW);
  } else if (strcmp(pin, "BLUE") == 0) {
    state.led_blue = on;
    digitalWrite(PIN_LED_BLUE, on ? HIGH : LOW);
  } else if (strcmp(pin, "GREEN") == 0) {
    state.led_green = on;
    digitalWrite(PIN_LED_GREEN, on ? HIGH : LOW);
  }
  Serial.printf("[LED] %s = %s\n", pin, on ? "ON" : "OFF");
}

void setMotor(bool on, int speed) {
  state.motor = on;
  if (on) {
    digitalWrite(PIN_MOTOR_DIR1, HIGH);
    digitalWrite(PIN_MOTOR_DIR2, LOW);
    ledcWrite(PWM_CHANNEL, speed);
    Serial.printf("[Motor] ON speed=%d\n", speed);
  } else {
    digitalWrite(PIN_MOTOR_DIR1, LOW);
    digitalWrite(PIN_MOTOR_DIR2, LOW);
    ledcWrite(PWM_CHANNEL, 0);
    Serial.println(F("[Motor] OFF"));
  }
}

void applyState() {
  digitalWrite(PIN_LED_RED,   state.led_red   ? HIGH : LOW);
  digitalWrite(PIN_LED_BLUE,  state.led_blue  ? HIGH : LOW);
  digitalWrite(PIN_LED_GREEN, state.led_green ? HIGH : LOW);
  setMotor(state.motor, MOTOR_SPEED);
}

// ─────────────────────────────────────────────────────────────────────
void sendStateUpdate() {
  StaticJsonDocument<256> doc;
  doc["type"] = "STATE_UPDATE";
  JsonObject s = doc.createNestedObject("state");
  s["led_red"]   = state.led_red;
  s["led_blue"]  = state.led_blue;
  s["led_green"] = state.led_green;
  s["motor"]     = state.motor;

  String msg;
  serializeJson(doc, msg);
  if (wsClient.available()) {
    wsClient.send(msg);
  }
}

void sendHeartbeat() {
  StaticJsonDocument<128> doc;
  doc["type"]      = "heartbeat";
  doc["device_id"] = DEVICE_ID;
  doc["uptime_ms"] = millis();
  doc["wifi_rssi"] = WiFi.RSSI();
  String msg;
  serializeJson(doc, msg);
  wsClient.send(msg);
}
