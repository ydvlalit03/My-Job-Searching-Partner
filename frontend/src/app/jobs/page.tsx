"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [savedJobs, setSavedJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState("");
  const [tab, setTab] = useState<"search" | "saved">("search");

  const searchJobs = async () => {
    setLoading(true);
    try {
      const results = await api.searchJobs(role || undefined);
      setJobs(results);
    } catch (err: any) {
      alert(err.message);
    }
    setLoading(false);
  };

  const loadSaved = async () => {
    try {
      const saved = await api.getSavedJobs();
      setSavedJobs(saved);
    } catch {}
  };

  useEffect(() => {
    loadSaved();
  }, []);

  const saveJob = async (index: number) => {
    try {
      await api.saveJob(index, role || undefined);
      await loadSaved();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const updateStatus = async (id: string, status: string) => {
    try {
      await api.updateJobStatus(id, status);
      await loadSaved();
    } catch {}
  };

  return (
    <ProtectedRoute>
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>

        {/* Tabs */}
        <div className="mt-4 flex gap-1 bg-gray-100 rounded-lg p-1 w-fit">
          {(["search", "saved"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                tab === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {t === "search" ? "Search Jobs" : `Saved (${savedJobs.length})`}
            </button>
          ))}
        </div>

        {tab === "search" && (
          <>
            <div className="mt-4 flex gap-3">
              <input
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Role (leave empty for auto-selected role)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
              <button
                onClick={searchJobs}
                disabled={loading}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? "Searching..." : "Search"}
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {jobs.map((job, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{job.title}</h3>
                      <p className="text-sm text-gray-600 mt-0.5">
                        {job.company} {job.location && `| ${job.location}`}
                        {job.is_remote && " | Remote"}
                      </p>
                      {job.salary_range && (
                        <p className="text-sm text-green-600 mt-1">{job.salary_range}</p>
                      )}
                      {job.match_details && (
                        <div className="mt-2 flex gap-3 text-xs text-gray-500">
                          <span>Skill: {job.match_details.skill_score}</span>
                          <span>Location: {job.match_details.location_score}</span>
                          <span>Exp: {job.match_details.experience_score}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <span className={`text-lg font-bold ${job.match_score >= 70 ? "text-green-600" : job.match_score >= 40 ? "text-yellow-600" : "text-gray-400"}`}>
                        {job.match_score}
                      </span>
                      <div className="flex gap-2">
                        {job.apply_url && (
                          <a
                            href={job.apply_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700"
                          >
                            Apply
                          </a>
                        )}
                        <button
                          onClick={() => saveJob(i)}
                          className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded text-xs font-medium hover:bg-indigo-200"
                        >
                          Save
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {tab === "saved" && (
          <div className="mt-4 space-y-3">
            {savedJobs.length === 0 && (
              <p className="text-sm text-gray-500 py-8 text-center">No saved jobs yet. Search and save jobs first.</p>
            )}
            {savedJobs.map((job) => (
              <div key={job.id} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-gray-900">{job.title}</h3>
                    <p className="text-sm text-gray-600">{job.company}</p>
                  </div>
                  <select
                    value={job.status}
                    onChange={(e) => updateStatus(job.id, e.target.value)}
                    className={`text-xs font-medium px-3 py-1 rounded-full border-0 ${
                      job.status === "applied" ? "bg-blue-100 text-blue-700" :
                      job.status === "interview" ? "bg-green-100 text-green-700" :
                      job.status === "rejected" ? "bg-red-100 text-red-700" :
                      "bg-gray-100 text-gray-700"
                    }`}
                  >
                    <option value="matched">Matched</option>
                    <option value="applied">Applied</option>
                    <option value="interview">Interview</option>
                    <option value="rejected">Rejected</option>
                    <option value="offered">Offered</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
