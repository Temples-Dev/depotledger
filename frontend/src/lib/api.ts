/** Typed client for the depotledger API. Base defaults to the dev proxy. */

const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "/api/v1";

export interface HealthStatus {
  status: "ok" | "degraded";
  database: "connected" | "unreachable";
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/health/`, { signal });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiError | null;
    throw new Error(body?.error.message ?? `Health check failed: ${response.status}`);
  }
  return (await response.json()) as HealthStatus;
}
