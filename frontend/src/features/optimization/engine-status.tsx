"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { getEngineHealth } from "@/lib/api/engine";

export function EngineStatus() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    getEngineHealth().then((ok) => {
      if (!cancelled) setOnline(ok);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (online === null) {
    return <Badge tone="neutral">Engine…</Badge>;
  }
  if (online) {
    return <Badge tone="normal">Engine connected</Badge>;
  }
  return <Badge tone="offline">Engine offline</Badge>;
}
