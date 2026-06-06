const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
export const WS_URL = (import.meta.env.VITE_WS_URL ?? "ws://localhost:8000") + "/ws/dashboard";

// ── Types ──────────────────────────────────────────────────────────────────

export interface ChatResponse {
  session_id: string;
  bot_reply: string;
  request_id: string | null;
  needs_clarification: boolean;
  clarification_questions: string[];
  status: "extracting" | "matching" | "outreach_started" | "clarification_needed" | "error";
}

export interface Donor {
  id: string;
  name: string;
  phone: string;
  blood_group: string;
  area: string;
  lat: number;
  lng: number;
  health_status: "available" | "unavailable";
  response_rate: number;
  total_donations: number;
  last_donation_date: string | null;
  created_at: string;
}

export interface DonorResponse {
  id: string;
  donor_id: string;
  wave_id: string;
  request_id: string;
  intent: "accepted" | "rejected" | "unavailable" | "no_response";
  response_text: string;
  responded_at: string;
}

export interface Wave {
  id: string;
  request_id: string;
  wave_number: number;
  donor_ids: string[];
  status: "pending" | "in_progress" | "completed";
  started_at: string;
  completed_at: string | null;
  responses: DonorResponse[];
}

export interface BloodRequest {
  id: string;
  chat_session_id: string;
  blood_group: string;
  units_needed: number;
  hospital_name: string;
  hospital_area: string;
  urgency_level: string;
  patient_name: string | null;
  status: "pending" | "in_progress" | "fulfilled" | "failed";
  confirmed_donors: number;
  created_at: string;
  waves: Wave[];
}

export interface DashboardStats {
  total_requests: number;
  fulfilled_requests: number;
  failed_requests: number;
  in_progress_requests: number;
  fulfillment_rate: number;
  total_donors: number;
  eligible_donors: number;
  total_waves: number;
  avg_waves_per_request: number;
  blood_group_breakdown: Record<string, number>;
}

// WebSocket event shapes
export interface WSEvent {
  event: "wave_started" | "donor_response" | "wave_completed" | "request_fulfilled" | "request_failed" | "status_update";
  request_id: string;
  wave_number: number | null;
  data: Record<string, unknown>;
}

// ── API functions ──────────────────────────────────────────────────────────

export async function postChat(sessionId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error(`Chat error ${res.status}`);
  return res.json();
}

export async function getDonors(params?: {
  blood_group?: string;
  area?: string;
  health_status?: string;
  limit?: number;
}): Promise<Donor[]> {
  const q = new URLSearchParams();
  if (params?.blood_group) q.set("blood_group", params.blood_group);
  if (params?.area) q.set("area", params.area);
  if (params?.health_status) q.set("health_status", params.health_status);
  q.set("limit", String(params?.limit ?? 100));
  const res = await fetch(`${API}/api/donors?${q}`);
  if (!res.ok) throw new Error(`Donors error ${res.status}`);
  return res.json();
}

export async function getRequests(): Promise<BloodRequest[]> {
  const res = await fetch(`${API}/api/requests`);
  if (!res.ok) throw new Error(`Requests error ${res.status}`);
  return res.json();
}

export async function getRequest(id: string): Promise<BloodRequest> {
  const res = await fetch(`${API}/api/requests/${id}`);
  if (!res.ok) throw new Error(`Request error ${res.status}`);
  return res.json();
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API}/api/dashboard/stats`);
  if (!res.ok) throw new Error(`Stats error ${res.status}`);
  return res.json();
}

// ── Session helpers ────────────────────────────────────────────────────────

export function getOrCreateSessionId(): string {
  const key = "lifedrop_session_id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}
