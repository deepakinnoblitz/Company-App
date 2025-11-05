// ===============================
// 🌐 PWA Initialization Script
// ===============================

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Register Service Worker (combined one)
  if ("serviceWorker" in navigator) {
    try {
      const registration = await navigator.serviceWorker.register("/assets/company/service-worker.js");
      console.log("✅ Service Worker registered:", registration);

      // Optional: listen for updates
      registration.onupdatefound = () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.onstatechange = () => {
            if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
              console.log("🔄 New service worker installed — will activate after reload.");
              frappe.show_alert({
                message: "A new version is available. Refresh to update!",
                indicator: "blue"
              }, 8);
            }
          };
        }
      };
    } catch (err) {
      console.error("❌ Service Worker registration failed:", err);
    }
  } else {
    console.warn("🚫 Service Workers are not supported in this browser.");
  }

  // ✅ Add manifest dynamically (in case it’s not linked in index.html)
  const existingManifest = document.querySelector("link[rel='manifest']");
  if (!existingManifest) {
    const manifestLink = document.createElement("link");
    manifestLink.rel = "manifest";
    manifestLink.href = "/assets/company/manifest.json";
    document.head.appendChild(manifestLink);
    console.log("📝 Manifest added dynamically.");
  }

  // ✅ Optional: Prompt install (for Chrome/Edge users)
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    window.deferredPrompt = e;
    console.log("📲 PWA install prompt ready.");
  });
});
