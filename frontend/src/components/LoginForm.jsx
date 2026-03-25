import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginForm() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        await login(form.username, form.password);
      } else {
        await register(form.username, form.email, form.password);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-900 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold" style={{ color: '#00FFCC' }}>
            GestureHub
          </h1>
          <p className="text-gray-500 text-sm mt-1">Real-time gesture control for IoT</p>
        </div>

        <div className="bg-dark-800 border border-gray-700 rounded-xl p-6">
          {/* Tabs */}
          <div className="flex mb-6 border-b border-gray-700">
            {['login', 'register'].map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(''); }}
                className={`flex-1 pb-2 text-sm font-mono capitalize transition-colors ${
                  mode === m
                    ? 'border-b-2 border-accent text-accent -mb-px'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Username</label>
              <input
                type="text"
                value={form.username}
                onChange={set('username')}
                required
                className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent transition-colors"
                placeholder="Enter username"
              />
            </div>

            {mode === 'register' && (
              <div>
                <label className="block text-xs text-gray-400 mb-1">Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={set('email')}
                  required
                  className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent transition-colors"
                  placeholder="Enter email"
                />
              </div>
            )}

            <div>
              <label className="block text-xs text-gray-400 mb-1">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={set('password')}
                required
                minLength={6}
                className="w-full bg-dark-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent transition-colors"
                placeholder={mode === 'register' ? 'Min. 6 characters' : 'Enter password'}
              />
            </div>

            {error && (
              <p className="text-red-400 text-xs bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg font-semibold text-sm transition-all disabled:opacity-50"
              style={{ backgroundColor: '#00FFCC', color: '#000' }}
            >
              {loading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Guest mode */}
          <div className="mt-4 pt-4 border-t border-gray-700 text-center">
            <p className="text-xs text-gray-500 mb-2">Just exploring?</p>
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('guest-mode'))}
              className="text-xs text-gray-400 hover:text-accent transition-colors underline"
            >
              Continue as guest (no gestures saved)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
