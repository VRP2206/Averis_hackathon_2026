// Typed client for the SDOC API (sdoc/api.py). Base URL comes from VITE_API_URL.

export type Category = "BL_COMPARISON" | "SI_REQUEST" | "INVOICE_QUERY" | "GENERAL" | "SPAM";
export type Status = "OK" | "MISMATCH" | "NEEDS_REVIEW";
export type ReviewReason = "wrong_doc_type" | "missing_attachment" | "unreadable" | "missing_value";

export interface EmailSummary {
  email_id: string;
  from: string;
  subject: string;
  attachments: string[];
  result: { category: Category; status: Status; review_reason: ReviewReason | null; defect_fields: string[] };
}

export interface EmailRecord {
  email_id: string;
  from: string;
  subject: string;
  body: string;
  attachments: string[];
}

export interface ExtractedField {
  field: string;
  value: string | null;
  source: string | null;
  confidence: number;
  blank: boolean;
}

export interface Extraction {
  doc_path: string;
  doc_type: string;
  method: string;
  fields: Record<string, ExtractedField>;
}

export interface FieldComparison {
  field: string;
  si_value: string | null;
  bl_value: string | null;
  si_normalised: string | null;
  bl_normalised: string | null;
  match: boolean;
}

export interface EmailResult {
  email_id: string;
  category: Category;
  status: Status;
  review_reason: ReviewReason | null;
  has_defect: boolean;
  defect_fields: string[];
  decided_by: string;
  classification: { category: Category; decided_by: string; confidence: number; signals: string[] } | null;
  comparisons: FieldComparison[];
  extractions: Extraction[];
  notes: string[];
  draft_reply: string | null;
}

export interface Metrics {
  final_score: number;
  n_emails: number;
  stage1: { accuracy: number; macro_f1: number; per_category: Record<string, { f1: number }> };
  stage3: { defect_precision: number; defect_recall: number; defect_f1: number; exact_match_rate: number };
  reliability: { escalation_recall: number; escalation_precision: number; pred_review: number; gold_review: number };
  end_to_end: { success: number; total: number; rate: number };
}

export const API_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_URL + path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text.slice(0, 200)}` : ""}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ ok: boolean; llm_provider: string; results: number }>("/health"),
  emails: () => request<EmailSummary[]>("/emails"),
  email: (id: string) => request<EmailRecord>(`/emails/${id}`),
  result: (id: string) => request<EmailResult>(`/results/${id}`),
  results: () => request<EmailResult[]>("/results"),
  processAll: () => request<{ processed: number }>("/process", { method: "POST" }),
  processOne: (id: string) => request<EmailResult>(`/process/${id}`, { method: "POST" }),
  review: (id: string, body: { status: Status; defect_fields: string[]; reviewer: string }) =>
    request<EmailResult>(`/results/${id}/review`, { method: "PATCH", body: JSON.stringify(body) }),
  metrics: () => request<Metrics>("/metrics"),
};

export const FIELD_LABELS: Record<string, string> = {
  shipper: "Shipper",
  consignee: "Consignee",
  notify_party: "Notify party",
  port_of_loading: "Port of loading",
  port_of_discharge: "Port of discharge",
  container_count: "Container count",
  gross_weight_kg: "Gross weight (kg)",
};
export const FIELDS = Object.keys(FIELD_LABELS);

export const REASON_TEXT: Record<ReviewReason, string> = {
  wrong_doc_type: "The second attachment is not a Bill of Lading.",
  missing_attachment: "The SI and/or draft BL were not attached.",
  unreadable: "An attachment is empty, corrupt or an image-only scan.",
  missing_value: "A required field is blank or could not be found.",
};
