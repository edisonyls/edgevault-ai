import type { AssistantQueryResponse } from "../types/assistant";
import { apiFetch, getApiErrorMessage } from "@/lib/api";

export async function askAssistant(
  question: string,
  options: { signal?: AbortSignal } = {},
): Promise<AssistantQueryResponse> {
  const response = await apiFetch("/assistant/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(
      await getApiErrorMessage(response, "Could not get an answer"),
    );
  }

  return response.json() as Promise<AssistantQueryResponse>;
}
