"use client";

import { getApi } from "@/lib/api";
import { CheckCircle, Loader2, MessageCircle, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

export function WhatsAppConfig() {
  const [connected, setConnected] = useState(false);
  const [phone, setPhone] = useState("");
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [phoneInput, setPhoneInput] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const api = getApi();
        const status = await api.getWhatsAppStatus();
        setConnected(status.connected);
        if (status.phone) setPhone(status.phone);
      } catch {
        // Not connected yet
      } finally {
        setLoading(false);
      }
    };
    checkStatus();
  }, []);

  const handleConnect = async () => {
    const cleanedPhone = phoneInput.replace(/\D/g, "");
    if (!cleanedPhone || cleanedPhone.length < 10) {
      setError("Please enter a valid phone number with country code");
      return;
    }

    setConnecting(true);
    setError("");

    try {
      const api = getApi();
      const result = await api.connectWhatsApp(cleanedPhone);
      setQrCode(result.qr_code);
      setConnected(result.connected);
      if (result.connected) {
        setPhone(cleanedPhone);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setConnecting(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-border p-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 size={14} className="animate-spin" />
          Checking connection...
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-center gap-2">
        <MessageCircle size={20} className="text-green-500" />
        <h3 className="text-lg font-semibold">WhatsApp</h3>
      </div>

      {connected ? (
        <div className="mt-3 space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle size={16} className="text-green-500" />
            <span className="text-sm text-muted-foreground">
              Connected to <strong>{phone}</strong>
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            Forward content ideas to this WhatsApp number and they&apos;ll appear
            in your Idea Bank automatically.
          </p>
        </div>
      ) : (
        <div className="mt-3 space-y-3">
          {qrCode ? (
            <div className="space-y-2">
              <div className="rounded-md border border-border bg-muted/30 p-4 text-center">
                <p className="text-sm font-medium mb-2">Scan this QR code</p>
                <img
                  src={qrCode}
                  alt="WhatsApp QR Code"
                  className="mx-auto h-48 w-48 rounded-md"
                />
                <p className="mt-2 text-xs text-muted-foreground">
                  Open WhatsApp &rarr; Linked Devices &rarr; Link a Device
                </p>
              </div>
              <button
                type="button"
                onClick={() => setQrCode(null)}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Connect your WhatsApp number to capture content ideas on the go.
              </p>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Phone number (with country code)
                </label>
                <div className="flex gap-2">
                  <input
                    type="tel"
                    value={phoneInput}
                    onChange={(e) => setPhoneInput(e.target.value)}
                    placeholder="+521234567890"
                    className="block flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                  <button
                    type="button"
                    onClick={handleConnect}
                    disabled={connecting || !phoneInput.trim()}
                    className="inline-flex items-center gap-1 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
                  >
                    {connecting ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <MessageCircle size={14} />
                    )}
                    Connect
                  </button>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-1 rounded-md bg-red-50 p-2 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-400">
                  <XCircle size={14} />
                  {error}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
