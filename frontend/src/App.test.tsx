import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the depotledger shell with section navigation", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "depotledger" })).toBeInTheDocument();
    for (const section of ["Dashboard", "Orders", "Inventory", "Procurement"]) {
      expect(screen.getByRole("button", { name: section })).toBeInTheDocument();
    }
  });
});
