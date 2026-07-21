"use client";

import { useEffect, useState } from "react";
import { getApi } from "@/lib/api";

export function InstagramConnect() {
  const [connected, setConnected] = useState(false);
  const [accountName, setAccountName] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const api = getApi();
        const status = await api.getInstagramStatus();
        setConnected(status.connected);
        if (status.account) {
          setAccountName((status.account as { account_name?: string }).account_name || "");
        }
      } catch {
        // Not connected
      } finally {
        setLoading(false);
      }
    };
    checkStatus();
  }, []);

  const handleConnect = async () => {
    try {
      const api = getApi();
      const { auth_url } = await api.connectInstagram(window.location.origin + "/settings/integrations");
      // Store the redirect handler in sessionStorage before leaving
      sessionStorage.setItem("instagram_oauth_state", "pending");
      window.location.href = auth_url;
    } catch (err: unknown) {
      console.error("Failed to start Instagram OAuth", err);
    }
  };

  // Handle OAuth callback detection on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    if (code && sessionStorage.getItem("instagram_oauth_state") === "pending") {
      sessionStorage.removeItem("instagram_oauth_state");
      const handleCallback = async () => {
        try {
          const api = getApi();
          await api.instagramCallback(code);
          setConnected(true);
          // Remove code from URL
          window.history.replaceState({}, "", window.location.pathname);
          // Reload to show connected state
          window.location.reload();
        } catch (err: unknown) {
          console.error("Instagram callback failed", err);
        }
      };
      handleCallback();
    }
  }, []);

  if (loading) {
    return <div className="text-sm text-muted-foreground">Checking connection...</div>;
  }

  return (
    <div className="rounded-lg border border-border p-4">
      <h3 className="text-lg font-semibold">Instagram</h3>
      {connected ? (
        <div className="mt-2 space-y-2">
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-muted-foreground">
              Connected as <strong>{accountName}</strong>
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            Your Instagram Business account is linked. You can create, schedule, and publish posts.
          </p>
        </div>
      ) : (
        <div className="mt-2 space-y-2">
          <p className="text-sm text-muted-foreground">
            Connect your Instagram Business account to start publishing.
          </p>
          <button
            onClick={handleConnect}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90"
          >
            Connect Instagram
          </button>
        </div>
      )}
    </div>
  );
}
