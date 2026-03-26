import { useState } from 'react';

function Slider({ label, value, min, max, step, onChange, description }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label className="text-sm text-gray-300">{label}</label>
        <span className="text-xs font-mono text-accent">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded appearance-none bg-gray-700 accent-current cursor-pointer"
        style={{ accentColor: '#00FFCC' }}
      />
      {description && <p className="text-xs text-gray-500">{description}</p>}
    </div>
  );
}

function Toggle({ label, checked, onChange, description }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div>
        <p className="text-sm text-gray-300">{label}</p>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`
          relative flex-shrink-0 w-10 h-5 rounded-full transition-colors duration-200
          ${checked ? 'bg-accent' : 'bg-gray-700'}
        `}
      >
        <span
          className={`
            absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-200
            ${checked ? 'translate-x-5' : 'translate-x-0.5'}
          `}
        />
      </button>
    </div>
  );
}

export default function AccessibilityPanel({ settings, onSettingsChange }) {
  const {
    sensitivity = 0.7,
    tremorFilter = false,
    gestureDelayMs = 300,
  } = settings || {};

  function update(key, value) {
    onSettingsChange?.({ ...settings, [key]: value });
  }

  return (
    <div className="bg-dark-800 border border-gray-700 rounded-xl p-5 space-y-5">
      <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-widest">
        Accessibility Settings
      </h2>

      <Slider
        label="Detection Sensitivity"
        value={sensitivity}
        min={0.3}
        max={1.0}
        step={0.05}
        onChange={(v) => update('sensitivity', v)}
        description="Higher values require clearer gestures"
      />

      <Slider
        label="Gesture Delay (ms)"
        value={gestureDelayMs}
        min={100}
        max={1500}
        step={50}
        onChange={(v) => update('gestureDelayMs', v)}
        description="Cooldown between gesture confirmations"
      />

      <Toggle
        label="Tremor Filter"
        checked={tremorFilter}
        onChange={(v) => update('tremorFilter', v)}
        description="Smooths out unintentional rapid hand movements"
      />

      <div className="pt-2 border-t border-gray-700">
        <p className="text-xs text-gray-500 mb-3 uppercase tracking-wider">Gesture Reference</p>
        <div className="grid grid-cols-2 gap-1.5 text-xs font-mono">
          {[
            ['👍', 'THUMBS UP', 'Volume Up'],
            ['👎', 'THUMBS DOWN', 'Volume Down'],
            ['✌️', 'PEACE', 'Next Track'],
            ['🖐️', 'OPEN PALM', 'Reset'],
            ['✊', 'FIST', 'Play/Pause'],
            ['☝️', 'INDEX', 'Toggle LED'],
            ['🤘', 'ROCK', 'Toggle Motor'],
            ['✌️', 'TWO FINGERS', 'Swipe'],
          ].map(([emoji, name, action]) => (
            <div key={name} className="flex items-center gap-1.5 text-gray-400">
              <span>{emoji}</span>
              <span className="text-gray-500">{action}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
