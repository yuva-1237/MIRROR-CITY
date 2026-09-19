import React, { useState } from 'react';
import { Mail, Lock, Shield, ArrowRight, CheckCircle2 } from 'lucide-react';
import {
  auth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword
} from '../lib/firebase';

interface AuthScreenProps {
  onAuthSuccess: (token: string, role: string) => void;
  sessionExpired?: boolean;
}

export default function AuthScreen({ onAuthSuccess, sessionExpired }: AuthScreenProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('yuvathilagan@gmail.com');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Planner');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [mustChangePassword, setMustChangePassword] = useState(false);
  const [tempToken, setTempToken] = useState('');
  const [tempRole, setTempRole] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const baseUrl = (import.meta as any).env?.VITE_API_URL || 'http://127.0.0.1:8000';

  const exchangeWithBackend = async (
    userEmail: string,
    userRole: string,
    uid?: string,
    displayName?: string,
    userPassword?: string
  ) => {
    const res = await fetch(`${baseUrl}/api/auth/firebase-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: userEmail,
        role: userRole,
        firebase_uid: uid,
        display_name: displayName || userEmail.split('@')[0],
        password: userPassword,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Authentication failed. Please verify your connection.');
    }

    const data = await res.json();
    return data;
  };

  const handlePostAuth = (authData: { access_token: string; role: string; must_change_password?: boolean }) => {
    if (authData.must_change_password) {
      setTempToken(authData.access_token);
      setTempRole(authData.role);
      setMustChangePassword(true);
      setError('');
    } else {
      onAuthSuccess(authData.access_token, authData.role);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match. Please verify.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${baseUrl}/api/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tempToken}`,
        },
        body: JSON.stringify({
          new_password: newPassword,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to update password.');
      }

      // Password changed successfully, proceed into the platform
      onAuthSuccess(tempToken, tempRole);
    } catch (err: any) {
      setError(err.message || 'Error changing password.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setError('Please enter a valid email address.');
      setLoading(false);
      return;
    }

    try {
      if (isLogin) {
        // 1. Try Firebase Auth if configured
        let fbSuccess = false;
        try {
          const userCredential = await signInWithEmailAndPassword(auth, cleanEmail, password);
          const fbUser = userCredential.user;
          const authData = await exchangeWithBackend(
            fbUser.email || cleanEmail,
            role,
            fbUser.uid,
            fbUser.displayName || undefined,
            password
          );
          fbSuccess = true;
          handlePostAuth(authData);
          return;
        } catch (firebaseErr: any) {
          // Fallback to digital twin backend auth
        }

        if (!fbSuccess) {
          // 2. Direct backend authentication
          const authData = await exchangeWithBackend(
            cleanEmail,
            role,
            undefined,
            cleanEmail.split('@')[0],
            password
          );
          handlePostAuth(authData);
          return;
        }
      } else {
        // Registration Flow
        let fbSuccess = false;
        try {
          const userCredential = await createUserWithEmailAndPassword(auth, cleanEmail, password);
          const fbUser = userCredential.user;
          const authData = await exchangeWithBackend(
            fbUser.email || cleanEmail,
            role,
            fbUser.uid,
            fbUser.displayName || undefined,
            password
          );
          fbSuccess = true;
          handlePostAuth(authData);
          return;
        } catch (firebaseErr: any) {
          // Fallback to local DB registration
        }

        if (!fbSuccess) {
          const authData = await exchangeWithBackend(
            cleanEmail,
            role,
            undefined,
            cleanEmail.split('@')[0],
            password
          );
          handlePostAuth(authData);
          return;
        }
      }
    } catch (err: any) {
      console.error('[Auth] Login error:', err);
      setError(err.message || 'Unable to sign in. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#090d16] relative overflow-hidden px-4">
      {/* Ambient background glow effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-accent opacity-10 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-neonCyan opacity-10 blur-[120px] rounded-full pointer-events-none"></div>

      <div className="w-full max-w-md glass-panel-glow rounded-2xl p-8 relative z-10 border border-slate-800 bg-[#0d1322]/90 backdrop-blur-xl shadow-2xl">
        <div className="flex flex-col items-center mb-6">
          <div className="w-16 h-16 bg-blue-600/20 border border-blue-500/30 rounded-2xl flex items-center justify-center mb-3 shadow-[0_0_20px_rgba(59,130,246,0.3)]">
            <span className="text-3xl">🏙️</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-blue-400 bg-clip-text text-transparent">
            MIRROR CITY
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            See the future of your city before it happens.
          </p>
          <div className="mt-3 flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-[11px] font-medium text-emerald-400">
            <CheckCircle2 size={12} className="text-emerald-400" />
            <span>AI Digital Twin Engine Online</span>
          </div>
        </div>

        {mustChangePassword ? (
          /* Forced Password Change on First Login */
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="p-3 bg-amber-950/40 border border-brand-neonOrange/30 text-amber-300 text-xs rounded-xl shadow-[0_0_15px_rgba(249,115,22,0.1)] flex items-start gap-2">
              <span className="text-brand-neonOrange font-bold text-sm">🔒</span>
              <div>
                <strong className="block font-bold text-white mb-0.5">Initial Setup: Password Change Required</strong>
                Security policy requires establishing a new personal password on first login before accessing municipal panels.
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-950/50 border border-red-500/40 text-red-300 text-xs rounded-xl">
                ⚠️ {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                New Secure Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full bg-[#090d16] border border-slate-700/80 rounded-xl py-2.5 pl-10 pr-4 text-sm text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Confirm New Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat new password"
                  className="w-full bg-[#090d16] border border-slate-700/80 rounded-xl py-2.5 pl-10 pr-4 text-sm text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 mt-5"
            >
              {loading ? 'Securing Account...' : 'Set Password & Enter Digital Twin'}
              <ArrowRight size={16} />
            </button>
          </form>
        ) : (
          /* Standard Login / Registration Form */
          <form onSubmit={handleSubmit} className="space-y-4">
            {sessionExpired && !error && (
              <div className="p-3 bg-amber-950/40 border border-brand-neonOrange/30 text-amber-300 text-xs rounded-xl shadow-[0_0_15px_rgba(249,115,22,0.1)] flex items-start gap-2">
                <span className="text-brand-neonOrange font-bold text-sm">🔐</span>
                <div>
                  <strong className="block font-bold text-white mb-0.5">Session Expired</strong>
                  Your session has expired. Please sign in again.
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-950/50 border border-red-500/40 text-red-300 text-xs rounded-xl">
                ⚠️ {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
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
                  className="w-full bg-[#090d16] border border-slate-700/80 rounded-xl py-2.5 pl-10 pr-4 text-sm text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
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
                  className="w-full bg-[#090d16] border border-slate-700/80 rounded-xl py-2.5 pl-10 pr-4 text-sm text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>

            {!isLogin && (
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Planning Role
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-500">
                    <Shield size={16} />
                  </span>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full bg-[#090d16] border border-slate-700/80 rounded-xl py-2.5 pl-10 pr-4 text-sm text-gray-100 focus:outline-none focus:border-blue-500 transition-all appearance-none cursor-pointer"
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
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 mt-5"
            >
              {loading ? 'Authenticating...' : isLogin ? 'Sign In' : 'Create Account & Enter'}
              <ArrowRight size={16} />
            </button>

            <div className="mt-5 text-center">
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                }}
                className="text-xs text-blue-400 hover:text-blue-300 hover:underline focus:outline-none font-medium"
              >
                {isLogin
                  ? "Need a new account? Register here."
                  : "Already have an account? Sign in here."}
              </button>
            </div>
          </form>
        )}

        {/* Security & Authentication Info */}
        <div className="mt-6 pt-4 border-t border-slate-800/80 text-center">
          <p className="text-[11px] text-slate-500 flex items-center justify-center gap-1.5">
            <span>🛡️</span>
            <span>Zero Default Credentials • Bcrypt Salted Hash • JWT Encrypted</span>
          </p>
        </div>
      </div>
    </div>
  );
}
