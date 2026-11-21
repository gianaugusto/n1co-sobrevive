import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CreateProcessForm } from "./CreateProcessForm";

describe("CreateProcessForm", () => {
  it("submits trimmed values with the selected type", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<CreateProcessForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText("Tenant ID"), " acme ");
    await userEvent.selectOptions(screen.getByLabelText("Type"), "username");
    await userEvent.type(screen.getByLabelText("Key"), "jane ");
    await userEvent.click(screen.getByRole("button", { name: "Forget" }));

    expect(onSubmit).toHaveBeenCalledWith({ tenant_id: "acme", key: "jane", type: "username" });
  });

  it("offers every PII type", () => {
    render(<CreateProcessForm onSubmit={vi.fn()} />);
    const options = screen.getAllByRole("option").map((o) => o.textContent);
    expect(options).toEqual(["email", "username"]);
  });

  it("shows the error and keeps the key when the request fails", async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error("Service unavailable"));
    render(<CreateProcessForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText("Tenant ID"), "acme");
    await userEvent.type(screen.getByLabelText("Key"), "jane");
    await userEvent.click(screen.getByRole("button", { name: "Forget" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Service unavailable");
    expect(screen.getByLabelText("Key")).toHaveValue("jane");
  });
});
