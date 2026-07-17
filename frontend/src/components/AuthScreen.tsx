import React, { useState } from 'react';
import { Mail, Lock, Shield, ArrowRight } from 'lucide-react';

interface AuthScreenProps {
  onAuthSuccess: (token: string, role: string) => void;
  sessionExpired?: boolean;
}

export default function AuthScreen({ onAuthSuccess, sessionExpired }: AuthScreenProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Planner');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const baseUrl = 'http://127.0.0.1:8000/api/auth';
    const endpoint = isLogin ? '/login' : '/register';

    try {
      if (isLogin) {
        // Form encoded for OAuth2 /login
        const params = new URLSearchParams();
        params.append('username', email);
        params.append('password', password);

        const response = await fetch(`${baseUrl}${endpoint}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: params,
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Authentication failed');
        }

        const data = await response.json();
        onAuthSuccess(data.access_token, data.role);
      } else {
        // JSON payload for registration
        const response = await fetch(`${baseUrl}${endpoint}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email, password, role }),
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Registration failed');
        }

        // Auto login on successful register
        const params = new URLSearchParams();
        params.append('username', email);
        params.append('password', password);

        const loginRes = await fetch(`${baseUrl}/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: params,
        });

        const data = await loginRes.json();
        onAuthSuccess(data.access_token, data.role);
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#090d16] relative overflow-hidden px-4">
      {/* Background glowing decorations */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-accent opacity-10 blur-[120px] rounded-full"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-neonCyan opacity-10 blur-[120px] rounded-full"></div>

      <div className="w-full max-w-md glass-panel-glow rounded-2xl p-8 relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600/20 border border-blue-500/30 rounded-2xl flex items-center justify-center mb-4">
            <span className="text-3xl">🏙️</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-blue-400 bg-clip-text text-transparent">
            MIRROR CITY
          </h1>
          <p className="text-sm text-slate-400 mt-2">
            See the future of your city before it happens.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {sessionExpired && !error && (
            <div className="p-3 bg-amber-950/40 border border-brand-neonOrange/30 text-amber-300 text-xs rounded-xl shadow-[0_0_15px_rgba(249,115,22,0.1)] flex items-start gap-2">
              <span className="text-brand-neonOrange font-bold text-sm">🔐</span>
              <div>
                <strong className="block font-bold text-white mb-0.5">Session Expired</strong>
                Your security credentials were reset or expired. Please sign in again.
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-950/50 border border-red-500/40 text-red-300 text-xs rounded-lg">
              ⚠️ {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                <Mail size={16} />
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="planner@mirrorcity.gov"
                className="w-full bg-[#0d1220] border border-brand-border rounded-xl py-3 pl-10 pr-4 text-sm text-gray-200 focus:outline-none focus:border-brand-neonCyan transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                <Lock size={16} />
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#0d1220] border border-brand-border rounded-xl py-3 pl-10 pr-4 text-sm text-gray-200 focus:outline-none focus:border-brand-neonCyan transition-all"
              />
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Planning Role
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                  <Shield size={16} />
                </span>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-[#0d1220] border border-brand-border rounded-xl py-3 pl-10 pr-4 text-sm text-gray-200 focus:outline-none focus:border-brand-neonCyan transition-all appearance-none cursor-pointer"
                >
                  <option value="Planner">Urban Planner</option>
                  <option value="Government Official">Government Official</option>
                  <option value="Researcher">Academic Researcher</option>
                  <option value="Citizen">General Citizen</option>
                  <option value="Administrator">Administrator</option>
                </select>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 mt-8"
          >
            {loading ? 'Processing...' : isLogin ? 'Access Platform' : 'Create Account'}
            <ArrowRight size={16} />
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-xs text-brand-neonCyan hover:underline focus:outline-none"
          >
            {isLogin
              ? "Need access? Request a credentials account here."
              : "Already have an account? Sign in here."}
          </button>
        </div>
      </div>
    </div>
  );
}
