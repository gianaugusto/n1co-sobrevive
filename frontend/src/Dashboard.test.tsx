import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ApiClient } from "./api/client";
import { Dashboard } from "./Dashboard";
import { process, subscriber } from "./test/factories";

function fakeApi(overrides: Partial<ApiClient> = {}): ApiClient {
  return {
    listProcesses: vi.fn().mockResolvedValue([]),
    createProcess: vi.fn().mockResolvedValue(process()),
    retrySubscriber: vi.fn().mockResolvedValue(process()),
    ...overrides,
  };
}

describe("Dashboard", () => {
  it("lists processes with id, key, type, timestamp and status", async () => {
    const api = fakeApi({
      listProcesses: vi.fn().mockResolvedValue([process({ status: "IN_PROGRESS" })]),
    });
    render(<Dashboard api={api} />);

    expect(await screen.findByText("11111111-1111-1111-1111-111111111111")).toBeInTheDocument();
    expect(screen.getByText("jane@example.com")).toBeInTheDocument();
    expect(screen.getByText("IN PROGRESS")).toBeInTheDocument();
  });

  it("shows the empty state", async () => {
    render(<Dashboard api={fakeApi()} />);
    expect(await screen.findByText("No forget requests yet.")).toBeInTheDocument();
  });

  it("creates a process and reloads the list", async () => {
    const api = fakeApi();
    render(<Dashboard api={api} />);

    await userEvent.type(screen.getByLabelText("Tenant ID"), "acme");
    await userEvent.type(screen.getByLabelText("Key"), "jane@example.com");
    await userEvent.click(screen.getByRole("button", { name: "Forget" }));

    expect(api.createProcess).toHaveBeenCalledWith({
      tenant_id: "acme",
      key: "jane@example.com",
      type: "email",
    });
    expect(api.listProcesses).toHaveBeenCalledTimes(2);
  });

  it("expands a process, retries a failed subscriber and refreshes", async () => {
    const failing = process({
      status: "FAILED",
      subscribers: [subscriber({ name: "crm", status: "FAILED" })],
    });
    const api = fakeApi({ listProcesses: vi.fn().mockResolvedValue([failing]) });
    render(<Dashboard api={api} />);

    await userEvent.click(await screen.findByText(failing.id));
    await userEvent.click(screen.getByRole("button", { name: "Retry crm" }));

    expect(api.retrySubscriber).toHaveBeenCalledWith(failing.id, "crm");
  });

  it("shows an error banner when loading fails", async () => {
    const api = fakeApi({ listProcesses: vi.fn().mockRejectedValue(new Error("Request failed (500)")) });
    render(<Dashboard api={api} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Request failed (500)");
  });
});
