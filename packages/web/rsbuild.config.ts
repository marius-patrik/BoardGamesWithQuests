import { defineConfig } from "@rsbuild/core";
import { pluginReact } from "@rsbuild/plugin-react";
import { pluginTailwindcss } from "@rsbuild/plugin-tailwindcss";
import { fileURLToPath } from "node:url";

export default defineConfig({
  plugins: [pluginReact(), pluginTailwindcss()],
  source: {
    entry: { index: "./src/main.tsx" },
    alias: { "@": fileURLToPath(new URL("./src/", import.meta.url)) },
  },
  html: { template: "./index.html", title: "BoardGamesWithQuests" },
});
