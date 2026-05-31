import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { copyFileSync, existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = dirname(fileURLToPath(import.meta.url));
const rootFaviconPath = resolve(currentDir, "../favicon.svg");

function rootFaviconPlugin() {
  return {
    name: "root-favicon",
    configureServer(server) {
      server.middlewares.use("/favicon.svg", (_req, res) => {
        if (!existsSync(rootFaviconPath)) {
          res.statusCode = 404;
          res.end();
          return;
        }

        res.setHeader("Content-Type", "image/svg+xml");
        res.end(readFileSync(rootFaviconPath));
      });
    },
    writeBundle() {
      if (existsSync(rootFaviconPath)) {
        copyFileSync(rootFaviconPath, resolve(currentDir, "dist/favicon.svg"));
      }
    }
  };
}

export default defineConfig({
  plugins: [react(), rootFaviconPlugin()],
  server: {
    proxy: {
      "/extract": "http://localhost:8000",
      "/chat": "http://localhost:8000"
    }
  }
});
