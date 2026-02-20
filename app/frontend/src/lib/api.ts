/**
 * Shared fetch wrapper that adds credentials and CSRF header to all API calls.
 */
export function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, {
    ...init,
    credentials: "include",
    headers: {
      "X-CSRF": "1",
      ...(init?.headers as Record<string, string>),
    },
  });
}
