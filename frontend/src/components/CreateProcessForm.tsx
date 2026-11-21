import { type FormEvent, useState } from "react";
import { PII_TYPES, type CreateProcessInput, type PiiType } from "../api/types";

interface Props {
  onSubmit: (input: CreateProcessInput) => Promise<void>;
}

export function CreateProcessForm({ onSubmit }: Props) {
  const [tenantId, setTenantId] = useState("");
  const [key, setKey] = useState("");
  const [type, setType] = useState<PiiType>("email");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({ tenant_id: tenantId.trim(), key: key.trim(), type });
      setKey("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not create the process");
    } finally {
      setSubmitting(false);
    }
  }

  const input = "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm";
  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg bg-white p-4 shadow-sm">
      <h2 className="font-semibold">New forget request</h2>
      <label className="block text-sm">
        Tenant ID
        <input className={input} value={tenantId} onChange={(e) => setTenantId(e.target.value)} required />
      </label>
      <label className="block text-sm">
        Type
        <select className={input} value={type} onChange={(e) => setType(e.target.value as PiiType)}>
          {PII_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        Key
        <input className={input} value={key} onChange={(e) => setKey(e.target.value)} required />
      </label>
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Sending…" : "Forget"}
      </button>
    </form>
  );
}
