"use client";

import { useAuth } from "@/components/auth/AuthProvider";

export default function AccountSettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Account</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your account settings.
        </p>
      </div>

      <div className="rounded-lg border border-border p-4">
        <h3 className="font-semibold">Profile</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Signed in as <strong>{user?.email}</strong>
        </p>
      </div>

      <div className="rounded-lg border border-border p-4">
        <h3 className="font-semibold">Sign out</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Sign out of your account on this device.
        </p>
        <button
          onClick={logout}
          className="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-700"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
