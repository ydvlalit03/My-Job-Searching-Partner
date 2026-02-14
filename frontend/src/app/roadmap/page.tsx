"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function RoadmapPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [referralMsg, setReferralMsg] = useState<any>(null);
  const [refRole, setRefRole] = useState("");
  const [refCompany, setRefCompany] = useState("");
  const [refLoading, setRefLoading] = useState(false);

  const generateRoadmap = async () => {
    setLoading(true);
    try {
      const plan = await api.generateRoadmap(7);
      setEntries(plan);
    } catch (err: any) {
      alert(err.message);
    }
    setLoading(false);
  };

  const updateProgress = async (id: string, field: string, value: number) => {
    try {
      const result = await api.updateProgress(id, { [field]: value });
      setEntries((prev) => prev.map((e) => (e.id === id ? result : e)));
    } catch {}
  };

  const generateReferral = async () => {
    if (!refRole || !refCompany) return;
    setRefLoading(true);
    try {
      const msg = await api.getReferralMessage({ job_role: refRole, company_name: refCompany });
      setReferralMsg(msg);
    } catch (err: any) {
      alert(err.message);
    }
    setRefLoading(false);
  };

  return (
    <ProtectedRoute>
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Daily Roadmap</h1>
          <button
            onClick={generateRoadmap}
            disabled={loading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate 7-Day Plan"}
          </button>
        </div>

        {entries.length > 0 && (
          <div className="mt-6 space-y-4">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className={`bg-white rounded-xl border p-5 ${
                  entry.is_completed ? "border-green-300 bg-green-50" : "border-gray-200"
                }`}
              >
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{entry.date}</h3>
                    {entry.daily_tips?.focus && (
                      <span className="text-xs text-indigo-600 font-medium">
                        {entry.daily_tips.focus}
                      </span>
                    )}
                  </div>
                  {entry.is_completed && (
                    <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      Completed
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-4 mb-3">
                  {[
                    { label: "Jobs Applied", field: "jobs_applied", target: entry.jobs_to_apply, current: entry.jobs_applied },
                    { label: "Referrals Sent", field: "referrals_sent", target: entry.referrals_to_send, current: entry.referrals_sent },
                    { label: "Recruiters", field: "recruiters_connected", target: entry.recruiters_to_connect, current: entry.recruiters_connected },
                  ].map((item) => (
                    <div key={item.field}>
                      <div className="text-xs text-gray-500 mb-1">{item.label}</div>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min={0}
                          value={item.current}
                          onChange={(e) => updateProgress(entry.id, item.field, parseInt(e.target.value) || 0)}
                          className="w-16 px-2 py-1 border border-gray-300 rounded text-sm text-center"
                        />
                        <span className="text-xs text-gray-400">/ {item.target}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {entry.daily_tips?.tasks?.length > 0 && (
                  <div className="border-t border-gray-100 pt-3">
                    <ul className="space-y-1">
                      {entry.daily_tips.tasks.map((task: string, i: number) => (
                        <li key={i} className="text-sm text-gray-600 flex gap-2">
                          <span className="text-indigo-400">&#8227;</span> {task}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Referral Message Generator */}
        <div className="mt-10 bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Referral Message Generator</h2>
          <div className="grid md:grid-cols-2 gap-3 mb-4">
            <input
              value={refRole}
              onChange={(e) => setRefRole(e.target.value)}
              placeholder="Job Role (e.g. Frontend Developer)"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            />
            <input
              value={refCompany}
              onChange={(e) => setRefCompany(e.target.value)}
              placeholder="Company Name (e.g. Google)"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <button
            onClick={generateReferral}
            disabled={refLoading || !refRole || !refCompany}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
          >
            {refLoading ? "Generating..." : "Generate Message"}
          </button>

          {referralMsg && (
            <div className="mt-4 bg-gray-50 rounded-lg p-4">
              {referralMsg.subject_line && (
                <div className="mb-2">
                  <span className="text-xs font-medium text-gray-500">Subject:</span>
                  <p className="text-sm font-medium text-gray-900">{referralMsg.subject_line}</p>
                </div>
              )}
              <div>
                <span className="text-xs font-medium text-gray-500">Message:</span>
                <p className="text-sm text-gray-800 whitespace-pre-wrap mt-1">{referralMsg.message}</p>
              </div>
              <button
                onClick={() => navigator.clipboard.writeText(referralMsg.message)}
                className="mt-3 px-4 py-1.5 bg-white border border-gray-300 rounded text-xs font-medium text-gray-700 hover:bg-gray-50"
              >
                Copy to Clipboard
              </button>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
