// ===============================
// ✅ FIREBASE INITIALIZATION (v10+ compat)
// ===============================

// Step 1️⃣ - Load Firebase App first
const scriptApp = document.createElement("script");
scriptApp.src = "https://www.gstatic.com/firebasejs/10.8.1/firebase-app-compat.js";

// When firebase-app-compat is loaded...
scriptApp.onload = () => {
  console.log("🟢 Firebase App Loaded");

  // Step 2️⃣ - Load Firebase Messaging next
  const scriptMsg = document.createElement("script");
  scriptMsg.src = "https://www.gstatic.com/firebasejs/10.8.1/firebase-messaging-compat.js";

  scriptMsg.onload = () => {
    console.log("🟢 Firebase Messaging Loaded");

    // Step 3️⃣ - Initialize Firebase
    const firebaseConfig = {
      apiKey: "AIzaSyAp3cIYT8C4gRD_vliPK0PODHzyyyFYu4Y",
      authDomain: "company-erp-ef845.firebaseapp.com",
      projectId: "company-erp-ef845",
      storageBucket: "company-erp-ef845.firebasestorage.app",
      messagingSenderId: "695314443067",
      appId: "1:695314443067:web:07f8f463a526660a7e251e",
      measurementId: "G-ZDGX26G2EW",
    };

    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    console.log("✅ Firebase initialized");

    // Step 4️⃣ - Register Service Worker
    navigator.serviceWorker
      .register("/assets/company/service-worker.js")
      .then((registration) => {
        console.log("🟢 Service Worker registered:", registration);

        // Step 5️⃣ - Request notification permission
        Notification.requestPermission().then((permission) => {
          console.log("🔹 Notification permission:", permission);

          if (permission === "granted") {
            // Step 6️⃣ - Get FCM token using VAPID key + service worker
            messaging
              .getToken({
                vapidKey: frappe.boot.site_config.firebase.vapid_key,
                serviceWorkerRegistration: registration, // ✅ v9+ correct way
              })
              .then((token) => {
                if (token) {
                  console.log("🔥 Got FCM Token:", token);

                  // Save token to backend
                  frappe.call({
                    method: "company.company.api.save_fcm_token",
                    args: { token },
                    callback: function (r) {
                      console.log("✅ Token saved:", r);
                    },
                  });
                } else {
                  console.warn(
                    "⚠️ No token received — check VAPID key or Service Worker path."
                  );
                }
              })
              .catch((err) => {
                console.error("❌ Error getting token:", err);
              });
          } else {
            console.warn("🚫 Notifications not granted by user.");
          }
        });
      })
      .catch((err) => {
        console.error("❌ Service Worker registration failed:", err);
      });

    // Step 7️⃣ - Handle foreground notifications
    messaging.onMessage((payload) => {
      console.log("🔔 Notification received (foreground):", payload);
      frappe.show_alert(
        {
          message: `${payload.notification.title}: ${payload.notification.body}`,
          indicator: "blue",
        },
        10
      );
    });
  };

  document.head.appendChild(scriptMsg);
};

document.head.appendChild(scriptApp);
