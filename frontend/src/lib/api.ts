export const apiBaseUrl = process.env
  .NEXT_PUBLIC_API_BASE_URL!.trim()
  .replace(/\/$/, "");

export function apiFetch(path: string, init: RequestInit = {}) {
  return fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: "include",
  }).then((response) => {
    if (response.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new Event("edgevault:unauthorized"));
    }
    return response;
  });
}

export async function getApiErrorMessage(
  response: Response,
  fallback: string,
) {
  try {
    const payload = (await response.json()) as { detail?: unknown };

    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall through to the generic status message.
  }

  return `${fallback} with status ${response.status}.`;
}
