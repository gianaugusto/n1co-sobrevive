import type { SubscriberProgress } from "../api/types";
import { StatusBadge } from "./StatusBadge";

interface Props {
  subscribers: SubscriberProgress[];
  onRetry: (subscriber: string) => Promise<void>;
}

export function SubscriberList({ subscribers, onRetry }: Props) {
  if (subscribers.length === 0) {
    return <p className="text-sm text-slate-500">No subscriber has started processing yet.</p>;
  }
  return (
    <ul className="space-y-3">
      {subscribers.map((subscriber) => (
        <li key={subscriber.name} className="rounded border border-slate-200 bg-white p-3">
          <div className="flex items-center justify-between gap-2">
            <div>
              <span className="font-medium">{subscriber.name}</span>{" "}
              <StatusBadge status={subscriber.status} />
              <p className="text-xs text-slate-500">
                Started {new Date(subscriber.started_at).toLocaleString()} · attempt {subscriber.attempt}
              </p>
            </div>
            {subscriber.status === "FAILED" && (
              <button
                onClick={() => void onRetry(subscriber.name)}
                className="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-100"
              >
                Retry {subscriber.name}
              </button>
            )}
          </div>
          <ol className="mt-2 space-y-1 text-xs text-slate-600">
            {subscriber.results.map((result, index) => (
              <li key={index}>
                {new Date(result.occurred_at).toLocaleString()} · <StatusBadge status={result.event} />
                {result.detail ? ` ${result.detail}` : ""}
              </li>
            ))}
          </ol>
        </li>
      ))}
    </ul>
  );
}
