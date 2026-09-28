"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Wordmark } from "@/components/brand/mark";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/client";
import { loginBackend } from "@/lib/api/backend";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");
    try {
      await loginBackend(email, password);
      router.push("/command");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "Sign-in could not be completed. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-command lg:grid-cols-[minmax(280px,34%)_1fr]">
      <aside className="flex flex-col justify-between border-b border-subtle p-6 lg:border-b-0 lg:border-r">
        <div>
          <Wordmark />
          <p className="type-panel mt-8">Operator access</p>
          <h1 className="type-page-title mt-2">Industrial Oracle</h1>
          <p className="type-secondary mt-3 max-w-sm">
            Command center for plant telemetry, constraints, optimization, and
            authorized human decision. Backend authorization remains
            authoritative.
          </p>
        </div>
        <p className="type-meta mt-8 text-muted">
          Sign in with an account provisioned by your organization.
        </p>
      </aside>
      <main id="main" className="flex items-start p-6 lg:p-10">
        <section className="w-full max-w-md">
          <div className="mb-4">
            <p className="type-panel">Sign in</p>
          </div>
          <h2 className="type-section">Enter command center</h2>
          <p className="type-secondary mt-2">
            Use your Industrial Oracle account. Access is checked by the backend.
          </p>
          <form className="mt-6 flex flex-col gap-3" onSubmit={handleSubmit}>
            <label className="type-meta text-secondary" htmlFor="email">
              Operator identity
            </label>
            <Input
              id="email"
              name="email"
              type="email"
              required
              autoComplete="username"
            />
            <label className="type-meta text-secondary" htmlFor="password">
              Passphrase
            </label>
            <Input
              id="password"
              name="password"
              type="password"
              required
              autoComplete="current-password"
            />
            {error && (
              <p className="type-meta text-state-critical" role="alert">
                {error}
              </p>
            )}
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? "Signing in..." : "Sign in"}
            </Button>
          </form>
          <p className="type-meta mt-4">
            <Link href="/organization" className="text-brand">
              Organization selector
            </Link>
          </p>
        </section>
      </main>
    </div>
  );
}
