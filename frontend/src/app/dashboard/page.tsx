"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";
import Link from "next/link";

export default function DashboardPage() {
  const { user, refresh } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [onboarding, setOnboarding] = useState({
    degree: "",
    location_preference: "",
    remote_preference: "hybrid",
    salary_expectation: "",
  });
  const [saving, setSaving] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    api.getProfile().then(setProfile).catch(() => {});
  }, []);

  useEffect(() => {
    if (user) {
      setOnboarding({
        degree: user.degree || "",
        location_preference: user.location_preference || "",
        remote_preference: user.remote_preference || "hybrid",
        salary_expectation: user.salary_expectation || "",
      });
    }
  }, [user]);

  const saveOnboarding = async () => {
    setSaving(true);
    try {
      await api.onboard(onboarding);
      await refresh();
    } catch {}
    setSaving(false);
  };

  const runPipeline = async () => {
    if (!file) return;
    setPipelineLoading(true);
    try {
      const result = await api.runPipeline(file);
      setPipelineResult(result);
      await refresh();
    } catch (err: any) {
      alert(err.message);
    }
    setPipelineLoading(false);
  };

  const needsOnboarding = !user?.degree;

  return (
    <ProtectedRoute>
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome, {user?.full_name}
        </h1>

        {needsOnboarding && (
          <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Complete Your Profile</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Degree</label>
                <input
                  value={onboarding.degree}
                  onChange={(e) => setOnboarding({ ...onboarding, degree: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                  placeholder="B.Tech CSE"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  value={onboarding.location_preference}
                  onChange={(e) => setOnboarding({ ...onboarding, location_preference: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                  placeholder="Bangalore"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Work Mode</label>
                <select
                  value={onboarding.remote_preference}
                  onChange={(e) => setOnboarding({ ...onboarding, remote_preference: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                >
                  <option value="remote">Remote</option>
                  <option value="onsite">Onsite</option>
                  <option value="hybrid">Hybrid</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Salary Expectation</label>
                <input
                  value={onboarding.salary_expectation}
                  onChange={(e) => setOnboarding({ ...onboarding, salary_expectation: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                  placeholder="5-8 LPA"
                />
              </div>
            </div>
            <button
              onClick={saveOnboarding}
              disabled={saving}
              className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Preferences"}
            </button>
          </div>
        )}

        {/* Quick Pipeline */}
        <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-2">Quick Start Pipeline</h2>
          <p className="text-sm text-gray-600 mb-4">
            Upload your resume and get career recommendations, job matches, and ATS score — all at once.
          </p>
          <div className="flex items-center gap-4">
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="text-sm"
            />
            <button
              onClick={runPipeline}
              disabled={!file || pipelineLoading}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              {pipelineLoading ? "Processing..." : "Run AI Pipeline"}
            </button>
          </div>
        </div>

        {pipelineResult && (
          <div className="mt-6 space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <h3 className="font-semibold text-green-800">Pipeline Complete</h3>
              <p className="text-sm text-green-700 mt-1">
                Found {pipelineResult.skills_extracted?.length || 0} skills |
                ATS Score: {pipelineResult.ats_score?.score || "N/A"}/100 |
                {pipelineResult.matched_jobs?.length || 0} jobs matched
              </p>
            </div>

            {pipelineResult.career_recommendations?.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="font-semibold mb-3">Recommended Roles</h3>
                <div className="space-y-2">
                  {pipelineResult.career_recommendations.map((r: any, i: number) => (
                    <div key={i} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                      <span className="font-medium">{r.job_role}</span>
                      <span className="text-sm text-indigo-600 font-semibold">{r.match_score}% match</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Quick links */}
        <div className="mt-8 grid md:grid-cols-4 gap-4">
          {[
            { href: "/resume", label: "Resume & ATS", desc: "Upload, parse, score" },
            { href: "/career", label: "Career Match", desc: "Role recommendations" },
            { href: "/jobs", label: "Job Search", desc: "Find & track jobs" },
            { href: "/roadmap", label: "Daily Roadmap", desc: "Action plan & progress" },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:border-indigo-300 hover:shadow-sm transition"
            >
              <h3 className="font-semibold text-gray-900">{item.label}</h3>
              <p className="text-sm text-gray-500 mt-1">{item.desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </ProtectedRoute>
  );
}
