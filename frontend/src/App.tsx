import { useEffect, useState } from "react";
import { fetchHealth, type HealthStatus } from "./lib/api";

const SECTIONS = ["Dashboard", "Orders", "Inventory", "Procurement"] as const;

export default function App() {
  const [active, setActive] = useState<(typeof SECTIONS)[number]>("Dashboard");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchHealth(controller.signal)
      .then(setHealth)
      .catch((error: unknown) => {
        if (error instanceof Error && error.name !== "AbortError") {
          setHealthError(error.message);
        }
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <h1 className="text-xl font-semibold tracking-tight">depotledger</h1>
          <p className="text-sm text-zinc-500" role="status">
            {health
              ? `API ${health.status} · DB ${health.database}`
              : (healthError ?? "Connecting to API…")}
          </p>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 px-6 pb-3">
          {SECTIONS.map((section) => (
            <button
              key={section}
              type="button"
              onClick={() => setActive(section)}
              aria-pressed={active === section}
              className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                active === section
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              {section}
            </button>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <h2 className="text-lg font-medium">{active}</h2>
        <p className="mt-2 text-sm text-zinc-600">
          {active} workflows land here in M10. Domain screens follow the backend
          milestones — catalogue and warehouses first.
        </p>
      </main>
    </div>
  );
}
