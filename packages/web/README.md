# Web frontend

Single intended React/Rsbuild interface, shared by browser and hosted Tauri
wrapper. The source bootstrap is intentionally not a playable game.

Run `bun install` from this directory to generate the Bun lockfile before
enabling web CI/deployment. The frontend has no Supabase keys, authentication or
game APIs wired yet. Public development builds must not be advertised as playable.
The production web project will use this directory as its Vercel root.
