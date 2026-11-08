// Universal Media Grabber — Content Script
// รองรับ:
// 1. วางเมาส์เหนือภาพ/วิดีโอ (Hover HUD) -> กดโหลดเป็น .PNG / .JPG / .MP4 ทันที
// 2. ลากภาพหรือวิดีโอมาวางที่ปุ่มลอยมุมขวาล่าง (Quick Drop Zone) -> โหลดเป็น .PNG / .JPG / .MP4 ทันที
// 3. ระบบแปลงไฟล์คู่ขนาน (Dual-Engine): ใช้ Local Companion Server (Pillow + FFmpeg H.264) และมี Built-in HTML5 Canvas Converter ในตัวเมื่อรันเฉพาะ Extension เดี่ยวๆ
(() => {
  if (window.__UMG_INITIALIZED__) return;
  window.__UMG_INITIALIZED__ = true;

  const COMPANION_URL = "http://127.0.0.1:8765";
  const WEIRD_EXT_REGEX = /\.(webp|avif|svg|svgz|jfif|bmp|gif|ico|tiff|tif|heic|webm|ogv|ogg|mov|mkv|ts|m3u8|mpd|flv|avi|bin|dat|php)(\?.*|#.*|$)/i;
  let currentTarget = null;
  let hideTimer = null;

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

  // Built-in Browser Canvas Image Converter (Fallback when Companion Server is offline)
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

  // Create Shadow DOM Hover HUD Host
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
      .btn:hover {
        transform: translateY(-1px);
        opacity: 0.95;
      }
    </style>
    <div class="hud-bar" id="hud-bar">
      <span class="badge" id="hud-badge">MEDIA</span>
      <button class="btn" id="btn-primary">⬇ โหลด PNG</button>
      <button class="btn secondary" id="btn-secondary" style="display:none;">⬇ โหลด JPG</button>
    </div>
  `;
  document.documentElement.appendChild(hoverHost);

  // Toast & Drag-Drop Dock Host
  const toastHost = document.createElement("div");
  toastHost.id = "umg-toast-host";
  const toastShadow = toastHost.attachShadow({ mode: "open" });
  toastShadow.innerHTML = `
    <style>
      .dock {
        pointer-events: auto;
        background: rgba(15, 23, 42, 0.92);
        border: 2px dashed rgba(52, 211, 153, 0.5);
        color: #e2e8f0;
        padding: 8px 14px;
        border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 12px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.35);
        transition: all 0.15s ease;
        cursor: pointer;
      }
      .dock.dragover {
        background: rgba(16, 185, 129, 0.25);
        border-color: #10b981;
        transform: scale(1.04);
      }
      .toast {
        background: rgba(15, 23, 42, 0.95);
        color: #fff;
        border-left: 4px solid #10b981;
        padding: 10px 14px;
        border-radius: 10px;
        margin-top: 8px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 13px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
      }
    </style>
    <div class="dock" id="quick-drop-dock" title="ลากรูปหรือวิดีโอมาวางที่นี่เพื่อโหลดเป็น .PNG / .MP4 ทันที">
      📥 ลากภาพ/วิดีโอวางที่นี่ ➔ ได้ไฟล์ <b>.PNG / .MP4</b>
    </div>
    <div id="toast-list"></div>
  `;
  document.documentElement.appendChild(toastHost);

  function showToast(msg) {
    const list = toastShadow.getElementById("toast-list");
    const item = document.createElement("div");
    item.className = "toast";
    item.textContent = msg;
    list.appendChild(item);
    setTimeout(() => item.remove(), 3500);
  }

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
    showToast(`⏳ กำลังแปลงและดาวน์โหลดเป็น .${targetFormat.toUpperCase()} ...`);
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
        showToast(`✅ ดาวน์โหลดสำเร็จ: ${data.filename}`);
        return;
      }
    } catch (_) {
      // Fallback to Built-in Browser Canvas / Direct MP4 Downloader when Companion Server is not running
    }

    try {
      if (info.mediaType === "image") {
        const converted = await convertImageInBrowserCanvas(info, targetFormat);
        triggerBrowserDownload(converted.dataUrl, converted.filename);
        showToast(`✅ แปลงและดาวน์โหลดสำเร็จ: ${converted.filename}`);
      } else {
        const stem = sanitizeCleanStem(payload.filename, "video");
        const cleanMp4 = `${stem}.mp4`;
        triggerBrowserDownload(payload.base64Data || payload.url, cleanMp4);
        showToast(`✅ ดาวน์โหลดวิดีโอสำเร็จ: ${cleanMp4}`);
      }
    } catch (err) {
      showToast(`❌ ไม่สามารถแปลงไฟล์ได้: ${err.message}`);
    }
  }

  // Setup Drag-and-Drop on Quick Dock
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

  const badgeEl = shadow.getElementById("hud-badge");
  const btnPrimary = shadow.getElementById("btn-primary");
  const btnSecondary = shadow.getElementById("btn-secondary");

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
      }, 600);
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
