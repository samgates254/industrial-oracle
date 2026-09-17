# Industrial Oracle — frontend

Next.js 14 App Router command-center UI. This package lives in the Industrial Oracle monorepo next to the Python engine.

```bash
npm install
npm run dev
```

| Script | Command |
| --- | --- |
| Dev | `npm run dev` |
| Typecheck | `npm run typecheck` |
| Lint | `npm run lint` |
| Unit tests | `npm test` |
| Production build | `npm run build` |

Demo data lives in `src/lib/demo` and is labeled in the UI. It is not live telemetry and it is not a HiGHS solve.

Engine mathematics stay in `../src/industrial_oracle`. This UI does not run the solver.
