import type { ForgetProcess, SubscriberProgress } from "../api/types";

export function subscriber(overrides: Partial<SubscriberProgress> = {}): SubscriberProgress {
  return {
    name: "billing",
    started_at: "2026-01-01T12:00:00Z",
    status: "IN_PROGRESS",
    attempt: 1,
    results: [{ event: "STARTED", detail: null, occurred_at: "2026-01-01T12:00:00Z" }],
    ...overrides,
  };
}

export function process(overrides: Partial<ForgetProcess> = {}): ForgetProcess {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    tenant_id: "acme",
    key: "jane@example.com",
    type: "email",
    status: "PENDING",
    requested_at: "2026-01-01T12:00:00Z",
    subscribers: [],
    ...overrides,
  };
}
