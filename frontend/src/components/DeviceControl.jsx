const COMMANDS = {
  LED_RED: { on: 'LED_RED_ON', off: 'LED_RED_OFF', color: '#ef4444', label: 'Red LED' },
  LED_BLUE: { on: 'LED_BLUE_ON', off: 'LED_BLUE_OFF', color: '#3b82f6', label: 'Blue LED' },
  LED_GREEN: { on: 'LED_GREEN_ON', off: 'LED_GREEN_OFF', color: '#22c55e', label: 'Green LED' },
};

function LEDButton({ label, color, active, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className={`
        flex flex-col items-center gap-2 p-4 rounded-xl border transition-all duration-200
        ${active
          ? 'border-current bg-current/10'
          : 'border-gray-700 bg-dark-700 hover:border-gray-500'
        }
      `}
      style={{ color: active ? color : '#6b7280' }}
    >
      <div
        className="w-8 h-8 rounded-full border-2 transition-all duration-200"
        style={{
          borderColor: active ? color : '#374151',
          backgroundColor: active ? color : 'transparent',
          boxShadow: active ? `0 0 12px ${color}88` : 'none',
        }}
      />
      <span className="text-xs font-mono">{label}</span>
    </button>
  );
}

export default function DeviceControl({ deviceState, onCommand, connected, lastAction }) {
  const isEsp32Connected = deviceState?.connected;

  function toggleMotor() {
    onCommand?.(deviceState?.motor ? 'MOTOR_OFF' : 'MOTOR_ON');
  }

  return (
    <div className="bg-dark-800 border border-gray-700 rounded-xl p-5 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-widest">
          Device Control
        </h2>
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${isEsp32Connected ? 'bg-green-400' : 'bg-gray-600'}`}
          />
          <span className="text-xs text-gray-400">
            {isEsp32Connected ? 'ESP32 Online' : 'ESP32 Offline'}
          </span>
        </div>
      </div>

      {/* LEDs */}
      <div>
        <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">LEDs</p>
        <div className="grid grid-cols-3 gap-2">
          <LEDButton
            label="Red LED"
            color="#ef4444"
            active={!!deviceState?.led_red}
            onToggle={() => onCommand?.(deviceState?.led_red ? 'LED_RED_OFF' : 'LED_RED_ON')}
          />
          <LEDButton
            label="Blue LED"
            color="#3b82f6"
            active={!!deviceState?.led_blue}
            onToggle={() => onCommand?.(deviceState?.led_blue ? 'LED_BLUE_OFF' : 'LED_BLUE_ON')}
          />
          <LEDButton
            label="Green LED"
            color="#22c55e"
            active={!!deviceState?.led_green}
            onToggle={() => onCommand?.(deviceState?.led_green ? 'LED_GREEN_OFF' : 'LED_GREEN_ON')}
          />
        </div>
      </div>

      {/* Motor */}
      <div>
        <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">DC Motor</p>
        <button
          onClick={toggleMotor}
          className={`
            w-full py-3 rounded-xl border font-mono text-sm transition-all duration-200
            ${deviceState?.motor
              ? 'border-accent text-accent bg-accent/10 glow'
              : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }
          `}
        >
          {deviceState?.motor ? '⚙️ Motor Running' : '⚙️ Motor Stopped'}
        </button>
      </div>

      {/* Reset */}
      <button
        onClick={() => onCommand?.('RESET')}
        className="w-full py-2.5 rounded-xl border border-red-800 text-red-400 text-sm font-mono hover:bg-red-900/20 transition-colors"
      >
        🔄 Reset All
      </button>

      {/* Last action */}
      {lastAction && (
        <div className="rounded-lg bg-dark-700 border border-gray-700 p-3">
          <p className="text-xs text-gray-500 mb-1">Last Gesture Action</p>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-accent">{lastAction.gesture}</span>
            <span className="text-xs font-mono text-gray-300">→ {lastAction.action}</span>
          </div>
        </div>
      )}
    </div>
  );
}
