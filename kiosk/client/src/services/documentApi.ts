import localApi from "./localApi";

import type {
  HotspotResponse,
  LocalDocument,
  UploadSession,
} from "../types/localDocument";

export async function checkLocalAgent() {
  const response = await localApi.get("/health");
  return response.data;
}

export async function startHotspot(): Promise<HotspotResponse> {
  const response = await localApi.post("/hotspot/start");

  return response.data;
}

export async function stopHotspot(): Promise<HotspotResponse> {
  const response = await localApi.post("/hotspot/stop");

  return response.data;
}

export async function createUploadSession(): Promise<UploadSession> {
  const response = await localApi.post("/upload-sessions");

  return response.data;
}

export async function getUploadSession(sessionId: string,): Promise<UploadSession> {
  const response = await localApi.get(`/upload-sessions/${sessionId}`);

  return response.data;
}

export async function uploadUSBFile(file: File): Promise<LocalDocument> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await localApi.post("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}

export async function removeDocument(documentId: string): Promise<void> {
  await localApi.delete(`/documents/${documentId}`);
}

export function getDocumentPreviewUrl(documentId: string): string {
  const baseUrl =
    import.meta.env.VITE_LOCAL_API_URL ?? "http://127.0.0.1:9001/api";

  return `${baseUrl}/documents/` + `${documentId}/file`;
}
