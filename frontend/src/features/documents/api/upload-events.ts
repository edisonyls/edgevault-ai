import { apiBaseUrl } from "@/lib/api";

export type UploadStatusEvent = {
  id: string;
  status: string;
};

// Open a Server-Sent Events stream of upload status changes. The caller gets a
// callback per event and a function to close the stream. The browser's
// EventSource reconnects automatically, so transient drops self-heal.
export function subscribeToUploadEvents(
  onEvent: (event: UploadStatusEvent) => void,
): () => void {
  const source = new EventSource(`${apiBaseUrl}/uploads/events`, {
    withCredentials: true,
  });

  const handler = (message: MessageEvent<string>) => {
    try {
      onEvent(JSON.parse(message.data) as UploadStatusEvent);
    } catch {
      // Ignore malformed payloads; the next full refresh will reconcile.
    }
  };

  source.addEventListener("upload-status", handler);

  return () => {
    source.removeEventListener("upload-status", handler);
    source.close();
  };
}
