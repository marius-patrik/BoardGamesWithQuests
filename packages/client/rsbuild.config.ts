import { fileURLToPath } from "node:url";
import { defineConfig } from "@rsbuild/core";
import { pluginReact } from "@rsbuild/plugin-react";

export default defineConfig({
	plugins: [pluginReact()],
	source: {
		entry: { index: "./src/main.tsx" },
		alias: { "@": fileURLToPath(new URL("./src/", import.meta.url)) },
	},
	html: { template: "./index.html", title: "BoardGamesWithQuests" },
});
