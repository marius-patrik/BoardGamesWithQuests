# Web frontend

Single intended React/Rsbuild interface, shared by browser and hosted Tauri
wrapper. The source bootstrap is intentionally not a playable game.

Run `bun install` from this directory to generate the Bun lockfile before
enabling web CI/deployment. The frontend has no Supabase keys, authentication or
game APIs wired yet. Public development builds must not be advertised as playable.
The production web project will use this directory as its Vercel root.

## Vercel bootstrap

Project: `boardgameswithquests-web` (`prj_iWSGkCmiCeh1uliqVN06b5QWPAAx`).
Initial deployment `dpl_2Sy36YSuA7Yx91cPuMEny3nWrv1P` reports READY, but
Vercel Authentication prevents public unauthenticated access. The rendered
page is intentionally a non-playable placeholder and cannot be used for class.
