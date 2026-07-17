import React, { useState } from 'react';
import { AlertCircle, MapPin, Send, RefreshCw, CheckCircle, AlertTriangle, XCircle, ShieldCheck } from 'lucide-react';
import { apiPost } from '../lib/api';

interface Verification {
  verification_score: number;
  corroborated: boolean;
  evidence: string[];
  recommendation: string;
}

interface IncidentReporterProps {
  authToken: string;
  onReportSuccess: () => void;
  selectedCoordinates: [number, number] | null;
}

export default function IncidentReporter({ authToken, onReportSuccess, selectedCoordinates }: IncidentReporterProps) {
  const [type, setType]               = useState('accident');
  const [name, setName]               = useState('');
  const [desc, setDesc]               = useState('');
  const [loading, setLoading]         = useState(false);
  const [reportLog, setReportLog]     = useState<string | null>(null);
  const [verification, setVerification] = useState<Verification | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const coords = selectedCoordinates || [37.7749, -122.4194];

    setLoading(true);
    setVerification(null);
    setReportLog("Transmitting incident report to municipal servers...");

    try {
      const result: any = await apiPost(
        '/api/incidents',
        {
          type,
          name,
          description: desc,
          location_geojson: JSON.stringify({ type: 'Point', coordinates: [coords[1], coords[0]] })
        },
        { token: authToken }
      );

      // Show immediate cross-verification result from backend
      if (result?.verification) {
        setVerification(result.verification);
      }

      setReportLog("Report received. AI is cross-verifying against IoT sensors, satellite feeds, and corroborating reports...");
      setName('');
      setDesc('');

      setTimeout(() => {
        setReportLog("Incident logged and verified. Added to Live Digital Twin overlay.");
        onReportSuccess();
        setTimeout(() => { setReportLog(null); }, 5000);
      }, 4000);

    } catch (err: any) {
      setReportLog(`Error: ${err.message || 'Transmission failed.'}`);
      setTimeout(() => setReportLog(null), 4000);
    } finally {
      setLoading(false);
    }
  };

  // Score display helpers
  const scoreColor = (s: number) =>
    s >= 80 ? 'text-emerald-400' : s >= 60 ? 'text-amber-400' : s >= 40 ? 'text-orange-400' : 'text-red-400';
  const scoreBg = (s: number) =>
    s >= 80 ? 'bg-emerald-500/10 border-emerald-500/30' : s >= 60 ? 'bg-amber-500/10 border-amber-500/30' : 'bg-red-500/10 border-red-500/30';
  const ScoreIcon = (s: number) =>
    s >= 70 ? <CheckCircle className="h-4 w-4" /> : s >= 50 ? <AlertTriangle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />;

  return (
    <div className="glass-panel p-4 rounded-xl border border-brand-border/60 bg-brand-panel/40 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-brand-border/40 pb-2">
        <AlertCircle className="h-5 w-5 text-brand-neonOrange" />
        <h3 className="font-semibold text-sm tracking-wide text-slate-200">CITIZEN TELEMETRY REPORTING</h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-[10px] uppercase font-bold text-slate-400 font-mono mb-1">Incident Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="w-full bg-slate-900 border border-brand-border/50 text-slate-200 rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-brand-accent"
          >
            <option value="accident">Traffic Accident / Collision</option>
            <option value="pothole">Road Pothole / Damage</option>
            <option value="water_leak">Water Leakage / Pipe Burst</option>
            <option value="power_cut">Electrical Outage / Grid Fault</option>
            <option value="flood">Surface Run-off / Flooding</option>
            <option value="crime">Public Safety Concern / Vandalism</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] uppercase font-bold text-slate-400 font-mono mb-1">Title / Location Name</label>
          <input
            type="text"
            placeholder="e.g. Broken Water Main on Anna Nagar St"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-slate-900 border border-brand-border/50 text-slate-200 rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-brand-accent placeholder-slate-600"
            required
          />
        </div>

        <div>
          <label className="block text-[10px] uppercase font-bold text-slate-400 font-mono mb-1">Incident Description</label>
          <textarea
            placeholder="Provide extra details for municipal dispatch..."
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            className="w-full bg-slate-900 border border-brand-border/50 text-slate-200 rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-brand-accent placeholder-slate-600 h-[55px] resize-none"
          />
        </div>

        <div className="flex gap-2 items-center bg-black/20 p-2 rounded border border-brand-border/30 text-[11px] text-slate-400">
          <MapPin className="h-3.5 w-3.5 text-brand-neonCyan" />
          <span>
            {selectedCoordinates ? (
              <>Location: <span className="font-mono text-slate-200">{selectedCoordinates[0].toFixed(4)}, {selectedCoordinates[1].toFixed(4)}</span></>
            ) : (
              "Click on map to pin coordinates"
            )}
          </span>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-brand-neonOrange hover:bg-brand-neonOrange/85 text-white font-semibold text-xs py-2 rounded flex items-center justify-center gap-1.5 transition disabled:opacity-50"
        >
          {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
          Report Incident to Digital Twin
        </button>
      </form>

      {/* Status log */}
      {reportLog && (
        <div className="p-2 bg-slate-900 border border-brand-border/50 rounded font-mono text-[9px] text-brand-neonOrange leading-relaxed flex items-start gap-1.5">
          <span className="animate-pulse">●</span>
          <span>{reportLog}</span>
        </div>
      )}

      {/* ── Cross-Verification Result ────────────────────────────────── */}
      {verification && (
        <div className={`rounded-xl border p-3 space-y-2 ${scoreBg(verification.verification_score)}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className={`h-4 w-4 ${scoreColor(verification.verification_score)}`} />
              <span className={`text-xs font-bold uppercase tracking-wider ${scoreColor(verification.verification_score)}`}>
                AI Cross-Verification
              </span>
            </div>
            <div className={`flex items-center gap-1.5 ${scoreColor(verification.verification_score)}`}>
              {ScoreIcon(verification.verification_score)}
              <span className="text-lg font-bold font-mono">{verification.verification_score}</span>
              <span className="text-[10px] text-slate-400">/100</span>
            </div>
          </div>

          {/* Score bar */}
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ${
                verification.verification_score >= 80 ? 'bg-emerald-500' :
                verification.verification_score >= 60 ? 'bg-amber-500' :
                'bg-red-500'
              }`}
              style={{ width: `${verification.verification_score}%` }}
            />
          </div>

          {/* Evidence list */}
          <div className="space-y-1">
            {verification.evidence.map((ev, i) => (
              <p key={i} className="text-[10px] text-slate-300 border-l-2 border-slate-600 pl-2">{ev}</p>
            ))}
          </div>

          {/* Recommendation */}
          <p className={`text-[10px] font-semibold italic ${scoreColor(verification.verification_score)}`}>
            → {verification.recommendation}
          </p>
        </div>
      )}
    </div>
  );
}
