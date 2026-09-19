import type { CapacitorConfig } from "@capacitor/cli";

// Android wrapper for the same React build. The API base URL is baked in at
// build time via VITE_API_URL (emulator -> http://10.0.2.2:8000, device -> your
// deployed HTTPS URL). Cleartext is allowed only for local development.
const config: CapacitorConfig = {
  appId: "com.sdoc.app",
  appName: "SDOC",
  webDir: "dist",
  // adjustMarginsForEdgeToEdge keeps the web view below the status bar on Android 15+.
  android: { allowMixedContent: true, adjustMarginsForEdgeToEdge: "auto" },
  server: { androidScheme: "http", cleartext: true },
};

export default config;
