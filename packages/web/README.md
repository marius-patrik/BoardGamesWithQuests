# Web application

React and TypeScript are built with Rsbuild and Bun 1.4.2.
The committed Bun lockfile fixes dependency resolution for frozen installation.
The browser UI is the **sole** frontend for web and Tauri; only the trusted
Python engine authorizes legal moves.

Install and run in `packages/web`:

```sh
bun install --frozen-lockfile
bun run dev
bun run typecheck
bun run build
```

The Vercel project `boardgameswithquests-web` builds this directory and
publishes `dist/`. Production site:
`https://boardgameswithquests-web.vercel.app`.

Auth, board interaction, settings forms, game state, clocks, quests and Realtime
must be tested through actual browser-visible outcomes. The scaffold does not
provide gameplay until those requirements are fulfilled.
