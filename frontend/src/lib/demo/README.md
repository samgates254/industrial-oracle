# Demo data layer

This directory is the **only** place synthetic operational data may live.

Rules:

- Demo snapshots are typed (`CommandCenterSnapshot`, `PlantTopologySnapshot`).
- `meta.source` is always `"demo"`.
- The UI must label the data as synthetic. Never present it as live telemetry.
- Timestamps are deterministic to keep SSR and client markup aligned.
- Replace these modules with API clients when `NEXT_PUBLIC_DATA_SOURCE=api`.
- Do not compute optimization mathematics, economic impact, or authorization here.
