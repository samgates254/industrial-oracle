import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-start justify-center bg-command io-page">
      <p className="type-panel">Not found</p>
      <h1 className="type-page-title mt-2">This route does not exist</h1>
      <p className="type-secondary mt-2 max-w-prose">
        The requested screen is not part of Industrial Oracle. Return to the Command
        Center.
      </p>
      <div className="mt-4">
        <Button asChild variant="primary" size="sm">
          <Link href="/command">Command Center</Link>
        </Button>
      </div>
    </div>
  );
}
