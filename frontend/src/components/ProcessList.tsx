import type { ForgetProcess } from "../api/types";
import { StatusBadge } from "./StatusBadge";
import { SubscriberList } from "./SubscriberList";

interface Props {
  processes: ForgetProcess[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onRetry: (processId: string, subscriber: string) => Promise<void>;
}

export function ProcessList({ processes, selectedId, onSelect, onRetry }: Props) {
  if (processes.length === 0) {
    return <p className="text-sm text-slate-500">No forget requests yet.</p>;
  }
  return (
    <div className="overflow-x-auto rounded-lg bg-white shadow-sm">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
          <tr>
            <th className="p-3">Process</th>
            <th className="p-3">Key</th>
            <th className="p-3">Type</th>
            <th className="p-3">Requested</th>
            <th className="p-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {processes.map((process) => {
            const open = process.id === selectedId;
            return (
              <tr key={process.id} className="border-b border-slate-100 align-top">
                <td className="p-3">
                  <button
                    className="font-mono text-xs underline"
                    aria-expanded={open}
                    onClick={() => onSelect(open ? null : process.id)}
                  >
                    {process.id}
                  </button>
                  {open && (
                    <div className="mt-3">
                      <SubscriberList
                        subscribers={process.subscribers}
                        onRetry={(name) => onRetry(process.id, name)}
                      />
                    </div>
                  )}
                </td>
                <td className="p-3">{process.key}</td>
                <td className="p-3">{process.type}</td>
                <td className="p-3">{new Date(process.requested_at).toLocaleString()}</td>
                <td className="p-3">
                  <StatusBadge status={process.status} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
