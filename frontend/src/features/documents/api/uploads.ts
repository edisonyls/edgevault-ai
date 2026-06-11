const DEFAULT_API_BASE_URL = "http://localhost:8000/api";

const configuredApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "") ?? "";
const apiBaseUrl =
  configuredApiBaseUrl.length > 0 ? configuredApiBaseUrl : DEFAULT_API_BASE_URL;

export type UploadStatus = "uploaded" | "processing" | "processed" | "failed";

export type UploadMetadataResponse = {
  id: string;
  text: string | null;
  original_filename: string;
  display_filename: string;
  stored_filename: string;
  file_path: string | null;
  mime_type: string;
  file_size: number;
  status: UploadStatus;
  created_at: string;
  updated_at: string;
};

export type UploadMetadataUpdate = {
  display_filename?: string;
  file_path?: string | null;
  status?: UploadStatus;
  text?: string | null;
};

export async function listUploadMetadata(
  options: { signal?: AbortSignal } = {},
): Promise<UploadMetadataResponse[]> {
  const response = await fetch(`${apiBaseUrl}/uploads`, {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getUploadErrorMessage(response, "Load failed"));
  }

  return response.json() as Promise<UploadMetadataResponse[]>;
}

export async function uploadDocumentFile(
  file: File,
): Promise<UploadMetadataResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiBaseUrl}/uploads`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getUploadErrorMessage(response, "Upload failed"));
  }

  return response.json() as Promise<UploadMetadataResponse>;
}

export async function updateUploadMetadata(
  id: string,
  update: UploadMetadataUpdate,
): Promise<UploadMetadataResponse> {
  const response = await fetch(`${apiBaseUrl}/uploads/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error(await getUploadErrorMessage(response, "Update failed"));
  }

  return response.json() as Promise<UploadMetadataResponse>;
}

export async function deleteUploadMetadata(id: string): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/uploads/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(await getUploadErrorMessage(response, "Delete failed"));
  }
}

async function getUploadErrorMessage(response: Response, fallback: string) {
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
