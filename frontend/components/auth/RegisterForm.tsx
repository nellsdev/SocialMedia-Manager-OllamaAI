"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "./AuthProvider";
import { useRouter } from "next/navigation";

export function RegisterForm() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setSubmitting(true);
    try {
      await register(email, password);
      setMessage("Account created! Check your email to verify, then sign in.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-400">
          {error}
        </div>
      )}
      {message && (
        <div className="rounded-md bg-green-50 p-3 text-sm text-green-800 dark:bg-green-900/30 dark:text-green-400">
          {message}
        </div>
      )}
      <div>
        <label htmlFor="register-email" className="block text-sm font-medium text-foreground">
          Email
        </label>
        <input
          id="register-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
          placeholder="you@example.com"
        />
      </div>
      <div>
        <label htmlFor="register-password" className="block text-sm font-medium text-foreground">
          Password
        </label>
        <input
          id="register-password"
          type="password"
          required
          minLength={6}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-50"
      >
        {submitting ? "Creating account..." : "Create account"}
      </button>
    </form>
  );
}
