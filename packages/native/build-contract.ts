import app from "./src-tauri/tauri.conf.json";

// Type-checked entrypoint contract: remote web app is the native rendering source.
export const hostedWebOrigin: string = app.app.windows[0].url;
