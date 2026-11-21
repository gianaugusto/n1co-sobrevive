import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { subscriber } from "../test/factories";
import { SubscriberList } from "./SubscriberList";

describe("SubscriberList", () => {
  it("explains when nobody has started yet", () => {
    render(<SubscriberList subscribers={[]} onRetry={vi.fn()} />);
    expect(screen.getByText(/No subscriber has started/)).toBeInTheDocument();
  });

  it("shows the history of returns with details", () => {
    const failed = subscriber({
      status: "FAILED",
      results: [
        { event: "STARTED", detail: null, occurred_at: "2026-01-01T12:00:00Z" },
        { event: "FAILED", detail: "timeout", occurred_at: "2026-01-01T12:05:00Z" },
      ],
    });
    render(<SubscriberList subscribers={[failed]} onRetry={vi.fn()} />);

    expect(screen.getByText(/timeout/)).toBeInTheDocument();
    expect(screen.getAllByText("FAILED")).toHaveLength(2); // subscriber badge + history entry
  });

  it("offers retry only for failed subscribers", async () => {
    const onRetry = vi.fn().mockResolvedValue(undefined);
    render(
      <SubscriberList
        subscribers={[
          subscriber({ name: "crm", status: "FAILED" }),
          subscriber({ name: "billing", status: "SUCCEEDED" }),
        ]}
        onRetry={onRetry}
      />,
    );

    expect(screen.queryByRole("button", { name: "Retry billing" })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry crm" }));
    expect(onRetry).toHaveBeenCalledWith("crm");
  });
});
