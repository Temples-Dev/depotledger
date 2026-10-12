import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "./button";

describe("Button", () => {
  it("renders the primary medium button by default", () => {
    render(<Button>Save</Button>);
    const button = screen.getByRole("button", { name: "Save" });
    expect(button.className).toContain("bg-zinc-900");
    expect(button.className).toContain("h-9");
  });

  it("applies the requested variant and size", () => {
    render(
      <Button variant="ghost" size="sm">
        Cancel
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Cancel" });
    expect(button.className).toContain("text-zinc-600");
    expect(button.className).toContain("h-8");
  });

  it("renders as its child element when asChild is set", () => {
    render(
      <Button asChild variant="outline">
        <a href="/orders">View orders</a>
      </Button>,
    );
    const link = screen.getByRole("link", { name: "View orders" });
    expect(link.className).toContain("bg-white");
  });
});
