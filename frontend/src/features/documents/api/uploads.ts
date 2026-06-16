import type {
  UploadMetadataResponse,
  UploadMetadataUpdate,
} from "../types/upload";
import { apiFetch, getApiErrorMessage } from "@/lib/api";

export async function listUploadMetadata(
  options: { signal?: AbortSignal } = {},
): Promise<UploadMetadataResponse[]> {
  const response = await apiFetch("/uploads", {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Load failed"));
  }

  return response.json() as Promise<UploadMetadataResponse[]>;
}

export async function uploadDocumentFile(
  file: File,
): Promise<UploadMetadataResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiFetch("/uploads", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Upload failed"));
  }

  return response.json() as Promise<UploadMetadataResponse>;
}

export async function updateUploadMetadata(
  id: string,
  update: UploadMetadataUpdate,
): Promise<UploadMetadataResponse> {
  const response = await apiFetch(`/uploads/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Update failed"));
  }

  return response.json() as Promise<UploadMetadataResponse>;
}

export async function deleteUploadMetadata(id: string): Promise<void> {
  const response = await apiFetch(`/uploads/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Delete failed"));
  }
}
