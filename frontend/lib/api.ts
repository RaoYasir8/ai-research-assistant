function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.split("; ").find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=").slice(1).join("=")) : null;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request(path: string, init: RequestInit, allowRefresh: boolean): Promise<Response> {
  const method = (init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrf = getCookie("csrf_token");
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }
  const response = await fetch(`/api/backend${path}`, {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  if (response.status === 401 && allowRefresh && !path.startsWith("/api/v1/auth/")) {
    const csrf = getCookie("csrf_token");
    if (csrf) {
      const refreshed = await fetch("/api/backend/api/v1/auth/refresh", {
        method: "POST",
        headers: {"X-CSRF-Token": csrf},
        credentials: "include",
        cache: "no-store",
      });
      if (refreshed.ok) return request(path, init, false);
    }
  }
  return response;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await request(path, init, true);
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof body === "object" && body && "detail" in body ? body.detail : body;
    throw new ApiError(response.status, typeof detail === "string" ? detail : "Request failed");
  }
  return body as T;
}
