/**
 * SafePay Assistant — Embeddable Chat Widget
 * ============================================
 *
 * Usage on any client website (ONE line):
 *
 *   <script src="https://your-server.com/widget.js" async></script>
 *
 * Optional configuration via data attributes:
 *
 *   <script src="https://your-server.com/widget.js"
 *           data-api="https://your-server.com"
 *           data-position="bottom-right"
 *           data-theme="dark"
 *           async></script>
 *
 * The script auto-detects its own URL to figure out the API base,
 * so in most cases you don't need data-api at all.
 */
(function () {
    "use strict";

    // ── Detect the server base URL from the script's own src ────────────────
    var scripts = document.getElementsByTagName("script");
    var ownScript = scripts[scripts.length - 1];
    var scriptSrc = ownScript.src || "";
    var API_BASE = ownScript.getAttribute("data-api") || scriptSrc.replace(/\/widget\.js.*$/, "");
    var WIDGET_URL = API_BASE + "/widget.html";

    // ── Configuration ────────────────────────────────────────────────────────
    var position = (ownScript.getAttribute("data-position") || "bottom-right").toLowerCase();

    // ── Prevent double-init ──────────────────────────────────────────────────
    if (window.__safepayWidgetInit) return;
    window.__safepayWidgetInit = true;

    // ── Inject CSS ───────────────────────────────────────────────────────────
    var css = `
#safepay-bubble {
    position: fixed;
    ${position.includes("left") ? "left" : "right"}: 20px;
    bottom: 20px;
    width: 60px; height: 60px;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    z-index: 2147483000;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    animation: safepay-pulse 2.5s infinite;
}
#safepay-bubble:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 28px rgba(99, 102, 241, 0.55);
}
#safepay-bubble svg { width: 28px; height: 28px; fill: white; }
#safepay-bubble .safepay-close { display: none; }
#safepay-bubble.open .safepay-chat-icon { display: none; }
#safepay-bubble.open .safepay-close { display: block; }
#safepay-bubble.open { animation: none; }

#safepay-bubble .safepay-badge {
    position: absolute;
    top: -2px; ${position.includes("left") ? "left" : "right"}: -2px;
    width: 18px; height: 18px;
    background: #22c55e;
    border: 2px solid #0f172a;
    border-radius: 50%;
    font-size: 10px; color: white;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600;
}

#safepay-panel {
    position: fixed;
    ${position.includes("left") ? "left" : "right"}: 20px;
    bottom: 90px;
    width: 380px; height: 560px;
    max-width: calc(100vw - 40px);
    max-height: calc(100vh - 120px);
    border: none;
    border-radius: 16px;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
    z-index: 2147483001;
    display: none;
    overflow: hidden;
    opacity: 0;
    transform: translateY(20px) scale(0.95);
    transition: opacity 0.3s ease, transform 0.3s ease;
}
#safepay-panel.open {
    display: block;
    opacity: 1;
    transform: translateY(0) scale(1);
}

@keyframes safepay-pulse {
    0%, 100% { box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4); }
    50% { box-shadow: 0 4px 20px rgba(99, 102, 241, 0.6), 0 0 0 8px rgba(99, 102, 241, 0.08); }
}

@media (max-width: 480px) {
    #safepay-panel {
        width: 100vw; height: 100vh;
        right: 0; left: 0; bottom: 0;
        border-radius: 0;
        max-width: 100%; max-height: 100%;
    }
    #safepay-bubble { bottom: 16px; ${position.includes("left") ? "left" : "right"}: 16px; }
}
`;
    var style = document.createElement("style");
    style.id = "safepay-widget-css";
    style.textContent = css;
    document.head.appendChild(style);

    // ── Create the floating bubble ───────────────────────────────────────────
    var bubble = document.createElement("div");
    bubble.id = "safepay-bubble";
    bubble.innerHTML = `
        <svg class="safepay-chat-icon" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.38 5.07L2 22l4.93-1.38C8.42 21.5 10.15 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.66 0-3.22-.45-4.55-1.24l-.33-.2-2.94.82.78-2.87-.21-.33C3.86 14.85 3.4 13.4 3.4 12c0-4.75 3.85-8.6 8.6-8.6s8.6 3.85 8.6 8.6-3.85 8.6-8.6 8.6z"/>
            <path d="M12 6c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm-3 5h6v1.5H9V11zm0 2.5h6V15H9v-1.5z" fill="white"/>
        </svg>
        <svg class="safepay-close" viewBox="0 0 24 24">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
        <div class="safepay-badge">1</div>
    `;
    document.body.appendChild(bubble);

    // ── Create the iframe panel ──────────────────────────────────────────────
    var panel = document.createElement("iframe");
    panel.id = "safepay-panel";
    panel.src = WIDGET_URL + "?api=" + encodeURIComponent(API_BASE);
    panel.setAttribute("scrolling", "no");
    panel.setAttribute("frameborder", "0");
    panel.setAttribute("allow", "clipboard-write");
    document.body.appendChild(panel);

    // ── Toggle logic ─────────────────────────────────────────────────────────
    var isOpen = false;

    function toggleWidget() {
        isOpen = !isOpen;
        if (isOpen) {
            bubble.classList.add("open");
            panel.classList.add("open");
            // Remove the notification badge after opening
            var badge = bubble.querySelector(".safepay-badge");
            if (badge) badge.style.display = "none";
        } else {
            bubble.classList.remove("open");
            panel.classList.remove("open");
        }
    }

    bubble.addEventListener("click", toggleWidget);

    // ── Auto-open after delay (optional, can be disabled) ─────────────────────
    var autoOpen = ownScript.getAttribute("data-auto-open");
    if (autoOpen !== "false") {
        setTimeout(function () {
            if (!isOpen) toggleWidget();
        }, 3000);
    }
})();
