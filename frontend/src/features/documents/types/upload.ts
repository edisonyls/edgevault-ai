export type UploadStatus =
  | "uploaded"
  | "processing"
  | "indexing"
  | "processed"
  | "failed";

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
  status?: UploadStatus;
  text?: string | null;
};
