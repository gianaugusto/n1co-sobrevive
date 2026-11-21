// Mirrors the backend response models (docs/api.md).
export const PII_TYPES = ["email", "username"] as const;
export type PiiType = (typeof PII_TYPES)[number];

export type ProcessStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "FAILED";
export type SubscriberStatus = "IN_PROGRESS" | "SUCCEEDED" | "FAILED";
export type FeedbackEvent = "STARTED" | "SUCCEEDED" | "FAILED";

export interface SubscriberResult {
  event: FeedbackEvent;
  detail: string | null;
  occurred_at: string;
}

export interface SubscriberProgress {
  name: string;
  started_at: string;
  status: SubscriberStatus;
  attempt: number;
  results: SubscriberResult[];
}

export interface ForgetProcess {
  id: string;
  tenant_id: string;
  key: string;
  type: PiiType;
  status: ProcessStatus;
  requested_at: string;
  subscribers: SubscriberProgress[];
}

export interface CreateProcessInput {
  tenant_id: string;
  key: string;
  type: PiiType;
}
