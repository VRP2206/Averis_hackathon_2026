import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

// Inside the Capacitor shell the web view runs under the status bar; mark it
// so CSS can pad the header (see .native in index.css).
const cap = (window as unknown as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor;
if (cap?.isNativePlatform?.()) document.documentElement.classList.add("native");

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
