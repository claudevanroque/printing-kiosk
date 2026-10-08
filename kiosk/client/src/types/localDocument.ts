export interface HealthResponse {
    status: string;
    database: string;
}



export type DocumentSource =
    | "QR"
    | "USB";


export interface LocalDocument {
    id: string;

    original_filename: string;

    content_type: string;
    extension: string;

    file_size: number;
    page_count: number;

    source: DocumentSource;

    created_at: string;

    preview_url: string;
}


export type UploadSessionStatus =
    | "WAITING"
    | "UPLOADING"
    | "READY"
    | "FAILED"
    | "EXPIRED"
    | "CONSUMED";


export interface UploadSession {
    id: string;

    status: UploadSessionStatus;

    upload_url: string;

    created_at: string;
    expires_at: string;

    document:
        LocalDocument | null;
}


export interface HotspotResponse {
    enabled?: boolean;

    mode: string;

    ssid?: string;
    password?: string;

    message?: string;
}