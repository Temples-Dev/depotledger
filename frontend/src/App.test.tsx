import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const SECTIONS = ["Dashboard", "Orders", "Inventory", "Procurement"];

function mockHealth(body: unknown, ok = true) {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(body), {
      status: ok ? 200 : 500,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("renders the depotledger shell with tab navigation", () => {
    mockHealth({ status: "ok", database: "connected" });
    render(<App />);
    expect(screen.getByRole("heading", { name: "depotledger" })).toBeInTheDocument();
    const tabs = screen.getAllByRole("tab");
    expect(tabs.map((tab) => tab.textContent)).toEqual(SECTIONS);
    expect(screen.getByRole("tab", { name: "Dashboard" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("switches section content when a tab is selected", async () => {
    const user = userEvent.setup();
    mockHealth({ status: "ok", database: "connected" });
    render(<App />);
    await user.click(screen.getByRole("tab", { name: "Inventory" }));
    expect(screen.getByRole("tab", { name: "Inventory" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText(/movement history/i)).toBeInTheDocument();
  });

  it("shows API and database status when the health check succeeds", async () => {
    mockHealth({ status: "ok", database: "connected" });
    render(<App />);
    expect(await screen.findByText("API ok · DB connected")).toBeInTheDocument();
  });

  it("shows the failure message when the health check fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network down"));
    render(<App />);
    expect(await screen.findByText("Network down")).toBeInTheDocument();
  });
});
