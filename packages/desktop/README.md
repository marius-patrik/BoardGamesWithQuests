# Desktop wrapper

This is a **Tauri 2 source bootstrap**, not a built or released desktop app.
Its Rust entry creates exactly one WebView of the **same hosted React website**
used by browser clients; no Python server or duplicated frontend is bundled.

The launch requires an explicit `BGWQ_WEB_URL` environment variable set to
the *final verified HTTPS origin*. Invalid or absent values fail closed; a
placeholder development server is never silently substituted.

The remote URL, login callback handling, native capabilities, window navigation,
platform packaging and security test are all G5 tasks. No Tauri build has been
executed and no hosted target is yet configured. `bundle.active=false` prevents
this bootstrap from being marketed as a finished installer.
