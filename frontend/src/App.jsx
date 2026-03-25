import { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { useWebSocket } from './hooks/useWebSocket';
import CameraFeed from './components/CameraFeed';
import DeviceControl from './components/DeviceControl';
import AccessibilityPanel from './components/AccessibilityPanel';
import LoginForm from './components/LoginForm';

function Dashboard() {
  const { user, token, logout } = useAuth();
  const { connected, deviceState, lastAction, sendGestureFrame, sendDeviceCommand, updateSettings } =
    useWebSocket(token);

  const [settings, setSettings] = useState({
    sensitivity: 0.7,
    tremorFilter: false,
    gestureDelayMs: 300,
  });

  const [activeTab, setActiveTab] = useState('camera'); // 'camera' | 'devices' | 'accessibility'
  const [gestureLog, setGestureLog] = useState([]);

  // Track last actions for gesture log
  useEffect(() => {
    if (lastAction) {
      setGestureLog((prev) => [
        { ...lastAction, id: Date.now() },
        ...prev.slice(0, 9),
      ]);
    }
  }, [lastAction]);

  const handleGesture = useCallback(
    (gesture, confidence) => {
      sendGestureFrame(gesture, confidence);
    },
    [sendGestureFrame]
  );

  const handleSettingsChange = useCallback(
    (newSettings) => {
      setSettings(newSettings);
      updateSettings({
        sensitivity: newSettings.sensitivity,
        tremorFilter: newSettings.tremorFilter,
        cooldownMs: newSettings.gestureDelayMs,
      });
    },
    [updateSettings]
  );

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="border-b border-gray-800 px-4 py-3 flex items-center justify-between sticky top-0 bg-dark-900/95 backdrop-blur-sm z-10">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold" style={{ color: '#00FFCC' }}>
            GestureHub
          </h1>
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-xs text-gray-500">{connected ? 'Live' : 'Disconnected'}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <span className="text-xs text-gray-400 hidden sm:inline">
              @{user.username}
            </span>
          )}
          <button
            onClick={logout}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Mobile tabs */}
        <div className="flex gap-1 mb-6 bg-dark-800 p-1 rounded-xl border border-gray-700 lg:hidden">
          {[
            { id: 'camera', label: '📷 Camera' },
            { id: 'devices', label: '💡 Devices' },
            { id: 'accessibility', label: '♿ Settings' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-2 rounded-lg text-xs font-mono transition-colors ${
                activeTab === tab.id
                  ? 'bg-dark-700 text-accent'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Camera Feed — always visible on desktop */}
          <div className={`lg:col-span-2 space-y-4 ${activeTab !== 'camera' ? 'hidden lg:block' : ''}`}>
            <CameraFeed onGesture={handleGesture} sensitivity={settings.sensitivity} />

            {/* Gesture log */}
            <div className="bg-dark-800 border border-gray-700 rounded-xl p-4">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
                Gesture Log
              </h3>
              {gestureLog.length === 0 ? (
                <p className="text-xs text-gray-600 text-center py-2">
                  No gestures yet — try showing your hand to the camera
                </p>
              ) : (
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {gestureLog.map((g) => (
                    <div
                      key={g.id}
                      className="flex items-center justify-between text-xs font-mono py-1 border-b border-gray-800 last:border-0"
                    >
                      <span className="text-accent">{g.gesture}</span>
                      <span className="text-gray-400">{g.action}</span>
                      <span className="text-gray-600">
                        {new Date(g.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right panel */}
          <div className="space-y-4">
            <div className={activeTab !== 'devices' ? 'hidden lg:block' : ''}>
              <DeviceControl
                deviceState={deviceState}
                onCommand={sendDeviceCommand}
                connected={connected}
                lastAction={lastAction}
              />
            </div>
            <div className={activeTab !== 'accessibility' ? 'hidden lg:block' : ''}>
              <AccessibilityPanel
                settings={settings}
                onSettingsChange={handleSettingsChange}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function AppContent() {
  const { user, loading } = useAuth();
  const [guestMode, setGuestMode] = useState(false);

  useEffect(() => {
    const handler = () => setGuestMode(true);
    window.addEventListener('guest-mode', handler);
    return () => window.removeEventListener('guest-mode', handler);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-900">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-500">Loading GestureHub…</p>
        </div>
      </div>
    );
  }

  if (!user && !guestMode) {
    return <LoginForm />;
  }

  return <Dashboard />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
