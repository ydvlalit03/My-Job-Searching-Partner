"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function ResumePage() {
  const [profile, setProfile] = useState<any>(null);
  const [atsResult, setAtsResult] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [targetRole, setTargetRole] = useState("");

  useEffect(() => {
    api.getProfile().then(setProfile).catch(() => {});
  }, []);

  const uploadResume = async (file: File) => {
    setUploading(true);
    try {
      const result = await api.uploadResume(file);
      setProfile(result);
    } catch (err: any) {
      alert(err.message);
    }
    setUploading(false);
  };

  const runAtsScore = async () => {
    setScoring(true);
    try {
      const result = await api.getAtsScore(targetRole || undefined);
      setAtsResult(result);
    } catch (err: any) {
      alert(err.message);
    }
    setScoring(false);
  };

  return (
    <ProtectedRoute>
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900">Resume</h1>

        {/* Upload */}
        <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-3">Upload Resume (PDF)</h2>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => e.target.files?.[0] && uploadResume(e.target.files[0])}
            disabled={uploading}
            className="text-sm"
          />
          {uploading && <p className="mt-2 text-sm text-indigo-600">Parsing with AI...</p>}
        </div>

        {/* Parsed Profile */}
        {profile && (
          <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Parsed Resume</h2>

            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Skills ({profile.skills?.length || 0})</h3>
              <div className="flex flex-wrap gap-2">
                {profile.skills?.map((s: string) => (
                  <span key={s} className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-sm">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Experience ({profile.total_experience_years} years)</h3>
              {profile.experience?.map((e: any, i: number) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg mb-2 text-sm">
                  {e.title && <span className="font-medium">{e.title}</span>}
                  {e.company && <span className="text-gray-500"> at {e.company}</span>}
                  {e.detail && <p className="text-gray-600">{e.detail}</p>}
                </div>
              ))}
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Education</h3>
              {profile.education?.map((e: any, i: number) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg mb-2 text-sm">
                  <span className="font-medium">{e.degree || e.detail}</span>
                  {e.institution && <span className="text-gray-500"> — {e.institution}</span>}
                  {e.year && <span className="text-gray-400 ml-2">({e.year})</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ATS Score */}
        {profile && (
          <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-3">ATS Score</h2>
            <div className="flex items-center gap-3 mb-4">
              <input
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="Target role (e.g. Backend Developer)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
              <button
                onClick={runAtsScore}
                disabled={scoring}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
              >
                {scoring ? "Scoring..." : "Score Resume"}
              </button>
            </div>

            {atsResult && (
              <div>
                <div className="flex items-center gap-6 mb-6">
                  <div className="text-center">
                    <div className={`text-4xl font-bold ${atsResult.score >= 70 ? "text-green-600" : atsResult.score >= 40 ? "text-yellow-600" : "text-red-600"}`}>
                      {atsResult.score}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Overall</div>
                  </div>
                  <div className="flex-1 grid grid-cols-3 gap-4">
                    {[
                      { label: "Keywords", value: atsResult.keyword_score, max: 40 },
                      { label: "Format", value: atsResult.format_score, max: 20 },
                      { label: "Achievements", value: atsResult.achievement_score, max: 20 },
                    ].map((item) => (
                      <div key={item.label}>
                        <div className="text-sm text-gray-500">{item.label}</div>
                        <div className="mt-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full"
                            style={{ width: `${(item.value / item.max) * 100}%` }}
                          />
                        </div>
                        <div className="text-xs text-gray-500 mt-1">{item.value}/{item.max}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {atsResult.missing_keywords?.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Missing Keywords</h4>
                    <div className="flex flex-wrap gap-2">
                      {atsResult.missing_keywords.map((kw: string) => (
                        <span key={kw} className="px-2 py-1 bg-red-50 text-red-600 rounded text-xs">{kw}</span>
                      ))}
                    </div>
                  </div>
                )}

                {atsResult.suggestions?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Suggestions</h4>
                    <ul className="space-y-1">
                      {atsResult.suggestions.map((s: string, i: number) => (
                        <li key={i} className="text-sm text-gray-600 flex gap-2">
                          <span className="text-indigo-500">&#8227;</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
