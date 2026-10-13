# Desktop wrapper

Tauri 2 will load the **same publicly deployed HTTPS website** as the browser.
This package reserves the native wrapper boundary; the final host URL has not
been deployed or verified, so no Tauri executable is presented as working.

The eventual WebView must restrict remote navigation and native capabilities,
and must work with Supabase authentication. No bundled Python server or
second React frontend is permitted.
