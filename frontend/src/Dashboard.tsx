import { useState } from "react";
import type { ApiClient } from "./api/client";
import { CreateProcessForm } from "./components/CreateProcessForm";
import { ProcessList } from "./components/ProcessList";
import { useProcesses } from "./hooks";

export function Dashboard({ api }: { api: ApiClient }) {
  const { processes, error, create, retry } = useProcesses(api);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div className="grid gap-6 lg:grid-cols-[20rem_1fr]">
      <CreateProcessForm onSubmit={create} />
      <section className="space-y-3">
        {error && (
          <p role="alert" className="rounded bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}
        <ProcessList
          processes={processes}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onRetry={retry}
        />
      </section>
    </div>
  );
}
