// Universal Media Grabber — Content Script
// รองรับ:
// 1. วางเมาส์เหนือภาพ/วิดีโอ (Hover HUD) หรือลากมาวาง (Drag & Drop)
// 2. ถ้าไฟล์ต้องใช้เซิร์ฟเวอร์แปลง (เช่น .m3u8, .webm, .mkv, .avif, .svg) จะสั่งปลุกเซิร์ฟเวอร์อัตโนมัติ
// 3. แสดงสถานะ "⏳ กำลังประมวลผลภาพ/วิดีโอ..." และเมื่อเสร็จจะมีปุ่ม "📥 ประมวลผลเสร็จแล้ว! กดโหลดอีกครั้ง" ให้กดโหลดซ้ำได้ทันที!
(() => {
  if (window.__UMG_INITIALIZED__) return;
  window.__UMG_INITIALIZED__ = true;

  const COMPANION_URL = "http://127.0.0.1:8765";
  const WEIRD_EXT_REGEX = /\.(webp|avif|svg|svgz|jfif|bmp|gif|ico|tiff|tif|heic|webm|ogv|ogg|mov|mkv|ts|m3u8|mpd|flv|avi|bin|dat|php)(\?.*|#.*|$)/i;
  let currentTarget = null;
  let hideTimer = null;
  let lastReadyDownload = null; // { url, filename }

  function sanitizeCleanStem(rawName, prefix = "media") {
    if (!rawName) return `${prefix}_${Date.now()}`;
    let base = String(rawName).split("?")[0].split("#")[0].split("/").pop() || prefix;
    try {
      base = decodeURIComponent(base);
    } catch (_) {}
    base = base.replace(WEIRD_EXT_REGEX, "").replace(/\.(png|jpg|jpeg|mp4)$/i, "");
    base = base.replace(/[^a-zA-Z0-9ก-๙_\-]/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
    if (!base || ["blob", "data", "media", "image", "video"].includes(base.toLowerCase())) {
      base = `${prefix}_${Date.now().toString().slice(-6)}`;
    }
    return base.slice(0, 70);
  }

  async function convertImageInBrowserCanvas(info, targetFormat) {
    const fmt = targetFormat === "jpg" ? "jpg" : "png";
    const mime = fmt === "jpg" ? "image/jpeg" : "image/png";
    const stem = sanitizeCleanStem(info.element?.getAttribute("alt") || info.url, "image");
    const filename = `${stem}.${fmt}`;

    const img = new Image();
    img.crossOrigin = "anonymous";

    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
      if (info.svgText) {
        img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(info.svgText);
      } else if (info.base64Data) {
        img.src = info.base64Data;
      } else {
        img.src = info.url;
      }
    });

    const w = img.naturalWidth || img.width || 800;
    const h = img.naturalHeight || img.height || 600;
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");

    if (fmt === "jpg") {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, w, h);
    }
    ctx.drawImage(img, 0, 0, w, h);
    const dataUrl = canvas.toDataURL(mime, 0.95);
    return { dataUrl, filename };
  }

  function triggerBrowserDownload(urlOrDataUrl, filename) {
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage({
        type: "UMG_DIRECT_DOWNLOAD",
        url: urlOrDataUrl,
        filename,
      });
    } else {
      const a = document.createElement("a");
      a.href = urlOrDataUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
  }

  // Hover HUD Host
  const hoverHost = document.createElement("div");
  hoverHost.id = "umg-hover-host";
  hoverHost.style.display = "none";
  const shadow = hoverHost.attachShadow({ mode: "open" });

  shadow.innerHTML = `
    <style>
      .hud-bar {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(15, 23, 42, 0.94);
        backdrop-filter: blur(10px);
        color: #f8fafc;
        padding: 6px 10px;
        border-radius: 10px;
        border: 1px solid rgba(16, 185, 129, 0.55);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 12px;
        user-select: none;
      }
      .badge {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        font-weight: 700;
        padding: 3px 7px;
        border-radius: 6px;
        font-size: 11px;
      }
      .btn {
        cursor: pointer;
        border: none;
        border-radius: 7px;
        padding: 5px 10px;
        font-size: 12px;
        font-weight: 600;
        color: #ffffff;
        background: linear-gradient(135deg, #10b981, #059669);
        transition: transform 0.12s ease, opacity 0.12s ease;
        display: inline-flex;
        align-items: center;
        gap: 4px;
      }
      .btn.secondary {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
      }
      .btn.processing {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        cursor: wait;
      }
      .btn.ready-again {
        background: linear-gradient(135deg, #059669, #047857);
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.6);
      }
      .btn:hover {
        transform: translateY(-1px);
        opacity: 0.95;
      }
    </style>
    <div class="hud-bar" id="hud-bar">
      <span class="badge" id="hud-badge">MEDIA</span>
      <button class="btn" id="btn-primary">⬇ โหลด PNG</button>
      <button class="btn secondary" id="btn-secondary" style="display:none;">⬇ โหลด JPG</button>
      <button class="btn ready-again" id="btn-redownload" style="display:none;">📥 กดโหลดอีกครั้ง</button>
    </div>
  `;
  document.documentElement.appendChild(hoverHost);

  // Toast & Interactive Processing Card Host
  const toastHost = document.createElement("div");
  toastHost.id = "umg-toast-host";
  const toastShadow = toastHost.attachShadow({ mode: "open" });
  toastShadow.innerHTML = `
    <style>
      .wrapper {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 8px;
        pointer-events: none;
      }
      .dock, .status-card {
        pointer-events: auto;
        background: rgba(15, 23, 42, 0.95);
        color: #f8fafc;
        padding: 10px 14px;
        border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
      }
      .dock {
        border: 2px dashed rgba(52, 211, 153, 0.5);
        cursor: pointer;
      }
      .dock.dragover {
        background: rgba(16, 185, 129, 0.25);
        border-color: #10b981;
      }
      .status-card {
        border-left: 4px solid #f59e0b;
        display: none;
        align-items: center;
        gap: 10px;
      }
      .status-card.ready {
        border-left-color: #10b981;
      }
      .dl-again-btn {
        cursor: pointer;
        border: none;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 700;
        color: #fff;
        background: linear-gradient(135deg, #10b981, #059669);
      }
      .close-btn {
        cursor: pointer;
        background: transparent;
        border: none;
        color: #94a3b8;
        font-size: 14px;
      }
    </style>
    <div class="wrapper">
      <div class="status-card" id="status-card">
        <span id="status-text">⏳ กำลังประมวลผลภาพ/วิดีโอ...</span>
        <button class="dl-again-btn" id="card-dl-btn" style="display:none;">📥 กดโหลดอีกครั้ง</button>
        <button class="close-btn" id="card-close-btn">✕</button>
      </div>
      <div class="dock" id="quick-drop-dock" title="ลากรูปหรือวิดีโอมาวางที่นี่เพื่อโหลดเป็น .PNG / .MP4 ทันที">
        📥 ลากภาพ/วิดีโอวางที่นี่ ➔ ได้ไฟล์ <b>.PNG / .MP4</b>
      </div>
    </div>
  `;
  document.documentElement.appendChild(toastHost);

  const statusCard = toastShadow.getElementById("status-card");
  const statusText = toastShadow.getElementById("status-text");
  const cardDlBtn = toastShadow.getElementById("card-dl-btn");
  const cardCloseBtn = toastShadow.getElementById("card-close-btn");

  const badgeEl = shadow.getElementById("hud-badge");
  const btnPrimary = shadow.getElementById("btn-primary");
  const btnSecondary = shadow.getElementById("btn-secondary");
  const btnRedownload = shadow.getElementById("btn-redownload");

  cardCloseBtn.addEventListener("click", () => {
    statusCard.style.display = "none";
  });

  function setProcessingState(mediaType, targetFormat) {
    const label = mediaType === "video" ? "วิดีโอเป็น .MP4" : `ภาพเป็น .${targetFormat.toUpperCase()}`;
    statusCard.style.display = " inline-flex";
    statusCard.classList.remove("ready");
    statusText.textContent = `⏳ กำลังประมวลผล${label}... รอสักครู่นะคะ`;
    cardDlBtn.style.display = "none";

    btnPrimary.classList.add("processing");
    btnPrimary.textContent = `⏳ กำลังประมวลผล...`;
    btnRedownload.style.display = "none";
  }

  function setFinishedState(downloadUrl, filename, mediaType) {
    lastReadyDownload = { url: downloadUrl, filename };
    statusCard.style.display = "inline-flex";
    statusCard.classList.add("ready");
    statusText.textContent = `✅ ประมวลผลเสร็จแล้ว! (${filename})`;
    cardDlBtn.style.display = "inline-flex";
    cardDlBtn.textContent = "📥 กดโหลดอีกครั้ง";

    btnPrimary.classList.remove("processing");
    btnPrimary.textContent = mediaType === "video" ? "⬇ โหลด MP4" : "⬇ โหลด PNG";
    btnRedownload.style.display = "inline-flex";
    btnRedownload.textContent = `📥 ประมวลผลเสร็จแล้ว! กดโหลด (${filename})`;
  }

  cardDlBtn.addEventListener("click", () => {
    if (lastReadyDownload) {
      triggerBrowserDownload(lastReadyDownload.url, lastReadyDownload.filename);
    }
  });

  btnRedownload.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    if (lastReadyDownload) {
      triggerBrowserDownload(lastReadyDownload.url, lastReadyDownload.filename);
    }
  });

  function extractMediaInfo(el) {
    if (!el || !el.tagName) return null;
    const tag = el.tagName.toLowerCase();

    if (tag === "video") {
      const src = el.currentSrc || el.src || (el.querySelector("source") && el.querySelector("source").src) || el.dataset.hlsSrc || el.dataset.src || "";
      return { mediaType: "video", url: src, element: el, label: "VIDEO → MP4" };
    }
    if (tag === "img") {
      const src = el.currentSrc || el.src || "";
      if (!src) return null;
      return { mediaType: "image", url: src, element: el, label: "IMG → PNG/JPG" };
    }
    if (tag === "svg" || el.closest("svg")) {
      const svgEl = tag === "svg" ? el : el.closest("svg");
      return { mediaType: "image", svgText: svgEl.outerHTML, element: svgEl, label: "SVG → PNG/JPG" };
    }
    if (tag === "canvas") {
      try {
        return { mediaType: "image", base64Data: el.toDataURL("image/png"), element: el, label: "CANVAS → PNG/JPG" };
      } catch (_) {}
    }
    const bg = window.getComputedStyle(el).backgroundImage;
    if (bg && bg.startsWith("url(")) {
      const m = bg.match(/url\(["']?([^"')]+)["']?\)/);
      if (m && m[1]) {
        return { mediaType: "image", url: m[1], element: el, label: "BG → PNG/JPG" };
      }
    }
    return null;
  }

  async function triggerConvertAndDownload(info, targetFormat) {
    setProcessingState(info.mediaType, targetFormat);

    const payload = {
      url: info.url || "",
      base64Data: info.base64Data || "",
      svgText: info.svgText || "",
      targetFormat,
      filename: info.element?.getAttribute("alt") || info.element?.dataset?.name || info.url || `media_${Date.now()}`,
    };

    if (payload.url && payload.url.startsWith("blob:")) {
      try {
        const res = await fetch(payload.url);
        const blob = await res.blob();
        payload.base64Data = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(blob);
        });
      } catch (_) {}
    }

    // 1. ส่งให้ Background Service Worker (สั่งปลุกเซิร์ฟเวอร์อัตโนมัติถ้ายังไม่เปิด หรือแปลงผ่าน OffscreenCanvas)
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage && !info.svgText) {
      try {
        const swRes = await new Promise((resolve) => {
          chrome.runtime.sendMessage(
            {
              type: "UMG_SMART_CONVERT_AND_DOWNLOAD",
              payload: {
                mediaType: info.mediaType,
                url: payload.url,
                base64Data: payload.base64Data,
                svgText: payload.svgText,
                targetFormat,
                filename: payload.filename,
                autoDownload: true,
              },
            },
            (res) => resolve(res)
          );
        });
        if (swRes && swRes.ok) {
          setFinishedState(swRes.downloadUrl, swRes.filename, info.mediaType);
          return;
        }
      } catch (_) {}
    }

    // 2. เรียก Companion Server โดยตรง
    const endpoint = info.mediaType === "video" ? "/api/convert/video" : "/api/convert/image";
    try {
      const resp = await fetch(`${COMPANION_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (data.ok && data.downloadUrl) {
        triggerBrowserDownload(data.downloadUrl, data.filename);
        setFinishedState(data.downloadUrl, data.filename, info.mediaType);
        return;
      }
    } catch (_) {}

    // 3. Fallback แปลงใน Browser Canvas ทันที
    try {
      if (info.mediaType === "image") {
        const converted = await convertImageInBrowserCanvas(info, targetFormat);
        triggerBrowserDownload(converted.dataUrl, converted.filename);
        setFinishedState(converted.dataUrl, converted.filename, info.mediaType);
      } else {
        const stem = sanitizeCleanStem(payload.filename, "video");
        const cleanMp4 = `${stem}.mp4`;
        const dlUrl = payload.base64Data || payload.url;
        triggerBrowserDownload(dlUrl, cleanMp4);
        setFinishedState(dlUrl, cleanMp4, info.mediaType);
      }
    } catch (err) {
      statusText.textContent = `❌ ประมวลผลไม่สำเร็จ: ${err.message}`;
      btnPrimary.classList.remove("processing");
    }
  }

  const quickDock = toastShadow.getElementById("quick-drop-dock");
  quickDock.addEventListener("dragover", (e) => {
    e.preventDefault();
    quickDock.classList.add("dragover");
  });
  quickDock.addEventListener("dragleave", () => quickDock.classList.remove("dragover"));
  quickDock.addEventListener("drop", (e) => {
    e.preventDefault();
    quickDock.classList.remove("dragover");
    if (currentTarget) {
      const fmt = currentTarget.mediaType === "video" ? "mp4" : "png";
      triggerConvertAndDownload(currentTarget, fmt);
      return;
    }
    const droppedUrl = e.dataTransfer.getData("text/uri-list") || e.dataTransfer.getData("text/plain");
    if (droppedUrl) {
      const isVid = /\.(webm|ogv|mov|mkv|ts|m3u8|mp4)(\?|$)/i.test(droppedUrl);
      triggerConvertAndDownload({ mediaType: isVid ? "video" : "image", url: droppedUrl }, isVid ? "mp4" : "png");
    }
  });

  btnPrimary.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    if (!currentTarget) return;
    const fmt = currentTarget.mediaType === "video" ? "mp4" : "png";
    triggerConvertAndDownload(currentTarget, fmt);
  });

  btnSecondary.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    if (!currentTarget) return;
    triggerConvertAndDownload(currentTarget, "jpg");
  });

  document.addEventListener("mouseover", (e) => {
    if (e.target === hoverHost || hoverHost.contains(e.target)) {
      if (hideTimer) clearTimeout(hideTimer);
      return;
    }
    const info = extractMediaInfo(e.target);
    if (!info) return;

    if (hideTimer) clearTimeout(hideTimer);
    if (currentTarget?.element && currentTarget.element !== info.element) {
      currentTarget.element.classList.remove("umg-media-hovered");
      btnRedownload.style.display = "none";
    }
    currentTarget = info;
    info.element.classList.add("umg-media-hovered");

    const rect = info.element.getBoundingClientRect();
    badgeEl.textContent = info.label;
    if (info.mediaType === "video") {
      btnPrimary.textContent = "⬇ โหลด MP4";
      btnSecondary.style.display = "none";
    } else {
      btnPrimary.textContent = "⬇ โหลด PNG";
      btnSecondary.style.display = "inline-flex";
      btnSecondary.textContent = "⬇ โหลด JPG";
    }

    hoverHost.style.top = `${Math.max(8, rect.top + 8)}px`;
    hoverHost.style.left = `${Math.max(8, rect.left + 8)}px`;
    hoverHost.style.display = "block";
  }, true);

  document.addEventListener("mouseout", (e) => {
    if (currentTarget && e.target === currentTarget.element) {
      hideTimer = setTimeout(() => {
        if (currentTarget?.element) currentTarget.element.classList.remove("umg-media-hovered");
        hoverHost.style.display = "none";
      }, 900);
    }
  }, true);

  if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
      if (msg.type === "UMG_SCAN_PAGE") {
        const items = [];
        document.querySelectorAll("img, video, svg, canvas, [style*='background-image']").forEach((el, idx) => {
          const info = extractMediaInfo(el);
          if (info) {
            items.push({
              index: idx,
              mediaType: info.mediaType,
              url: info.url || "",
              svgText: info.svgText || "",
              base64Data: info.base64Data || "",
              label: info.label,
            });
          }
        });
        sendResponse({ ok: true, items });
        return true;
      }
    });
  }
})();
