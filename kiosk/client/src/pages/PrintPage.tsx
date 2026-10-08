import { useEffect, useRef, useState } from "react";

import type { ChangeEvent } from "react";

import { useNavigate } from "react-router-dom";

import { isAxiosError } from "axios";

import { QRCodeSVG } from "qrcode.react";

import DocumentPreview from "../components/DocumentPreview";

import LoadingPanel from "../components/LoadingPanel";

import {
  checkLocalAgent,
  createUploadSession,
  getUploadSession,
  removeDocument,
  startHotspot,
  stopHotspot,
  uploadUSBFile,
} from "../services/documentApi";

import type {
  HotspotResponse,
  LocalDocument,
  UploadSession,
} from "../types/localDocument";

type UploadMethod = null | "QR" | "USB";

function getApiErrorDetail(error: unknown): string | undefined {
  if (
    !isAxiosError<{
      detail?: unknown;
    }>(error)
  ) {
    return undefined;
  }

  const detail = error.response?.data?.detail;

  return typeof detail === "string" ? detail : undefined;
}

export default function PrintPage() {
  const navigate = useNavigate();

  const [uploadMethod, setUploadMethod] = useState<UploadMethod>(null);

  const [agentStatus, setAgentStatus] = useState<
    "checking" | "ready" | "unavailable"
  >("checking");

  const [agentCheckId, setAgentCheckId] = useState(0);

  const [hotspot, setHotspot] = useState<HotspotResponse | null>(null);

  const [session, setSession] = useState<UploadSession | null>(null);

  const [document, setDocument] = useState<LocalDocument | null>(null);

  const [loading, setLoading] = useState(false);

  const [qrStep, setQrStep] = useState<"hotspot" | "session" | null>(null);

  const [error, setError] = useState<string | null>(null);

  const pollingRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function checkAgent() {
      setAgentStatus("checking");

      // Retry a few times so one slow or dropped request isn't fatal.
      for (let attempt = 0; attempt < 4; attempt++) {
        try {
          await checkLocalAgent();

          if (!cancelled) {
            setAgentStatus("ready");
          }

          return;
        } catch {
          if (cancelled) {
            return;
          }

          await new Promise((resolve) => window.setTimeout(resolve, 750));
        }
      }

      if (!cancelled) {
        setAgentStatus("unavailable");
      }
    }

    checkAgent();

    return () => {
      cancelled = true;

      if (pollingRef.current !== null) {
        window.clearInterval(pollingRef.current);
      }
    };
  }, [agentCheckId]);

  function stopPolling() {
    if (pollingRef.current !== null) {
      window.clearInterval(pollingRef.current);

      pollingRef.current = null;
    }
  }

  async function chooseQRUpload() {
    setError(null);
    setLoading(true);
    setQrStep("hotspot");

    try {
      // The upload URL depends on the hotspot address, so wait for it first.
      const hotspotResult = await startHotspot();

      setQrStep("session");

      let newSession: UploadSession;

      try {
        newSession = await createUploadSession();
      } catch (err) {
        await stopHotspot().catch(() => undefined);

        throw err;
      }

      setHotspot(hotspotResult);

      setSession(newSession);

      setUploadMethod("QR");

      pollingRef.current = window.setInterval(async () => {
        try {
          const updated = await getUploadSession(newSession.id);

          setSession(updated);

          if (updated.status === "READY" && updated.document) {
            stopPolling();

            setDocument(updated.document);

            await stopHotspot();
          }

          if (updated.status === "EXPIRED" || updated.status === "FAILED") {
            stopPolling();

            setError(
              updated.status === "EXPIRED"
                ? "Upload session expired."
                : "Document upload failed.",
            );
          }
        } catch (err) {
          console.error(err);
        }
      }, 2000);
    } catch (err: unknown) {
      setError(
        getApiErrorDetail(err) ??
          (err instanceof Error ? err.message : undefined) ??
          "Unable to start QR upload.",
      );
    } finally {
      setLoading(false);
      setQrStep(null);
    }
  }

  function chooseUSBUpload() {
    setError(null);

    setUploadMethod("USB");
  }

  async function handleUSBFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await uploadUSBFile(file);

      setDocument(result);
    } catch (err: unknown) {
      setError(getApiErrorDetail(err) ?? "Unable to upload document.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRemove() {
    if (!document) {
      return;
    }

    try {
      await removeDocument(document.id);
    } catch (err) {
      console.error(err);
    }

    setDocument(null);
    setSession(null);
    setUploadMethod(null);
    setHotspot(null);
    setError(null);
  }

  function handleContinue() {
    if (!document) {
      return;
    }

    /*
     * Phase 5 will replace this.
     *
     * We will pass the document ID
     * to the Print Job page.
     */

    console.log("Ready for Phase 5:", document);
  }

  function handleCancelQR() {
    stopPolling();

    setSession(null);
    setHotspot(null);
    setUploadMethod(null);

    void stopHotspot().catch((err) => console.error(err));
  }

  function handleBack() {
    // Hotspot is only up (or coming up) once the QR flow has started.
    if (uploadMethod === "QR" || qrStep) {
      handleCancelQR();
    }

    navigate("/");
  }

  if (agentStatus === "checking") {
    return (
      <main className="print-page">
        <LoadingPanel
          title="Connecting to the kiosk"
          description="Checking the local kiosk agent."
        />
      </main>
    );
  }

  if (agentStatus === "unavailable") {
    return (
      <main className="print-page">
        <button
          type="button"
          className="back-button"
          onClick={() => navigate("/")}
        >
          ← Back
        </button>

        <div className="kiosk-error">
          <h2>Local kiosk agent unavailable</h2>

          <p>Start the local FastAPI agent and try again.</p>

          <button
            type="button"
            className="secondary-button"
            onClick={() => setAgentCheckId((id) => id + 1)}
          >
            Retry
          </button>
        </div>
      </main>
    );
  }

  if (document) {
    return (
      <main className="print-page">
        <DocumentPreview
          document={document}
          onRemove={handleRemove}
          onContinue={handleContinue}
        />
      </main>
    );
  }

  return (
    <main className="print-page">
      <div className="print-header">
        <button
          type="button"
          className="back-button"
          onClick={handleBack}
        >
          ← Back
        </button>

        <h1>Print Document</h1>
      </div>

      {error && <div className="error-message">{error}</div>}

      {qrStep && (
        <LoadingPanel
          title={
            qrStep === "hotspot"
              ? "Starting kiosk Wi-Fi"
              : "Creating your upload link"
          }
          description={
            qrStep === "hotspot"
              ? "Turning on the Wi-Fi your phone will connect to."
              : "Preparing the QR code for your phone."
          }
          currentStep={qrStep === "hotspot" ? 0 : 1}
          totalSteps={2}
        />
      )}

      {!uploadMethod && !qrStep && (
        <section className="upload-section">
          <h2>How would you like to upload?</h2>

          <p className="subtitle">Choose how to send your document.</p>

          <div className="upload-options">
            <button
              type="button"
              className="service-card"
              onClick={chooseQRUpload}
              disabled={loading}
            >
              <div className="service-icon">📱</div>
              <h2>Upload via QR</h2>
              <p>Send a document from your phone.</p>
            </button>

            <button
              type="button"
              className="service-card"
              onClick={chooseUSBUpload}
              disabled={loading}
            >
              <div className="service-icon">💾</div>
              <h2>Upload via USB</h2>
              <p>Select a file from your USB drive.</p>
            </button>
          </div>
        </section>
      )}

      {uploadMethod === "USB" && (
        <section className="usb-upload">
          <h2>Upload from USB</h2>

          <p>Insert your USB drive and select your document.</p>

          <input
            type="file"
            accept="
                  .pdf,
                  .jpg,
                  .jpeg,
                  .png
                "
            onChange={handleUSBFile}
            disabled={loading}
          />

          {loading && <p>Processing document...</p>}
        </section>
      )}

      {uploadMethod === "QR" && session && hotspot && (
        <section className="qr-upload">
          <h2>Upload from Phone</h2>

          <div className="qr-steps">
            <div className="qr-step">
              <h3>1. Connect to kiosk Wi-Fi</h3>

              <QRCodeSVG
                value={
                  `WIFI:T:WPA;` +
                  `S:${hotspot.ssid};` +
                  `P:${hotspot.password};;`
                }
                size={220}
              />

              <p>
                Network: <strong>{hotspot.ssid}</strong>
              </p>

              <p>
                Password: <strong>{hotspot.password}</strong>
              </p>
            </div>

            <div className="qr-step">
              <h3>2. Scan to upload</h3>

              <QRCodeSVG value={session.upload_url} size={220} />

              <p>Scan after connecting to the kiosk Wi-Fi.</p>
            </div>
          </div>

          <div className="upload-status">
            {session.status === "WAITING" && <p>Waiting for document...</p>}

            {session.status === "UPLOADING" && <p>Receiving document...</p>}
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={handleCancelQR}
          >
            Cancel
          </button>
        </section>
      )}
    </main>
  );
}
