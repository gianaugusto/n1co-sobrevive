# Frontend guidance

Layout: `src/api` (typed client, mirrors backend models in `types.ts`), `src/components`, `src/hooks.ts`, `Dashboard.tsx`, `App.tsx` (Auth0 gate), `main.tsx`.

- Components are presentational and receive data/callbacks as props; data access goes through the injectable `ApiClient`, so tests use fakes (see `Dashboard.test.tsx`).
- Tailwind utility classes only; no CSS files beyond `index.css`.
- Keep `src/api/types.ts` in sync with `docs/api.md` and the backend schemas. `PII_TYPES` must match the backend `PiiType` enum.
- Run: `cd frontend && npm test`, `npm run typecheck`, `npm run build`.
