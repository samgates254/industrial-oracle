import type { Metadata } from "next";
import Link from "next/link";
import { Wordmark } from "@/components/brand/mark";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = { title: "Sign in" };

export default function LoginPage() {
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
          Phase 1 foundation · demo identity is labeled in the shell
        </p>
      </aside>
      <main id="main" className="flex items-start p-6 lg:p-10">
        <section className="w-full max-w-md">
          <div className="mb-4 flex items-center gap-2">
            <p className="type-panel">Sign in</p>
            <Badge tone="demo">Demo identity</Badge>
          </div>
          <h2 className="type-section">Enter command center</h2>
          <p className="type-secondary mt-2">
            Authentication is not connected to a backend in Phase 1. This is a
            real route, not a consumer marketing form.
          </p>
          <form className="mt-6 flex flex-col gap-3">
            <label className="type-meta text-secondary" htmlFor="email">
              Operator identity
            </label>
            <Input
              id="email"
              name="email"
              type="email"
              defaultValue="a.mwangi@demo.industrial-oracle"
              autoComplete="username"
              readOnly
            />
            <label className="type-meta text-secondary" htmlFor="password">
              Passphrase
            </label>
            <Input
              id="password"
              name="password"
              type="password"
              defaultValue="demo"
              autoComplete="current-password"
              readOnly
            />
            <Button asChild variant="primary">
              <Link href="/command">Enter command center</Link>
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
