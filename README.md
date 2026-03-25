# GestureHub 🤌

**Real-time hand gesture control for IoT devices** — Transform hand gestures detected via your webcam into commands that control physical hardware (LEDs, DC Motors) via an ESP32 microcontroller.

[![Node.js](https://img.shields.io/badge/Node.js-18+-green)](https://nodejs.org)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org)
[![Socket.io](https://img.shields.io/badge/Socket.io-4-black)](https://socket.io)
[![ESP32](https://img.shields.io/badge/ESP32--S3-Arduino-red)](https://espressif.com)

---

## 🏗 Architecture

```
Browser (React + MediaPipe.js)
        │ WebSocket (Socket.io)
        ▼
Backend (Node.js + Express + Socket.io)
        │ WebSocket (ws)
        ▼
ESP32-S3 (Arduino firmware)
        │ GPIO
        ▼
Hardware (LEDs, DC Motor)
```

| Layer    | Stack                              |
|----------|------------------------------------|
| Frontend | React 18, Vite, MediaPipe.js, Tailwind CSS, Socket.io-client |
| Backend  | Node.js 18+, Express, Socket.io, SQLite (better-sqlite3), JWT |
| Firmware | ESP32-S3, Arduino IDE, ArduinoWebsockets, ArduinoJson |
| DevOps   | Docker, Docker Compose, Nginx, Let's Encrypt |

---

## 🤲 Supported Gestures

| Gesture      | Emoji | Action         |
|--------------|-------|----------------|
| THUMBS_UP    | 👍    | Volume Up      |
| THUMBS_DOWN  | 👎    | Volume Down    |
| PEACE        | ✌️    | Next Track     |
| OPEN_PALM    | 🖐️    | Reset All      |
| FIST         | ✊    | Play / Pause   |
| INDEX        | ☝️    | Toggle LED     |
| ROCK         | 🤘    | Toggle Motor   |
| TWO_FINGERS  | ✌️    | Swipe          |

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Node.js ≥ 18
- npm ≥ 9
- A webcam

### 1. Run Setup Script

```bash
bash scripts/setup.sh
```

### 2. Start Backend

```bash
cd backend
npm run dev
# Server on http://localhost:3001
```

### 3. Start Frontend

```bash
cd frontend
npm run dev
# App on http://localhost:5173
```

### 4. Open the App

Navigate to **http://localhost:5173**. Register an account (or continue as guest), grant camera permission, and start gesturing!

---

## 🐳 Docker (Production)

```bash
# Copy and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — set JWT_SECRET, CORS_ORIGIN, ESP32_HOST

# Start all services
docker compose up --build -d

# View logs
docker compose logs -f
```

The app will be available at **http://localhost**.

---

## 📡 ESP32 Firmware

### Hardware Connections

| ESP32-S3 Pin | Component         |
|--------------|-------------------|
| GPIO 4       | Red LED (+)       |
| GPIO 5       | Blue LED (+)      |
| GPIO 6       | Green LED (+)     |
| GPIO 7       | Motor PWM (L298N EN) |
| GPIO 8       | Motor DIR1 (IN1)  |
| GPIO 9       | Motor DIR2 (IN2)  |
| GPIO 2       | Status LED (onboard) |

### Flashing

1. Install [Arduino IDE 2](https://www.arduino.cc/en/software)
2. Add ESP32 board support: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. Install libraries via Library Manager:
   - **ArduinoWebsockets** by Gil Maimon
   - **ArduinoJson** by Benoit Blanchon
4. Edit `esp32/config.h` — set WiFi credentials and server IP
5. Select board: **ESP32S3 Dev Module**
6. Upload `esp32/main.ino`

---

## 🌐 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET  | `/api/auth/me` | Get current user info |
| PUT  | `/api/auth/preferences` | Update accessibility settings |

### Devices

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/devices` | List registered devices |
| POST | `/api/devices/register` | Register an ESP32 |
| GET  | `/api/devices/state` | Get current hardware state |
| POST | `/api/devices/command` | Send a direct command |
| DELETE | `/api/devices/:id` | Remove a device |

### WebSocket Events (Socket.io)

**Client → Server:**

| Event | Payload | Description |
|-------|---------|-------------|
| `gesture:frame` | `{ gesture, confidence }` | Send detected gesture |
| `device:command` | `{ command }` | Direct device command |
| `settings:update` | `{ sensitivity, tremorFilter, cooldownMs }` | Update gesture settings |
| `ping` | — | Health check |

**Server → Client:**

| Event | Payload | Description |
|-------|---------|-------------|
| `device:state` | `{ led_red, led_blue, led_green, motor, connected }` | Hardware state |
| `gesture:action` | `{ gesture, action, device, timestamp }` | Confirmed gesture action |
| `gesture:confirmed` | `{ ...action, machineState }` | Gesture confirmed (to sender) |
| `gesture:pending` | `{ pendingGesture, ... }` | Gesture in progress |
| `esp32:connection` | `{ connected }` | ESP32 connectivity change |
| `pong` | `{ ts }` | Ping response |

---

## ♿ Accessibility Features

- **Sensitivity Slider** (0.3–1.0) — Adjust confidence threshold for gesture detection
- **Tremor Filter** — Smooths out rapid unintentional hand movements
- **Gesture Delay** (100–1500ms) — Cooldown between gesture activations
- Keyboard-navigable UI with ARIA labels
- High-contrast dark theme with accent colors

---

## 🔐 Security

- JWT authentication with configurable expiry
- bcrypt password hashing (12 rounds)
- Rate limiting on all API endpoints
- Helmet.js security headers
- Input validation with express-validator
- CORS configured to specific origins

---

## 🚢 VPS Deployment

```bash
# Deploy to your VPS (replace with your server details)
bash scripts/deploy-vps.sh user@your-vps.com yourdomain.com
```

This script:
1. Rsyncs the project to the VPS
2. Installs Docker if needed
3. Builds and starts containers
4. Configures Let's Encrypt SSL

---

## 🧪 Running Tests

```bash
cd backend
npm test
```

---

## 📁 Project Structure

```
GestureHub/
├── backend/
│   ├── src/
│   │   ├── config/
│   │   │   ├── env.js          # Configuration
│   │   │   └── database.js     # SQLite setup
│   │   ├── middleware/
│   │   │   └── auth.js         # JWT middleware
│   │   ├── routes/
│   │   │   ├── auth.js         # Auth endpoints
│   │   │   └── devices.js      # Device endpoints
│   │   ├── services/
│   │   │   ├── gestureService.js  # Gesture state machine
│   │   │   └── esp32Service.js    # ESP32 WebSocket client
│   │   ├── websocket/
│   │   │   └── handler.js      # Socket.io event handlers
│   │   └── server.js           # Express + Socket.io server
│   ├── tests/
│   │   └── gestureService.test.js
│   ├── .env.example
│   ├── Dockerfile
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CameraFeed.jsx       # MediaPipe gesture detection
│   │   │   ├── DeviceControl.jsx    # LED/Motor controls
│   │   │   ├── AccessibilityPanel.jsx
│   │   │   └── LoginForm.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # Auth state management
│   │   ├── hooks/
│   │   │   └── useWebSocket.js      # Socket.io hook
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── esp32/
│   ├── main.ino                # Arduino firmware
│   └── config.h                # WiFi + pin configuration
├── nginx/
│   └── nginx.conf              # Reverse proxy config
├── scripts/
│   ├── setup.sh                # Local dev setup
│   └── deploy-vps.sh           # VPS deployment
└── docker-compose.yml
```

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
