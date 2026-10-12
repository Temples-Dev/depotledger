import * as Tabs from "@radix-ui/react-tabs";
import { useEffect, useState } from "react";
import { fetchHealth, type HealthStatus } from "./lib/api";
import { cn } from "./lib/utils";

const SECTIONS = ["Dashboard", "Orders", "Inventory", "Procurement"] as const;
type Section = (typeof SECTIONS)[number];

const SECTION_COPY: Record<Section, string> = {
  Dashboard: "Operational summaries land here in M10, backed by reliable backend data.",
  Orders: "Sales order management lands here in M7: demand, allocation, and fulfilment progress.",
  Inventory: "Balances, movement history, and availability views land here in M4–M5.",
  Procurement: "Purchase orders and receiving screens land here in M6.",
};

export default function App() {
  const [active, setActive] = useState<Section>("Dashboard");
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
      </header>
      <Tabs.Root
        value={active}
        onValueChange={(value) => setActive(value as Section)}
        className="mx-auto max-w-6xl px-6 py-6"
      >
        <Tabs.List aria-label="Operational sections" className="flex gap-1">
          {SECTIONS.map((section) => (
            <Tabs.Trigger
              key={section}
              value={section}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100",
                "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-900",
                "data-[state=active]:bg-zinc-900 data-[state=active]:text-white",
              )}
            >
              {section}
            </Tabs.Trigger>
          ))}
        </Tabs.List>
        {SECTIONS.map((section) => (
          <Tabs.Content key={section} value={section} className="py-6">
            <h2 className="text-lg font-medium">{section}</h2>
            <p className="mt-2 text-sm text-zinc-600">{SECTION_COPY[section]}</p>
          </Tabs.Content>
        ))}
      </Tabs.Root>
    </div>
  );
}
