import { useCallback, useEffect, useState } from "react";
import {
  type FinancialRecord,
  listFinancialRecords,
} from "../api/financial-records";
import {
  type UploadMetadataResponse,
  deleteUploadMetadata,
  listUploadMetadata,
  updateUploadMetadata,
  uploadDocumentFile,
} from "../api/uploads";
import { mapUploadToDocument } from "../lib/document-utils";
import type { VaultDocument } from "../types/document";

type UseDocuments = {
  documents: VaultDocument[];
  isLoading: boolean;
  error: string | null;
  isUploading: boolean;
  uploadError: string | null;
  pendingId: string | null;
  clearError: () => void;
  reload: () => Promise<void>;
  uploadFiles: (files: File[]) => Promise<void>;
  renameDocument: (id: string, name: string) => Promise<boolean>;
  deleteDocument: (id: string) => Promise<boolean>;
};

// Pull uploads and their structured records together so the list can show the
// extracted vendor and amount.
async function loadVaultDocuments(
  signal?: AbortSignal,
): Promise<VaultDocument[]> {
  const [uploads, records] = await Promise.all([
    listUploadMetadata({ signal }),
    listFinancialRecords({ signal }).catch(() => [] as FinancialRecord[]),
  ]);

  const recordsByUpload = new Map(
    records.map((record) => [record.upload_id, record]),
  );

  return uploads.map((upload: UploadMetadataResponse) =>
    mapUploadToDocument(upload, recordsByUpload.get(upload.id) ?? null),
  );
}

// How often to re-poll the uploads list while any document is still being processed
// Set to 2.5s
const PROCESSING_POLL_INTERVAL_MS = 2500;

export function useDocuments(): UseDocuments {
  const [documents, setDocuments] = useState<VaultDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadDocuments() {
      setIsLoading(true);
      setError(null);

      try {
        setDocuments(await loadVaultDocuments(controller.signal));
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }

        setError(getErrorMessage(caught, "Could not load uploads."));
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadDocuments();

    return () => controller.abort();
  }, []);

  // used by the polling loop to reflect status/text changes once background OCR
  // completes.
  const refresh = useCallback(async (signal?: AbortSignal) => {
    try {
      setDocuments(await loadVaultDocuments(signal));
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        return;
      }
    }
  }, []);

  const hasProcessing = documents.some(
    (document) => document.status === "Processing",
  );

  useEffect(() => {
    if (!hasProcessing) {
      return;
    }

    const controller = new AbortController();
    const interval = setInterval(() => {
      void refresh(controller.signal);
    }, PROCESSING_POLL_INTERVAL_MS);

    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [hasProcessing, refresh]);

  const clearError = useCallback(() => setError(null), []);

  const uploadFiles = useCallback(async (files: File[]) => {
    if (files.length === 0) {
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setError(null);

    const results = await Promise.allSettled(files.map(uploadDocumentFile));
    const uploaded: VaultDocument[] = [];
    const failedNames: string[] = [];

    results.forEach((result, index) => {
      if (result.status === "fulfilled") {
        uploaded.push(mapUploadToDocument(result.value));
        return;
      }

      failedNames.push(files[index].name);
    });

    if (uploaded.length > 0) {
      setDocuments((current) => [...uploaded, ...current]);
    }

    if (failedNames.length > 0) {
      setUploadError(
        `Could not upload ${failedNames.join(", ")}. Check the backend and try again.`,
      );
    }

    setIsUploading(false);
  }, []);

  const renameDocument = useCallback(async (id: string, name: string) => {
    setPendingId(id);
    setError(null);

    try {
      const updated = await updateUploadMetadata(id, {
        display_filename: name,
      });
      setDocuments((current) =>
        current.map((document) =>
          document.id === id ? mapUploadToDocument(updated) : document,
        ),
      );
      return true;
    } catch (caught) {
      setError(getErrorMessage(caught, "Could not rename document."));
      return false;
    } finally {
      setPendingId(null);
    }
  }, []);

  const deleteDocument = useCallback(async (id: string) => {
    setPendingId(id);
    setError(null);

    try {
      await deleteUploadMetadata(id);
      setDocuments((current) =>
        current.filter((document) => document.id !== id),
      );
      return true;
    } catch (caught) {
      setError(getErrorMessage(caught, "Could not delete document."));
      return false;
    } finally {
      setPendingId(null);
    }
  }, []);

  return {
    documents,
    isLoading,
    error,
    isUploading,
    uploadError,
    pendingId,
    clearError,
    reload: refresh,
    uploadFiles,
    renameDocument,
    deleteDocument,
  };
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
}
