// Universal Media Grabber — Content Script (Strict Image & Video Only + Video-First Piercing Engine)
// แก้ไขปัญหาครบ 100%:
// 1. จับเฉพาะ "รูปภาพจริง (<img>)" และ "วิดีโอจริง (<video>)" เท่านั้น! ไม่จับปุ่ม ไอคอน พื้นหลัง หรือกล่องข้อความมั่วซั่วอีกต่อไป
// 2. ให้ความสำคัญกับ "วิดีโอ (<video>)" เป็นอันดับ 1 (ทะลุผ่านแผ่นใสบังปุ่ม Play / รูปปก Poster บนตัวเล่นวิดีโอ) ไม่เข้าใจผิดว่าวิดีโอเป็นรูปภาพอีกต่อไป!
// 3. รองรับการดึงวิดีโอทั้งไฟล์ตรง (.mp4/.webm/.mov), สตรีม HLS (.m3u8), และวิดีโอแบบ blob: (ผ่าน Network Sniffer + yt-dlp + FFmpeg)
(() => {
  // ถ้ามีการรันซ้ำหรือกด Reload Extension ให้ล้างตัวเก่าออกอย่างสะอาดก่อนเสมอ (ป้องกันปัญหา Extension context invalidated!)
  if (typeof window.__UMG_CLEANUP__ === "function") {
    try {
      window.__UMG_CLEANUP__();
    } catch (_) {}
  }
  document.getElementById("umg-hover-host")?.remove();
  document.getElementById("umg-toast-host")?.remove();
  if (window !== window.top && (window.innerWidth < 150 || window.innerHeight < 120)) {
    return;
  }
  window.__UMG_INITIALIZED__ = true;

  const COMPANION_URL = "http://127.0.0.1:8765";
  const WEIRD_EXT_REGEX = /\.(webp|avif|svg|svgz|jfif|bmp|gif|ico|tiff|tif|heic|webm|ogv|ogg|mov|mkv|ts|m3u8|mpd|flv|avi|bin|dat|php)(\?.*|#.*|$)/i;
  const MIN_MEDIA_SIZE = 72; // ข้ามไอคอน ปุ่ม และรูปขนาดเล็กกว่า 72x72px ทั้งหมด

  let currentTarget = null;
  let lockedHudTarget = null;
  let isMouseOnHud = false;
  let hideTimer = null;
  let lastReadyDownload = null;
  let isExtensionEnabled = true;

  function isExtensionContextValid() {
    try {
      return typeof chrome !== "undefined" && Boolean(chrome.runtime && chrome.runtime.id);
    } catch (_) {
      return false;
    }
  }

  function formatNowTimestamp() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
  }

  function extractSiteBrand(urlOrPage) {
    try {
      const u = new URL(urlOrPage || window.location.href);
      const host = (u.hostname || "").toLowerCase();
      if (!host || host === "127.0.0.1" || host === "localhost") return "";
      const brandMap = [
        [["alibaba.", "alicdn."], "Alibaba"],
        [["aliexpress."], "AliExpress"],
        [["1688."], "1688"],
        [["taobao.", "tbcdn."], "Taobao"],
        [["tmall."], "Tmall"],
        [["shopee.", "shopeemobile."], "Shopee"],
        [["lazada.", "lzd-img"], "Lazada"],
        [["youtube.", "youtu.be", "ytimg.", "googlevideo."], "YouTube"],
        [["tiktok.", "tiktokcdn."], "TikTok"],
        [["facebook.", "fbcdn.", "fb.watch"], "Facebook"],
        [["instagram.", "cdninstagram."], "Instagram"],
        [["twitter.", "x.com", "twimg."], "X"],
        [["pinterest.", "pinimg."], "Pinterest"],
        [["apple.", "cdn-apple."], "Apple"],
        [["amazon.", "media-amazon."], "Amazon"],
      ];
      for (const [keys, label] of brandMap) {
        if (keys.some((k) => host.includes(k))) return label;
      }
      const parts = host.split(".").filter((p) => !["www", "m", "mobile", "cdn", "img", "s", "gv", "videocdn", "com", "co", "th", "net", "org", "io"].includes(p));
      if (parts.length > 0) {
        return parts[0].charAt(0).toUpperCase() + parts[0].slice(1, 18);
      }
    } catch (_) {}
    return "";
  }

  function isGibberishOrHash(text) {
    if (!text) return true;
    const s = String(text).trim().replace(/^[_\-\s]+|[_\-\s]+$/g, "");
    if (s.length < 2) return true;
    if (/[ก-๙]/.test(s)) return false;
    const low = s.toLowerCase();
    const generic = new Set([
      "image", "video", "media", "blob", "data", "watch", "default", "maxresdefault",
      "hqdefault", "sddefault", "mqdefault", "master", "playlist", "index", "unnamed",
      "untitled", "download", "file", "poster", "thumbnail", "thumb",
    ]);
    if (generic.has(low)) return true;
    if (/^[\d_\-xX]+$/.test(s)) return true;
    if (/^[a-fA-F0-9_\-]{12,}$/.test(s) || /^(H[a-fA-F0-9]{16,}|O1CN01[a-zA-Z0-9_\-]+|TB2[a-zA-Z0-9_\-]+)/.test(s)) return true;

    const tokens = low.split(/[_\-\s]+/).filter(Boolean);
    const codecSet = new Set(["h264", "h265", "hevc", "avc", "hd", "sd", "fhd", "uhd", "mp4", "webm", "1080p", "720p", "480p", "360p", "trans", "aidc", "vod", "target"]);
    let meaningful = 0;
    let gibberish = 0;
    for (const tok of tokens) {
      if (codecSet.has(tok) || /^\d+$/.test(tok)) continue;
      if (/\d/.test(tok) && /[a-z]/.test(tok)) {
        gibberish++;
      } else if (tok.length >= 16 && !/[aeiou]{2}/.test(tok)) {
        gibberish++;
      } else if (tok.length >= 3) {
        meaningful++;
      }
    }
    if (meaningful === 0 && (gibberish > 0 || tokens.every((t) => codecSet.has(t) || /^\d+$/.test(t)))) {
      return true;
    }
    return false;
  }

  function cleanPageTitle(rawTitle) {
    if (!rawTitle) return "";
    let t = String(rawTitle).trim().replace(/^\(\d+\)\s*/, "");
    t = t.split(/\s+(?:\||-|\u2013|\u2014)\s+(?:Alibaba|AliExpress|Shopee|Lazada|YouTube|TikTok|Facebook|Instagram|Twitter|X|Buy\s|ซื้อ\s)/i)[0];
    t = t.replace(/[^a-zA-Z0-9ก-๙_\-\s]/g, " ").replace(/[\s_]+/g, "_").replace(/^[_\-]+|[_\-]+$/g, "");
    return t.slice(0, 50);
  }

  function extractSmartContext(info) {
    const el = info?.element;
    const siteName = extractSiteBrand(info?.pageUrl || window.location.href) || extractSiteBrand(info?.url);
    const candidates = [];

    if (el) {
      candidates.push(el.getAttribute("alt"));
      candidates.push(el.getAttribute("title"));
      candidates.push(el.getAttribute("aria-label"));
      candidates.push(el.dataset?.name);
      candidates.push(el.dataset?.title);

      // ค้นหาหัวข้อสินค้า/ชื่อโพสต์ที่อยู่ใกล้เคียงในการ์ดเดียวกัน
      let parent = el.parentElement;
      for (let i = 0; i < 6 && parent && parent !== document.body; i++) {
        const heading = parent.querySelector("h1, h2, h3, figcaption, [class*='title'], [class*='subject']");
        if (heading && heading.textContent) {
          candidates.push(heading.textContent.trim().slice(0, 80));
          break;
        }
        parent = parent.parentElement;
      }
    }

    const mainH1 = document.querySelector("h1");
    if (mainH1 && mainH1.textContent) {
      candidates.push(mainH1.textContent.trim().slice(0, 80));
    }
    if (document.title) {
      candidates.push(document.title);
    }

    let bestTitle = "";
    for (const raw of candidates) {
      if (!raw || String(raw).startsWith("http")) continue;
      const cleaned = cleanPageTitle(raw);
      if (cleaned && !isGibberishOrHash(cleaned)) {
        bestTitle = cleaned;
        break;
      }
    }

    return { siteName, pageTitle: bestTitle };
  }

  function sanitizeCleanStem(rawName, prefix = "media", mediaType = "image", pageTitle = "", siteName = "") {
    const typePrefix = mediaType === "video" ? "วิดีโอ" : "รูปภาพ";
    const ts = formatNowTimestamp();
    let stem = "";

    if (rawName && !String(rawName).startsWith("http") && !String(rawName).startsWith("data:") && !String(rawName).startsWith("blob:")) {
      const cleaned = cleanPageTitle(rawName);
      if (cleaned && !isGibberishOrHash(cleaned)) stem = cleaned;
    }
    if (!stem && pageTitle) {
      const cleaned = cleanPageTitle(pageTitle);
      if (cleaned && !isGibberishOrHash(cleaned)) stem = cleaned;
    }
    if (!stem && rawName) {
      let base = String(rawName).split("?")[0].split("#")[0].split("/").pop() || "";
      try {
        base = decodeURIComponent(base);
      } catch (_) {}
      base = base.replace(/\.(jpg|jpeg|png|webp|avif|gif)_\d+x\d+.*$/i, "");
      base = base.replace(WEIRD_EXT_REGEX, "").replace(/\.(png|jpg|jpeg|mp4)$/i, "");
      base = base.replace(/[^a-zA-Z0-9ก-๙_\-]/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
      if (base && !isGibberishOrHash(base)) stem = base.slice(0, 50);
    }

    const parts = [typePrefix];
    if (siteName) parts.push(siteName);
    if (stem && (!siteName || stem.toLowerCase() !== siteName.toLowerCase())) parts.push(stem);
    parts.push(ts);
    return parts.join("_").replace(/_+/g, "_").slice(0, 90);
  }

  async function convertImageInBrowserCanvas(info, targetFormat) {
    const fmt = targetFormat === "jpg" ? "jpg" : "png";
    const mime = fmt === "jpg" ? "image/jpeg" : "image/png";
    const ctxInfo = extractSmartContext(info);
    const stem = sanitizeCleanStem(info.element?.getAttribute("alt") || info.url, "image", "image", ctxInfo.pageTitle, ctxInfo.siteName);
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
    if (window.__UMG_TEST_MODE__) {
      window.__UMG_LAST_DOWNLOAD__ = { url: urlOrDataUrl, filename };
      return;
    }
    if (isExtensionContextValid() && chrome.runtime.sendMessage) {
      try {
        chrome.runtime.sendMessage({
          type: "UMG_DIRECT_DOWNLOAD",
          url: urlOrDataUrl,
          filename,
        });
        return;
      } catch (_) {}
    }
    const a = document.createElement("a");
    a.href = urlOrDataUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
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
      .badge.video {
        background: rgba(244, 63, 94, 0.22);
        color: #fb7185;
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
      .btn.video-btn {
        background: linear-gradient(135deg, #e11d48, #be123c);
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
      <button class="btn" id="btn-hud-pause" style="background:#475569; padding:5px 8px;" title="ปิดพักปุ่มลอย (Alt+M)">⏸ ปิด</button>
    </div>
  `;
  document.documentElement.appendChild(hoverHost);

  // Toast & Interactive Processing Card Host (แสดงเฉพาะตอนกำลังแปลงไฟล์และซ่อนอัตโนมัติ ไม่วางค้างเกะกะบนหน้าเว็บ!)
  const toastHost = document.createElement("div");
  toastHost.id = "umg-toast-host";
  const toastShadow = toastHost.attachShadow({ mode: "open" });
  toastShadow.innerHTML = `
    <style>
      .wrapper {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
        pointer-events: none;
      }
      .status-card {
        pointer-events: auto;
        background: rgba(15, 23, 42, 0.95);
        color: #f8fafc;
        padding: 10px 14px;
        border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
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
  const btnHudPause = shadow.getElementById("btn-hud-pause");
  let statusAutoHideTimer = null;

  function showTransientNotice(message, durationMs = 2200) {
    if (statusAutoHideTimer) clearTimeout(statusAutoHideTimer);
    statusCard.style.display = "inline-flex";
    statusCard.classList.add("ready");
    statusText.textContent = message;
    cardDlBtn.style.display = "none";
    statusAutoHideTimer = setTimeout(() => {
      statusCard.style.display = "none";
    }, durationMs);
  }

  function applyEnabledState(enabled, persist = true, showNotice = false) {
    isExtensionEnabled = Boolean(enabled);
    if (!isExtensionEnabled) {
      if (currentTarget?.element) currentTarget.element.classList.remove("umg-media-hovered");
      currentTarget = null;
      lockedHudTarget = null;
      hoverHost.style.display = "none";
      if (showNotice) {
        showTransientNotice("⚪ ปิดพักโหมดดึงภาพ/วิดีโอแล้ว (กด Alt+M หรือคลิกไอคอนส่วนขยายเพื่อเปิดใหม่)");
      }
    } else if (showNotice) {
      showTransientNotice("🟢 เปิดโหมดดึงภาพ/วิดีโอแล้ว (ON)");
    }
    if (persist && isExtensionContextValid() && chrome.storage && chrome.storage.local) {
      try {
        chrome.storage.local.set({ umgEnabled: isExtensionEnabled });
        if (chrome.runtime && chrome.runtime.sendMessage) {
          chrome.runtime.sendMessage({ type: "UMG_SET_ENABLED", enabled: isExtensionEnabled });
        }
      } catch (_) {}
    }
  }

  btnHudPause.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    applyEnabledState(false, true, true);
  });

  const onKeyDown = (e) => {
    if (e.altKey && (e.key === "m" || e.key === "M" || e.code === "KeyM")) {
      e.preventDefault();
      applyEnabledState(!isExtensionEnabled, true, true);
    }
  };
  window.addEventListener("keydown", onKeyDown);

  if (isExtensionContextValid() && chrome.storage && chrome.storage.local) {
    try {
      chrome.storage.local.get({ umgEnabled: true }, (res) => {
        if (res) applyEnabledState(res.umgEnabled !== false, false, false);
      });
      chrome.storage.onChanged.addListener((changes) => {
        if (changes.umgEnabled) {
          applyEnabledState(changes.umgEnabled.newValue !== false, false, false);
        }
      });
    } catch (_) {}
  }

  hoverHost.addEventListener("mouseenter", () => {
    isMouseOnHud = true;
    if (hideTimer) {
      clearTimeout(hideTimer);
      hideTimer = null;
    }
  });

  hoverHost.addEventListener("mouseleave", () => {
    isMouseOnHud = false;
  });

  cardCloseBtn.addEventListener("click", () => {
    if (statusAutoHideTimer) clearTimeout(statusAutoHideTimer);
    statusCard.style.display = "none";
  });

  function setProcessingState(mediaType, targetFormat) {
    if (statusAutoHideTimer) clearTimeout(statusAutoHideTimer);
    const label = mediaType === "video" ? "วิดีโอเป็น .MP4" : `ภาพเป็น .${targetFormat.toUpperCase()}`;
    statusCard.style.display = "inline-flex";
    statusCard.classList.remove("ready");
    statusText.textContent = `⏳ กำลังประมวลผล${label}... รอสักครู่นะคะ`;
    cardDlBtn.style.display = "none";

    btnPrimary.classList.add("processing");
    btnPrimary.textContent = `⏳ กำลังประมวลผล...`;
    btnRedownload.style.display = "none";
  }

  function setFinishedState(downloadUrl, filename, mediaType) {
    if (statusAutoHideTimer) clearTimeout(statusAutoHideTimer);
    lastReadyDownload = { url: downloadUrl, filename };
    statusCard.style.display = "inline-flex";
    statusCard.classList.add("ready");
    statusText.textContent = `✅ ประมวลผลเสร็จแล้ว! (${filename})`;
    cardDlBtn.style.display = "inline-flex";
    cardDlBtn.textContent = "📥 กดโหลดอีกครั้ง";

    btnPrimary.classList.remove("processing");
    btnPrimary.textContent = mediaType === "video" ? "🎬 โหลด MP4" : "⬇ โหลด PNG";
    btnRedownload.style.display = "inline-flex";
    btnRedownload.textContent = `📥 ประมวลผลเสร็จแล้ว! กดโหลด (${filename})`;

    // ซ่อนการ์ดแจ้งเตือนอัตโนมัติใน 4.5 วินาที ไม่ค้างเกะกะหน้าเว็บ
    statusAutoHideTimer = setTimeout(() => {
      statusCard.style.display = "none";
    }, 4500);
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

  function collectSniffedVideoResources(videoEl = null) {
    const urls = [];
    const addCandidate = (u) => {
      if (!u || typeof u !== "string") return;
      const clean = u.replace(/\\\//g, "/").replace(/\\u002F/gi, "/").replace(/&amp;/g, "&").trim();
      if (!clean.startsWith("http") || clean.startsWith(COMPANION_URL) || clean.startsWith("blob:")) return;
      if (/\.(mp4|m3u8|webm|mov|m4v)(\?|$|#)/i.test(clean) || /(videocdn|videoplayback|icbu_vod_video|mime=video)/i.test(clean)) {
        if (!urls.includes(clean)) urls.push(clean);
      }
    };

    // 1. ค้นหาจาก React / Vue Props บนตัว <video> และกล่องครอบโดยตรง (แม่นยำที่สุดสำหรับเว็บสมัยใหม่ที่ใช้ blob:)
    if (videoEl) {
      let node = videoEl;
      for (let depth = 0; depth < 6 && node && node !== document.body; depth++) {
        try {
          const keys = Object.keys(node);
          for (const k of keys) {
            if (k.startsWith("__reactProps") || k.startsWith("__reactFiber") || k.startsWith("__vue")) {
              const str = JSON.stringify(node[k], (key, val) => (key.startsWith("_") || val instanceof Node ? undefined : val));
              if (str) {
                const matches = str.match(/https?:\\?\/\\?\/[^\s"'<>\\]+\.(?:mp4|m3u8|webm)(?:\?[^\s"'<>\\]*)?/gi) || [];
                matches.forEach(addCandidate);
              }
            }
          }
        } catch (_) {}
        node = node.parentElement;
      }
    }

    // 2. ค้นหาจาก Performance Resource Timing API ในแท็บปัจจุบัน
    try {
      const entries = performance.getEntriesByType("resource") || [];
      for (let i = entries.length - 1; i >= 0; i--) {
        addCandidate(entries[i].name || "");
      }
    } catch (_) {}

    // 3. ค้นหาจาก JSON-LD และ Inline Script ในหน้าเว็บที่ล็อกอินอยู่แล้ว
    if (urls.length === 0) {
      try {
        const scripts = document.querySelectorAll('script[type="application/ld+json"], script:not([src])');
        for (const s of scripts) {
          const txt = s.textContent || "";
          if (!txt || (!txt.includes(".mp4") && !txt.includes(".m3u8") && !txt.includes("videoUrl"))) continue;
          const matches = txt.match(/https?:\\?\/\\?\/[^\s"'<>\\]+\.(?:mp4|m3u8|webm)(?:\?[^\s"'<>\\]*)?/gi) || [];
          matches.forEach(addCandidate);
          if (urls.length >= 8) break;
        }
      } catch (_) {}
    }

    return urls.slice(0, 12);
  }

  function extractVideoDetails(videoEl) {
    // 1. ค้นหา URL ตรงจาก <source> หรือ attribute ก่อน (ถ้ามีลิงก์ http ตรง จะดีกว่า blob:)
    let bestSrc = "";
    const sources = videoEl.querySelectorAll("source");
    for (const s of sources) {
      if (s.src && !s.src.startsWith("blob:")) {
        bestSrc = s.src;
        break;
      }
    }
    if (!bestSrc) {
      const candidates = [
        videoEl.dataset?.hlsSrc,
        videoEl.dataset?.src,
        videoEl.dataset?.videoUrl,
        videoEl.dataset?.url,
        videoEl.getAttribute("src"),
        videoEl.currentSrc,
        videoEl.src,
        sources[0] && sources[0].src,
      ];
      for (const c of candidates) {
        if (c && !String(c).startsWith("blob:")) {
          bestSrc = c;
          break;
        }
      }
      if (!bestSrc) {
        bestSrc = videoEl.currentSrc || videoEl.src || (sources[0] && sources[0].src) || "";
      }
    }

    const resourceUrls = collectSniffedVideoResources(videoEl);
    if ((!bestSrc || bestSrc.startsWith("blob:")) && resourceUrls.length > 0) {
      bestSrc = resourceUrls[0];
    }

    // 2. ค้นหาลิงก์หน้าวิดีโอ (Permalink) สำหรับกรณีวิดีโอเป็น blob: (เช่น YouTube, TikTok, Reels, Facebook, X)
    let pageUrl = window.location.href;
    const linkEl = videoEl.closest("a[href]");
    if (linkEl && linkEl.href && linkEl.href.startsWith("http")) {
      pageUrl = linkEl.href;
    } else {
      let parent = videoEl.parentElement;
      for (let depth = 0; depth < 5 && parent; depth++) {
        const a = parent.querySelector(
          'a[href*="/watch"], a[href*="/reel"], a[href*="/shorts/"], a[href*="/videos/"], a[href*="/video/"], a[href*="/status/"]'
        );
        if (a && a.href) {
          pageUrl = a.href;
          break;
        }
        parent = parent.parentElement;
      }
    }

    return {
      mediaType: "video",
      url: bestSrc,
      resourceUrls,
      pageUrl,
      element: videoEl,
      label: "🎬 VIDEO → MP4",
    };
  }

  function resolveBestImageSrc(imgEl) {
    let raw = "";
    // 1. ถ้ามี srcset ให้เลือก URL ที่มีความละเอียดสูงสุดก่อน
    const srcset = imgEl.getAttribute("srcset") || imgEl.dataset?.srcset || "";
    if (srcset) {
      let maxScore = -1;
      for (const part of srcset.split(",")) {
        const tokens = part.trim().split(/\s+/);
        const candidateUrl = tokens[0];
        if (!candidateUrl) continue;
        let score = 1;
        if (tokens[1]) {
          const m = tokens[1].match(/^(\d+(?:\.\d+)?)(w|x)$/i);
          if (m) {
            score = m[2].toLowerCase() === "w" ? parseFloat(m[1]) : parseFloat(m[1]) * 1000;
          }
        }
        if (score >= maxScore) {
          maxScore = score;
          raw = candidateUrl;
        }
      }
    }
    if (!raw) {
      raw =
        imgEl.dataset?.zoomImage ||
        imgEl.dataset?.largeImage ||
        imgEl.dataset?.original ||
        imgEl.currentSrc ||
        imgEl.src ||
        imgEl.dataset?.src ||
        imgEl.dataset?.lazySrc ||
        imgEl.getAttribute("src") ||
        "";
    }
    if (!raw) return "";
    try {
      raw = new URL(raw, window.location.href).href;
    } catch (_) {}
    // 2. อัปเกรดรูปย่อของ Alibaba / AliExpress / Taobao (.jpg_80x80.jpg, .jpg_300x300q90.jpg_.webp -> .jpg) ให้ได้ภาพชัดเต็มความละเอียดทันที
    return raw
      .replace(/(\.(?:jpg|jpeg|png))_\d+x\d+[^?]*$/i, "$1")
      .replace(/_\.webp$/i, "");
  }

  // ค้นหาวิดีโอหรือรูปภาพจริงใต้ตำแหน่งเมาส์ (ให้ความสำคัญกับ <video> อันดับ 1 เสมอ!)
  function findMediaAtCursor(clientX, clientY, targetEl) {
    if (!targetEl || !targetEl.tagName) return null;

    // 1. เช็กก่อนว่า targetEl เองเป็น <video> หรือไม่
    if (targetEl.tagName.toLowerCase() === "video") {
      return extractVideoDetails(targetEl);
    }

    // 2. เช็กทุก <video> บนหน้าเว็บว่าเมาส์ (clientX, clientY) วางอยู่เหนือพื้นที่ของ <video> หรือไม่
    // (วิธีนี้ทะลุแผ่นใสบังปุ่ม Play, รูปปก Poster <img> และแถบควบคุมวิดีโอได้ 100%!)
    if (clientX > 0 || clientY > 0) {
      const allVideos = document.querySelectorAll("video");
      for (const v of allVideos) {
        const r = v.getBoundingClientRect();
        if (
          r.width >= MIN_MEDIA_SIZE &&
          r.height >= MIN_MEDIA_SIZE &&
          clientX >= r.left &&
          clientX <= r.right &&
          clientY >= r.top &&
          clientY <= r.bottom
        ) {
          return extractVideoDetails(v);
        }
      }
    }

    // 3. เช็กว่า targetEl (เช่น รูปปก Poster หรือปุ่ม Play) อยู่ข้างในกล่อง Video Player เดียวกับ <video> หรือไม่
    let container = targetEl.parentElement;
    for (let i = 0; i < 4 && container && container !== document.body; i++) {
      const r = container.getBoundingClientRect();
      if (r.width > 0 && r.width <= window.innerWidth * 0.95 && r.height <= window.innerHeight * 0.95) {
        const vidInside = container.querySelector("video");
        if (vidInside) {
          const vr = vidInside.getBoundingClientRect();
          if (vr.width >= MIN_MEDIA_SIZE && vr.height >= MIN_MEDIA_SIZE) {
            return extractVideoDetails(vidInside);
          }
        }
      }
      container = container.parentElement;
    }

    // 4. ตรวจหา "รูปภาพจริง (<img>)" ที่มีขนาด >= 72x72px (ข้ามไอคอนเล็กๆ ทั้งหมดโดยไม่หยุดลูป!)
    let bestImg = null;
    if (targetEl.tagName.toLowerCase() === "img") {
      const r = targetEl.getBoundingClientRect();
      if (r.width >= MIN_MEDIA_SIZE && r.height >= MIN_MEDIA_SIZE && resolveBestImageSrc(targetEl)) {
        bestImg = targetEl;
      }
    }

    if (!bestImg && (clientX > 0 || clientY > 0)) {
      const stacked = document.elementsFromPoint(clientX, clientY);
      for (const el of stacked) {
        if (el.tagName && el.tagName.toLowerCase() === "img") {
          const r = el.getBoundingClientRect();
          if (r.width >= MIN_MEDIA_SIZE && r.height >= MIN_MEDIA_SIZE && resolveBestImageSrc(el)) {
            bestImg = el;
            break;
          }
        }
      }
    }

    // 5. ถ้ามีแผ่นใส แว่นขยาย (Magnifier Lens) หรือกรอบสไลด์ทับรูปอยู่ ให้เช็กตำแหน่ง (clientX, clientY) เทียบกับทุก <img> บนหน้า
    if (!bestImg && (clientX > 0 || clientY > 0)) {
      const allImgs = document.querySelectorAll("img");
      let bestArea = 0;
      for (const img of allImgs) {
        const r = img.getBoundingClientRect();
        if (
          r.width >= MIN_MEDIA_SIZE &&
          r.height >= MIN_MEDIA_SIZE &&
          clientX >= r.left &&
          clientX <= r.right &&
          clientY >= r.top &&
          clientY <= r.bottom &&
          resolveBestImageSrc(img)
        ) {
          const style = window.getComputedStyle(img);
          if (style.visibility === "hidden" || style.display === "none") continue;
          // อนุญาตกรณีแว่นขยายสินค้า (Zoom Lens) ซ่อน <img> ต้นฉบับด้วย opacity: 0 ชั่วคราวตอนเอาเมาส์ชี้ (ถ้ารูปมีขนาด >= 120x120px)
          if (parseFloat(style.opacity) === 0 && (r.width < 120 || r.height < 120)) continue;
          const area = r.width * r.height;
          if (area > bestArea) {
            bestArea = area;
            bestImg = img;
          }
        }
      }
    }

    if (bestImg) {
      return {
        mediaType: "image",
        url: resolveBestImageSrc(bestImg),
        element: bestImg,
        label: "🖼 IMAGE → PNG/JPG",
      };
    }

    // 6. กรณีเว็บใช้กล่องรูปสินค้าแบบ CSS background-image ขนาดใหญ่ (>= 150x150px และไม่ใช่ปุ่ม/เมนู/พื้นหลังทั้งหน้า)
    let bgNode = targetEl;
    for (let depth = 0; depth < 2 && bgNode && bgNode !== document.body && bgNode !== document.documentElement; depth++) {
      const tag = (bgNode.tagName || "").toLowerCase();
      if (["button", "a", "input", "select", "textarea", "nav", "header", "footer", "aside"].includes(tag)) break;
      const r = bgNode.getBoundingClientRect();
      if (r.width >= 150 && r.height >= 150 && r.width <= window.innerWidth * 0.85 && r.height <= window.innerHeight * 0.85) {
        const bg = window.getComputedStyle(bgNode).backgroundImage || "";
        const m = bg.match(/url\(["']?(https?:\/\/[^"')]+)["']?\)/i);
        if (m && m[1] && /\.(jpg|jpeg|png|webp|avif)(\?|$)/i.test(m[1]) && !bgNode.querySelector("button, input, video")) {
          const cleanBgUrl = m[1].replace(/(\.(?:jpg|jpeg|png))_\d+x\d+[^?]*$/i, "$1").replace(/_\.webp$/i, "");
          return {
            mediaType: "image",
            url: cleanBgUrl,
            element: bgNode,
            label: "🖼 IMAGE → PNG/JPG",
          };
        }
      }
      bgNode = bgNode.parentElement;
    }

    return null;
  }

  async function tryCaptureBrowserImageBase64(url) {
    if (!url || url.startsWith("data:")) return url || "";
    try {
      const res = await fetch(url, { credentials: "include", mode: "cors" });
      if (!res.ok) return "";
      const blob = await res.blob();
      if (!blob || blob.size < 100 || blob.size > 35 * 1024 * 1024) return "";
      if (blob.type && !blob.type.startsWith("image/") && blob.type !== "application/octet-stream") return "";
      return await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(typeof reader.result === "string" ? reader.result : "");
        reader.onerror = () => resolve("");
        reader.readAsDataURL(blob);
      });
    } catch (_) {
      return "";
    }
  }

  let isProcessingDownload = false;
  let lastMouseX = 0;
  let lastMouseY = 0;

  function clearAllHoveredOutlines() {
    if (currentTarget?.element) currentTarget.element.classList.remove("umg-media-hovered");
    document.querySelectorAll(".umg-media-hovered").forEach((el) => el.classList.remove("umg-media-hovered"));
  }

  async function triggerConvertAndDownload(info, targetFormat) {
    if (!info || isProcessingDownload) return;
    isProcessingDownload = true;
    try {
      setProcessingState(info.mediaType, targetFormat);

      const ctxInfo = extractSmartContext(info);
      const payload = {
        url: info.url || "",
        resourceUrls: info.resourceUrls || collectSniffedVideoResources(),
        pageUrl: info.pageUrl || window.location.href,
        pageTitle: ctxInfo.pageTitle || document.title || "",
        siteName: ctxInfo.siteName || "",
        base64Data: info.base64Data || "",
        svgText: info.svgText || "",
        targetFormat,
        filename:
          info.element?.getAttribute("alt") ||
          info.element?.dataset?.name ||
          ctxInfo.pageTitle ||
          info.url ||
          document.title ||
          `media_${Date.now()}`,
      };

      // สำหรับรูปภาพ ลองดึง Bytes จาก Browser Session ก่อน (ช่วยทะลุเว็บที่บล็อก Hotlink 403 ได้ 100%)
      if (info.mediaType === "image" && !payload.base64Data && !payload.svgText && payload.url) {
        payload.base64Data = await tryCaptureBrowserImageBase64(payload.url);
      }

      // ถ้าเป็นวิดีโอแบบ blob: ลองดึง Blob ในเบราว์เซอร์ (รองรับแม้ไม่มี blob.type)
      if (payload.url && payload.url.startsWith("blob:") && !payload.base64Data) {
        try {
          const res = await fetch(payload.url);
          const blob = await res.blob();
          if (blob.size > 500 && blob.size < 65 * 1024 * 1024) {
            payload.base64Data = await new Promise((resolve) => {
              const reader = new FileReader();
              reader.onloadend = () => resolve(reader.result);
              reader.readAsDataURL(blob);
            });
          }
        } catch (_) {
          // MSE Blob Stream — ใช้ resourceUrls / sniffedUrl / pageUrl
        }
      }

      // 1. ส่งให้ Background Service Worker (เฉพาะกรณีข้อมูลไม่ใหญ่เกินขีดจำกัด IPC ของ Chrome)
      const ipcSafeBase64 = payload.base64Data && payload.base64Data.length < 12 * 1024 * 1024 ? payload.base64Data : "";
      if (isExtensionContextValid() && chrome.runtime.sendMessage && !info.svgText && (!payload.base64Data || ipcSafeBase64)) {
        try {
          const swRes = await new Promise((resolve) => {
            chrome.runtime.sendMessage(
              {
                type: "UMG_SMART_CONVERT_AND_DOWNLOAD",
                payload: {
                  mediaType: info.mediaType,
                  url: payload.url,
                  resourceUrls: payload.resourceUrls,
                  pageUrl: payload.pageUrl,
                  pageTitle: payload.pageTitle,
                  siteName: payload.siteName,
                  base64Data: ipcSafeBase64,
                  svgText: payload.svgText,
                  targetFormat,
                  filename: payload.filename,
                  autoDownload: true,
                },
              },
              (res) => {
                void chrome.runtime?.lastError;
                resolve(res);
              }
            );
          });
          if (swRes && swRes.ok) {
            setFinishedState(swRes.downloadUrl, swRes.filename, info.mediaType);
            return;
          }
        } catch (_) {}
      }

      // 2. เรียก Companion Server โดยตรง (รองรับไฟล์ใหญ่ไม่จำกัดขนาด และทำงานได้แม้เพิ่งกด Reload Extension!)
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

      // 3. Fallback แปลงใน Browser Canvas สำหรับรูปภาพ
      try {
        if (info.mediaType === "image") {
          const converted = await convertImageInBrowserCanvas(info, targetFormat);
          triggerBrowserDownload(converted.dataUrl, converted.filename);
          setFinishedState(converted.dataUrl, converted.filename, info.mediaType);
        } else {
          statusText.textContent = "❌ ไม่สามารถดึงสตรีมวิดีโอนี้ได้ กรุณากดเล่นวิดีโอสักครู่แล้วกดโหลดอีกครั้งค่ะ";
          btnPrimary.classList.remove("processing");
        }
      } catch (err) {
        statusText.textContent = `❌ ประมวลผลไม่สำเร็จ: ${err.message}`;
        btnPrimary.classList.remove("processing");
      }
    } finally {
      isProcessingDownload = false;
    }
  }

  btnPrimary.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    const target = currentTarget || lockedHudTarget;
    if (!target) return;
    const fmt = target.mediaType === "video" ? "mp4" : "png";
    triggerConvertAndDownload(target, fmt);
  });

  btnSecondary.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    const target = currentTarget || lockedHudTarget;
    if (!target) return;
    triggerConvertAndDownload(target, "jpg");
  });

  function positionHudForElement(el) {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    // วางปุ่มให้อยู่ในพื้นที่ที่มองเห็นได้เสมอ (ไม่จมใต้แถบเมนูด้านบนของเว็บ)
    const minTop = rect.top < 52 && rect.bottom > 110 ? 58 : 8;
    const topPos = Math.min(Math.max(minTop, rect.top + 10), Math.max(minTop, rect.bottom - 44));
    const leftPos = Math.min(Math.max(8, rect.left + 10), Math.max(8, window.innerWidth - 280));
    hoverHost.style.top = `${topPos}px`;
    hoverHost.style.left = `${leftPos}px`;
  }

  // ซ่อนหรือขยับปุ่มลอยทันทีเมื่อผู้ใช้เลื่อนหน้าจอ (Scroll) หรือย่อขยายหน้าจอ (Resize) ไม่ให้ปุ่มลอยค้างกลางอากาศ!
  const onScrollOrResize = () => {
    if (!currentTarget || !currentTarget.element) {
      if (hoverHost.style.display !== "none" && !isMouseOnHud) {
        hoverHost.style.display = "none";
      }
      return;
    }
    if (!document.contains(currentTarget.element)) {
      clearAllHoveredOutlines();
      currentTarget = null;
      hoverHost.style.display = "none";
      return;
    }
    const r = currentTarget.element.getBoundingClientRect();
    const outOfViewport = r.bottom < 40 || r.top > window.innerHeight - 40 || r.right < 40 || r.left > window.innerWidth - 40;
    const cursorLeftElement =
      !isMouseOnHud &&
      (lastMouseX > 0 || lastMouseY > 0) &&
      (lastMouseX < r.left - 24 || lastMouseX > r.right + 24 || lastMouseY < r.top - 24 || lastMouseY > r.bottom + 24);
    if (outOfViewport || cursorLeftElement) {
      clearAllHoveredOutlines();
      currentTarget = null;
      hoverHost.style.display = "none";
    } else {
      positionHudForElement(currentTarget.element);
    }
  };

  const onVisibilityOrBlur = () => {
    if (document.hidden) {
      clearAllHoveredOutlines();
      currentTarget = null;
      isMouseOnHud = false;
      hoverHost.style.display = "none";
    }
  };

  const onMouseMove = (e) => {
    if (!isExtensionEnabled) return;
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
    const path = typeof e.composedPath === "function" ? e.composedPath() : [];
    if (
      isMouseOnHud ||
      e.target === hoverHost ||
      hoverHost.contains(e.target) ||
      e.target === toastHost ||
      toastHost.contains(e.target) ||
      path.includes(hoverHost) ||
      path.includes(toastHost)
    ) {
      if (hideTimer) {
        clearTimeout(hideTimer);
        hideTimer = null;
      }
      return;
    }

    const info = findMediaAtCursor(e.clientX, e.clientY, e.target);
    if (!info) {
      if (currentTarget && !hideTimer) {
        hideTimer = setTimeout(() => {
          if (isMouseOnHud) {
            hideTimer = null;
            return;
          }
          clearAllHoveredOutlines();
          currentTarget = null;
          hoverHost.style.display = "none";
          hideTimer = null;
        }, 550);
      }
      return;
    }

    if (hideTimer) {
      clearTimeout(hideTimer);
      hideTimer = null;
    }

    if (currentTarget?.element && currentTarget.element !== info.element) {
      clearAllHoveredOutlines();
      btnRedownload.style.display = "none";
    }

    currentTarget = info;
    lockedHudTarget = info;
    info.element.classList.add("umg-media-hovered");

    badgeEl.textContent = info.label;
    if (info.mediaType === "video") {
      badgeEl.classList.add("video");
      btnPrimary.classList.add("video-btn");
      if (!btnPrimary.classList.contains("processing")) {
        btnPrimary.textContent = "🎬 โหลดวิดีโอ MP4";
      }
      btnSecondary.style.display = "none";
    } else {
      badgeEl.classList.remove("video");
      btnPrimary.classList.remove("video-btn");
      if (!btnPrimary.classList.contains("processing")) {
        btnPrimary.textContent = "⬇ โหลด PNG";
      }
      btnSecondary.style.display = "inline-flex";
      btnSecondary.textContent = "⬇ โหลด JPG";
    }

    positionHudForElement(info.element);
    hoverHost.style.display = "block";
  };

  document.addEventListener("mousemove", onMouseMove, { passive: true });
  window.addEventListener("scroll", onScrollOrResize, { passive: true, capture: true });
  window.addEventListener("resize", onScrollOrResize, { passive: true });
  document.addEventListener("visibilitychange", onVisibilityOrBlur);

  window.__UMG_CLEANUP__ = () => {
    if (statusAutoHideTimer) clearTimeout(statusAutoHideTimer);
    if (hideTimer) clearTimeout(hideTimer);
    clearAllHoveredOutlines();
    document.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("scroll", onScrollOrResize, { capture: true });
    window.removeEventListener("resize", onScrollOrResize);
    document.removeEventListener("visibilitychange", onVisibilityOrBlur);
    window.removeEventListener("keydown", onKeyDown);
    hoverHost.remove();
    toastHost.remove();
  };

  if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
      if (msg.type === "UMG_SET_ENABLED") {
        applyEnabledState(Boolean(msg.enabled), false, false);
        sendResponse({ ok: true, enabled: isExtensionEnabled });
        return true;
      }
      if (msg.type === "UMG_SHOW_PROCESSING") {
        setProcessingState(msg.mediaType || "video", msg.targetFormat || "mp4");
        sendResponse({ ok: true });
        return true;
      }
      if (msg.type === "UMG_SHOW_FINISHED") {
        setFinishedState(msg.downloadUrl || "", msg.filename || "media", msg.mediaType || "video");
        sendResponse({ ok: true });
        return true;
      }
      if (msg.type === "UMG_SCAN_PAGE") {
        const items = [];
        document.querySelectorAll("video").forEach((v, idx) => {
          const r = v.getBoundingClientRect();
          if (r.width >= MIN_MEDIA_SIZE && r.height >= MIN_MEDIA_SIZE) {
            const info = extractVideoDetails(v);
            items.push({ index: idx, mediaType: "video", url: info.url, pageUrl: info.pageUrl, label: info.label });
          }
        });
        document.querySelectorAll("img").forEach((img, idx) => {
          const r = img.getBoundingClientRect();
          if (r.width >= MIN_MEDIA_SIZE && r.height >= MIN_MEDIA_SIZE && (img.currentSrc || img.src)) {
            items.push({ index: 1000 + idx, mediaType: "image", url: resolveBestImageSrc(img), label: "🖼 IMAGE → PNG/JPG" });
          }
        });
        sendResponse({ ok: true, items });
        return true;
      }
    });
  }
})();
