import React, { useState, useEffect } from 'react';
import { Users, FileText, Database, ShieldAlert, Check } from 'lucide-react';

interface AdminPanelProps {
  authToken: string;
}

interface User {
  id: number;
  email: string;
  role: string;
  created_at: string;
}

interface AuditLog {
  id: number;
  user_id: number;
  action: string;
  timestamp: string;
}

export default function AdminPanel({ authToken }: AdminPanelProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      // Fetch users
      const usersRes = await fetch('http://localhost:8000/api/admin/users', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (!usersRes.ok) throw new Error("Failed to fetch user list. Ensure you have Admin privileges.");
      const usersData = await usersRes.json();
      setUsers(usersData);

      // Fetch logs
      const logsRes = await fetch('http://localhost:8000/api/admin/logs', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      const logsData = await logsRes.json();
      setLogs(logsData);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load admin telemetry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [authToken]);

  const handleRoleChange = async (userId: number, newRole: string) => {
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const response = await fetch(`http://localhost:8000/api/admin/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ role: newRole })
      });
      if (!response.ok) throw new Error("Failed to update user role");
      
      setSuccessMsg("User role updated successfully.");
      fetchData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update role.");
    }
  };

  const handleReseed = async () => {
    if (!window.confirm("Are you sure you want to re-seed the system? This will clear all scenarios and restore default data.")) return;
    setSeeding(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const response = await fetch('http://localhost:8000/api/admin/seed', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (!response.ok) throw new Error("Reseeding failed");
      const data = await response.json();
      setSuccessMsg(data.message || "System database re-seeded.");
      fetchData();
    } catch (err: any) {
      setErrorMsg(err.message || "Reseeding failed.");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <ShieldAlert className="text-brand-neonOrange" size={20} />
          Platform Admin Cockpit
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Manage system users, change planning roles, review spatial log audits, and restore baseline nodes.
        </p>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-950/40 border border-red-500/30 text-red-300 text-xs rounded-xl">
          ⚠️ {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="p-3 bg-green-950/40 border border-green-500/30 text-green-300 text-xs rounded-xl flex items-center gap-2">
          <Check size={14} className="text-brand-neonGreen" />
          {successMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User Management */}
        <div className="lg:col-span-2 bg-[#101625]/60 border border-brand-border p-5 rounded-2xl glass-panel space-y-4">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Users size={14} className="text-blue-500" />
            User Registration & Access Controls
          </h3>

          {loading ? (
            <div className="text-center text-xs text-slate-500 italic py-8">Loading users...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-brand-border text-slate-400 text-[10px] uppercase font-bold tracking-wider">
                    <th className="py-2.5 px-2">Email</th>
                    <th className="py-2.5 px-2">Active Role</th>
                    <th className="py-2.5 px-2">Assigned Date</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-brand-border/40 hover:bg-white/2 transition-all">
                      <td className="py-3 px-2 text-xs font-medium text-white">{u.email}</td>
                      <td className="py-3 px-2 text-xs">
                        <select
                          value={u.role}
                          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleRoleChange(u.id, e.target.value)}
                          className="bg-[#0d1220] border border-brand-border text-xs rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-brand-neonCyan cursor-pointer"
                        >
                          <option value="Citizen">Citizen</option>
                          <option value="Planner">Planner</option>
                          <option value="Government Official">Government Official</option>
                          <option value="Researcher">Researcher</option>
                          <option value="Administrator">Administrator</option>
                        </select>
                      </td>
                      <td className="py-3 px-2 text-xs text-slate-500">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Database Controls */}
        <div className="bg-[#101625]/60 border border-brand-border p-5 rounded-2xl glass-panel space-y-4">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Database size={14} className="text-brand-neonGreen" />
            System Seeding Controls
          </h3>
          <p className="text-[11px] leading-5 text-slate-400">
            Clicking Reseed clears all custom scenarios and elements, regenerates the 36-intersection coordinate grid, and reinstalls defaults.
          </p>
          <button
            onClick={handleReseed}
            disabled={seeding}
            className="w-full py-2.5 bg-brand-neonOrange/20 hover:bg-brand-neonOrange/30 text-brand-neonOrange border border-brand-neonOrange/40 font-semibold text-xs rounded-xl shadow-lg transition-all"
          >
            {seeding ? "Re-seeding database..." : "Reseed Database Tables"}
          </button>
        </div>
      </div>

      {/* Audit Logs */}
      <div className="bg-[#101625]/60 border border-brand-border p-5 rounded-2xl glass-panel space-y-4">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <FileText size={14} className="text-brand-neonPurple" />
          Audit Trail Log History
        </h3>
        {logs.length > 0 ? (
          <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
            {logs.map((log) => (
              <div key={log.id} className="p-3 bg-[#0d1220] border border-brand-border/40 rounded-xl flex justify-between text-xs items-center">
                <span className="text-slate-300 font-medium">{log.action}</span>
                <span className="text-[10px] text-slate-500">
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">No audit logs recorded.</p>
        )}
      </div>
    </div>
  );
}
