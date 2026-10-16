# Web

The one user interface shared by browsers and the remote Tauri WebView.
Bun installs the React/TypeScript/Rsbuild/Tailwind/shadcn/ui/Motion stack.

```sh
bun install
bun run typecheck
bun run build
bun run dev
```

Build output is `dist/`. Use the separate Vercel web project
`boardgameswithquests-web`. This is a functional React bootstrap but it
contains no playable board games or account/session flows.
