import type { CreateProcessInput, ForgetProcess } from "./types";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface ApiClient {
  listProcesses(): Promise<ForgetProcess[]>;
  createProcess(input: CreateProcessInput): Promise<ForgetProcess>;
  retrySubscriber(processId: string, subscriber: string): Promise<ForgetProcess>;
}

type TokenProvider = () => Promise<string>;

export function createApiClient(
  getToken: TokenProvider,
  baseUrl: string,
  fetchImpl: typeof fetch = (...args) => fetch(...args),
): ApiClient {
  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetchImpl(`${baseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${await getToken()}`,
      },
    });
    if (!response.ok) {
      throw new ApiError(response.status, await errorMessage(response));
    }
    return (await response.json()) as T;
  }

  return {
    listProcesses: () => request<ForgetProcess[]>("/api/v1/processes?limit=100"),
    createProcess: (input) =>
      request<ForgetProcess>("/api/v1/processes", { method: "POST", body: JSON.stringify(input) }),
    retrySubscriber: (processId, subscriber) =>
      request<ForgetProcess>(
        `/api/v1/processes/${encodeURIComponent(processId)}/subscribers/${encodeURIComponent(subscriber)}/retry`,
        { method: "POST" },
      ),
  };
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // fall through to the generic message
  }
  return `Request failed (${response.status})`;
}
