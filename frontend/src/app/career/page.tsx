"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function CareerPage() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [saved, setSaved] = useState(false);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const recs = await api.getRecommendations();
      setRecommendations(recs);
    } catch (err: any) {
      alert(err.message);
    }
    setLoading(false);
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const saveSelection = async () => {
    if (selected.size === 0) return;
    try {
      await api.selectRoles(Array.from(selected));
      setSaved(true);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <ProtectedRoute>
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Career Recommendations</h1>
          <button
            onClick={fetchRecommendations}
            disabled={loading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Analyzing..." : "Get AI Recommendations"}
          </button>
        </div>

        <p className="mt-2 text-sm text-gray-600">
          Upload your resume first, then get AI-powered role suggestions based on your skills.
        </p>

        {recommendations.length > 0 && (
          <div className="mt-6 space-y-3">
            {recommendations.map((rec) => (
              <div
                key={rec.id}
                onClick={() => toggleSelect(rec.id)}
                className={`bg-white rounded-xl border p-5 cursor-pointer transition ${
                  selected.has(rec.id)
                    ? "border-indigo-500 ring-2 ring-indigo-200"
                    : "border-gray-200 hover:border-indigo-300"
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900">{rec.job_role}</h3>
                    {rec.matched_skills?.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {rec.matched_skills.map((s: string) => (
                          <span key={s} className="px-2 py-0.5 bg-green-50 text-green-700 rounded text-xs">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                    {rec.missing_skills?.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {rec.missing_skills.map((s: string) => (
                          <span key={s} className="px-2 py-0.5 bg-orange-50 text-orange-600 rounded text-xs">
                            +{s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${rec.match_score >= 70 ? "text-green-600" : rec.match_score >= 40 ? "text-yellow-600" : "text-gray-400"}`}>
                      {rec.match_score}%
                    </div>
                    <div className="text-xs text-gray-500">match</div>
                  </div>
                </div>
              </div>
            ))}

            <div className="flex justify-between items-center pt-4">
              <p className="text-sm text-gray-500">{selected.size} role(s) selected</p>
              <button
                onClick={saveSelection}
                disabled={selected.size === 0}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
              >
                {saved ? "Saved!" : "Select These Roles"}
              </button>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
