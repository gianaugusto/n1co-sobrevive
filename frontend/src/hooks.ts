import { useCallback, useEffect, useState } from "react";
import type { ApiClient } from "./api/client";
import type { CreateProcessInput, ForgetProcess } from "./api/types";

const POLL_INTERVAL_MS = 5000;

export function useProcesses(api: ApiClient) {
  const [processes, setProcesses] = useState<ForgetProcess[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setProcesses(await api.listProcesses());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load processes");
    }
  }, [api]);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [refresh]);

  const create = useCallback(
    async (input: CreateProcessInput) => {
      await api.createProcess(input);
      await refresh();
    },
    [api, refresh],
  );

  const retry = useCallback(
    async (processId: string, subscriber: string) => {
      try {
        await api.retrySubscriber(processId, subscriber);
        await refresh();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Retry failed");
      }
    },
    [api, refresh],
  );

  return { processes, error, create, retry };
}
