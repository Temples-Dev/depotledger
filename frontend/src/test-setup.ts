import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Explicit vitest imports disable RTL's auto-cleanup; restore it manually.
afterEach(() => {
  cleanup();
});
