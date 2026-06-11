const DEFAULT_API_BASE_URL = "http://localhost:8000/api";

const configuredApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "") ?? "";
const apiBaseUrl =
  configuredApiBaseUrl.length > 0 ? configuredApiBaseUrl : DEFAULT_API_BASE_URL;

export type UploadMetadataResponse = {
  id: string;
  original_filename: string;
  display_filename: string;
  stored_filename: string;
  file_path: string | null;
  mime_type: string;
  file_size: number;
  status: string;
  created_at: string;
  updated_at: string;
};

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
    throw new Error(await getUploadErrorMessage(response));
  }

  return response.json() as Promise<UploadMetadataResponse>;
}

async function getUploadErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: unknown };

    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall through to the generic status message.
  }

  return `Upload failed with status ${response.status}.`;
}
