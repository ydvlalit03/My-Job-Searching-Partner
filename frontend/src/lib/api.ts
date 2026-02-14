const BASE = "/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

export const api = {
  // Auth
  register: (data: { email: string; password: string; full_name: string }) =>
    request<{ access_token: string; user: any }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; user: any }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // User
  getMe: () => request<any>("/users/me"),
  onboard: (data: any) =>
    request<any>("/users/me/onboard", { method: "PATCH", body: JSON.stringify(data) }),

  // Resume
  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<any>("/resume/upload", { method: "POST", body: form });
  },
  getProfile: () => request<any>("/resume/profile"),
  getAtsScore: (role?: string) =>
    request<any>(`/resume/ats-score${role ? `?target_role=${encodeURIComponent(role)}` : ""}`, {
      method: "POST",
    }),

  // Career
  getRecommendations: () => request<any[]>("/career/recommend", { method: "POST" }),
  selectRoles: (roleIds: string[]) =>
    request<any>("/career/select-roles", {
      method: "POST",
      body: JSON.stringify({ role_ids: roleIds }),
    }),

  // Jobs
  searchJobs: (role?: string) =>
    request<any[]>(`/jobs/search${role ? `?role=${encodeURIComponent(role)}` : ""}`),
  saveJob: (index: number, role?: string) =>
    request<any>(`/jobs/save/${index}${role ? `?role=${encodeURIComponent(role)}` : ""}`, {
      method: "POST",
    }),
  getSavedJobs: () => request<any[]>("/jobs/saved"),
  updateJobStatus: (id: string, status: string) =>
    request<any>(`/jobs/saved/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  // Roadmap
  generateRoadmap: (days = 7) =>
    request<any[]>(`/roadmap/generate?days=${days}`, { method: "POST" }),
  getToday: () => request<any | null>("/roadmap/today"),
  updateProgress: (id: string, data: any) =>
    request<any>(`/roadmap/${id}/progress`, { method: "PATCH", body: JSON.stringify(data) }),
  getReferralMessage: (data: { job_role: string; company_name: string }) =>
    request<any>("/roadmap/referral-message", { method: "POST", body: JSON.stringify(data) }),

  // Pipeline
  runPipeline: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<any>("/pipeline/onboard", { method: "POST", body: form });
  },
};
