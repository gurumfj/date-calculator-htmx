import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@components": path.resolve(__dirname, "./src/components"),
      "@pages": path.resolve(__dirname, "./src/pages"),
      "@hooks": path.resolve(__dirname, "./src/hooks"),
      "@contexts": path.resolve(__dirname, "./src/contexts"),
      "@services": path.resolve(__dirname, "./src/services"),
      "@utils": path.resolve(__dirname, "./src/utils"),
      "@layouts": path.resolve(__dirname, "./src/layouts"),
      "@app-types": path.resolve(__dirname, "./src/types"),
      "@app-lib": path.resolve(__dirname, "./src/lib"),
      "@stores": path.resolve(__dirname, "./src/stores"),
    },
  },
  server: {
    // proxy: {
    //   "/proxy": {
    //     target: "http://localhost:8888/proxy",
    //     changeOrigin: true,
    //     secure: false,
    //     rewrite: (path) => path.replace(/^\/proxy/, ""),
    //   },
    // },
  },
});
