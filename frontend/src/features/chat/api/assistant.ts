import type { AssistantQueryResponse } from "../types/assistant";

const apiBaseUrl = process.env
  .NEXT_PUBLIC_API_BASE_URL!.trim()
  .replace(/\/$/, "");

export async function askAssistant(
  question: string,
  options: { signal?: AbortSignal } = {},
): Promise<AssistantQueryResponse> {
  const response = await fetch(`${apiBaseUrl}/assistant/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Could not get an answer"));
  }

  return response.json() as Promise<AssistantQueryResponse>;
}

async function getErrorMessage(response: Response, fallback: string) {
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
