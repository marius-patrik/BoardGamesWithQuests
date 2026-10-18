import config from "../src-tauri/tauri.conf.json";

// Validate the real Tauri build contract before producing native artifacts.
const url = config.app.windows[0]?.url;
if (!url || !url.startsWith("https://")) {
  throw new Error("Native wrapper must load the production HTTPS web application.");
}
if (config.build.frontendDist !== url) {
  throw new Error("The Tauri window and frontend must load the same application.");
}
if (config.app.security.capabilities.length !== 0) {
  throw new Error("Remote content must not receive native command capabilities.");
}
