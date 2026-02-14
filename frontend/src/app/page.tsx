"use client";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <nav className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-indigo-600">Job Dhundo</h1>
        <div className="flex gap-3">
          <Link
            href="/login"
            className="px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Get Started
          </Link>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 pt-20 pb-32 text-center">
        <h2 className="text-5xl font-extrabold tracking-tight text-gray-900 sm:text-6xl">
          Find Your Dream Job
          <span className="block text-indigo-600 mt-2">Powered by AI</span>
        </h2>
        <p className="mt-6 text-xl text-gray-600 max-w-2xl mx-auto">
          Upload your resume, get AI-powered career recommendations, ATS scoring,
          job matching, and a daily application roadmap — all in one place.
        </p>
        <div className="mt-10 flex gap-4 justify-center">
          <Link
            href="/register"
            className="px-8 py-3 bg-indigo-600 text-white rounded-lg text-lg font-semibold hover:bg-indigo-700 transition shadow-lg shadow-indigo-200"
          >
            Start Free
          </Link>
          <Link
            href="/login"
            className="px-8 py-3 bg-white text-indigo-600 rounded-lg text-lg font-semibold border border-indigo-200 hover:bg-indigo-50 transition"
          >
            Login
          </Link>
        </div>

        <div className="mt-24 grid md:grid-cols-3 gap-8 text-left">
          {[
            {
              title: "Smart Resume Parser",
              desc: "AI extracts your skills, experience, and education from your PDF resume automatically.",
            },
            {
              title: "Career Recommendations",
              desc: "Get top 5 job roles that match your skills with market-aware AI reasoning.",
            },
            {
              title: "ATS Score (0-100)",
              desc: "Know exactly how your resume performs against ATS systems with actionable tips.",
            },
            {
              title: "Job Matching",
              desc: "Fresher-friendly jobs ranked by skill match, location, and experience fit.",
            },
            {
              title: "Daily Roadmap",
              desc: "Structured daily action plan: apply, network, connect — track your progress.",
            },
            {
              title: "Referral Messages",
              desc: "AI-generated personalized cold outreach messages for LinkedIn.",
            },
          ].map((f) => (
            <div key={f.title} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-lg text-gray-900">{f.title}</h3>
              <p className="mt-2 text-sm text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
