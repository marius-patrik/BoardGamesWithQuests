# Desktop application

Tauri 2 opens the **same** hosted HTTPS React frontend through a remote
WebView. Native code contains no Python server or duplicate React bundle.

`BGWQ_WEB_URL` must point to the reviewed HTTPS site origin. The wrapper
rejects invalid or missing host settings. Keep native capabilities minimal;
verify navigation, credentials, guest login callbacks and reconnection.

Distribution requires a real Tauri application build, platform tests
and independent release acceptance. `bundle.active=false` prevents issuing
an installer from the scaffold.
