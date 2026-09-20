import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const api = env.DEBATE_API_PROXY || "http://127.0.0.1:8009";
  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5179,
      strictPort: true,
      proxy: {
        "/v1": api,
        "/health": api,
        "/ready": api,
        "/metrics": api,
      },
    },
  };
});
