// Universal Media Grabber — Content Script (Strict Image & Video Only + Video-First Piercing Engine)
// แก้ไขปัญหาครบ 100%:
// 1. จับเฉพาะ "รูปภาพจริง (<img>)" และ "วิดีโอจริง (<video>)" เท่านั้น! ไม่จับปุ่ม ไอคอน พื้นหลัง หรือกล่องข้อความมั่วซั่วอีกต่อไป
// 2. ให้ความสำคัญกับ "วิดีโอ (<video>)" เป็นอันดับ 1 (ทะลุผ่านแผ่นใสบังปุ่ม Play / รูปปก Poster บนตัวเล่นวิดีโอ) ไม่เข้าใจผิดว่าวิดีโอเป็นรูปภาพอีกต่อไป!
// 3. รองรับการดึงวิดีโอทั้งไฟล์ตรง (.mp4/.webm/.mov), สตรีม HLS (.m3u8), และวิดีโอแบบ blob: (ผ่าน Network Sniffer + yt-dlp + FFmpeg)
(() => {
  if (window.__UMG_INITIALIZED__) return;
  window.__UMG_INITIALIZED__ = true;

  const COMPANION_URL = "http://127.0.0.1:8765";
  const WEIRD_EXT_REGEX = /\.(webp|avif|svg|svgz|jfif|bmp|gif|ico|tiff|tif|heic|webm|ogv|ogg|mov|mkv|ts|m3u8|mpd|flv|avi|bin|dat|php)(\?.*|#.*|$)/i;
  const MIN_MEDIA_SIZE = 72; // ข้ามไอคอน ปุ่ม และรูปขนาดเล็กกว่า 72x72px ทั้งหมด

  let currentTarget = null;
  let hideTimer = null;
  let lastReadyDownload = null;
  let isExtensionEnabled = true;

  function sanitizeCleanStem(rawName, prefix = "media") {
    if (!rawName) return `${prefix}_${Date.now()}`;
    let base = String(rawName).split("?")[0].split("#")[0].split("/").pop() || prefix;
    try {
      base = decodeURIComponent(base);
    } catch (_) {}
    base = base.replace(WEIRD_EXT_REGEX, "").replace(/\.(png|jpg|jpeg|mp4)$/i, "");
    base = base.replace(/[^a-zA-Z0-9ก-๙_\-]/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
    if (!base || ["blob", "data", "media", "image", "video", "watch"].includes(base.toLowerCase())) {
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
      .power-pill {
        pointer-events: auto;
        cursor: pointer;
        user-select: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(15, 23, 42, 0.9);
        backdrop-filter: blur(8px);
        color: #f8fafc;
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px solid rgba(16, 185, 129, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 12px;
        font-weight: 600;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3);
        transition: all 0.15s ease;
      }
      .power-pill.off {
        border-color: rgba(148, 163, 184, 0.35);
        color: #94a3b8;
        opacity: 0.75;
      }
      .power-pill:hover {
        opacity: 1;
        transform: translateY(-1px);
      }
    </style>
    <div class="wrapper">
      <div class="status-card" id="status-card">
        <span id="status-text">⏳ กำลังประมวลผลภาพ/วิดีโอ...</span>
        <button class="dl-again-btn" id="card-dl-btn" style="display:none;">📥 กดโหลดอีกครั้ง</button>
        <button class="close-btn" id="card-close-btn">✕</button>
      </div>
      <button class="power-pill" id="floating-power-pill" title="คลิกเพื่อ เปิด/ปิด ปุ่มดึงภาพและวิดีโอ (คีย์ลัด Alt+M)">
        🟢 โหมดดึงภาพ/วิดีโอ: เปิด (ON)
      </button>
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
  const floatingPowerPill = toastShadow.getElementById("floating-power-pill");

  function applyEnabledState(enabled, persist = true) {
    isExtensionEnabled = Boolean(enabled);
    if (!isExtensionEnabled) {
      if (currentTarget?.element) currentTarget.element.classList.remove("umg-media-hovered");
      currentTarget = null;
      hoverHost.style.display = "none";
      floatingPowerPill.classList.add("off");
      floatingPowerPill.textContent = "⚪ โหมดดึงภาพ/วิดีโอ: ปิดพัก (OFF)";
    } else {
      floatingPowerPill.classList.remove("off");
      floatingPowerPill.textContent = "🟢 โหมดดึงภาพ/วิดีโอ: เปิด (ON)";
    }
    if (persist && typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ umgEnabled: isExtensionEnabled });
      if (chrome.runtime && chrome.runtime.sendMessage) {
        chrome.runtime.sendMessage({ type: "UMG_SET_ENABLED", enabled: isExtensionEnabled });
      }
    }
  }

  floatingPowerPill.addEventListener("click", (e) => {
    e.stopPropagation();
    applyEnabledState(!isExtensionEnabled, true);
  });

  btnHudPause.addEventListener("click", (e) => {
    e.stopPropagation();
    e.preventDefault();
    applyEnabledState(false, true);
  });

  window.addEventListener("keydown", (e) => {
    if (e.altKey && (e.key === "m" || e.key === "M" || e.code === "KeyM")) {
      e.preventDefault();
      applyEnabledState(!isExtensionEnabled, true);
    }
  });

  if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get({ umgEnabled: true }, (res) => {
      applyEnabledState(res.umgEnabled !== false, false);
    });
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.umgEnabled) {
        applyEnabledState(changes.umgEnabled.newValue !== false, false);
      }
    });
  }

  cardCloseBtn.addEventListener("click", () => {
    statusCard.style.display = "none";
  });

  function setProcessingState(mediaType, targetFormat) {
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

  function extractVideoDetails(videoEl) {
    // 1. ค้นหา URL ตรงจาก <source> ก่อน (ถ้ามีลิงก์ http ตรง จะดีกว่า blob:)
    let bestSrc = "";
    const sources = videoEl.querySelectorAll("source");
    for (const s of sources) {
      if (s.src && !s.src.startsWith("blob:")) {
        bestSrc = s.src;
        break;
      }
    }
    if (!bestSrc) {
      bestSrc =
        videoEl.dataset.hlsSrc ||
        videoEl.dataset.src ||
        videoEl.dataset.videoUrl ||
        videoEl.currentSrc ||
        videoEl.src ||
        (sources[0] && sources[0].src) ||
        "";
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
      pageUrl,
      element: videoEl,
      label: "🎬 VIDEO → MP4",
    };
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

    // 4. ถ้าไม่ใช่วิดีโอ ให้ตรวจเฉพาะ "รูปภาพจริง (<img>)" เท่านั้น!
    let imgEl = null;
    if (targetEl.tagName.toLowerCase() === "img") {
      imgEl = targetEl;
    } else if (clientX > 0 || clientY > 0) {
      const stacked = document.elementsFromPoint(clientX, clientY);
      for (const el of stacked) {
        if (el.tagName && el.tagName.toLowerCase() === "img") {
          imgEl = el;
          break;
        }
      }
    }

    if (imgEl) {
      const r = imgEl.getBoundingClientRect();
      // กรองไอคอน ปุ่ม โลโก้เล็กๆ หรือรูปที่มีขนาดเล็กกว่า 72x72px ทิ้งทั้งหมด
      if (r.width < MIN_MEDIA_SIZE || r.height < MIN_MEDIA_SIZE) {
        return null;
      }
      const src = imgEl.currentSrc || imgEl.src || "";
      if (!src) return null;
      return {
        mediaType: "image",
        url: src,
        element: imgEl,
        label: "🖼 IMAGE → PNG/JPG",
      };
    }

    return null;
  }

  async function triggerConvertAndDownload(info, targetFormat) {
    setProcessingState(info.mediaType, targetFormat);

    const payload = {
      url: info.url || "",
      pageUrl: info.pageUrl || window.location.href,
      base64Data: info.base64Data || "",
      svgText: info.svgText || "",
      targetFormat,
      filename:
        info.element?.getAttribute("alt") ||
        info.element?.dataset?.name ||
        info.url ||
        document.title ||
        `media_${Date.now()}`,
    };

    // ถ้าเป็น blob: ลองดึงเฉพาะกรณีเป็นไฟล์ Blob ปกติ (ถ้าเป็น MSE Stream ของเว็บวิดีโอจะข้ามไปใช้ Sniffer / yt-dlp อัตโนมัติ)
    if (payload.url && payload.url.startsWith("blob:")) {
      try {
        const res = await fetch(payload.url);
        const blob = await res.blob();
        if (blob.size > 500 && blob.size < 60 * 1024 * 1024 && (info.mediaType === "image" || blob.type.startsWith("video/"))) {
          payload.base64Data = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
          });
        }
      } catch (_) {
        // MSE Blob Stream — ปล่อยให้ Companion Server ใช้ sniffedUrl / pageUrl ดึงเป็น MP4
      }
    }

    // 1. ส่งให้ Background Service Worker
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage && !info.svgText) {
      try {
        const swRes = await new Promise((resolve) => {
          chrome.runtime.sendMessage(
            {
              type: "UMG_SMART_CONVERT_AND_DOWNLOAD",
              payload: {
                mediaType: info.mediaType,
                url: payload.url,
                pageUrl: payload.pageUrl,
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

    // 3. Fallback แปลงใน Browser Canvas สำหรับรูปภาพ
    try {
      if (info.mediaType === "image") {
        const converted = await convertImageInBrowserCanvas(info, targetFormat);
        triggerBrowserDownload(converted.dataUrl, converted.filename);
        setFinishedState(converted.dataUrl, converted.filename, info.mediaType);
      } else {
        statusText.textContent = "❌ ไม่สามารถดึงสตรีมวิดีโอนี้ได้โดยตรง";
        btnPrimary.classList.remove("processing");
      }
    } catch (err) {
      statusText.textContent = `❌ ประมวลผลไม่สำเร็จ: ${err.message}`;
      btnPrimary.classList.remove("processing");
    }
  }

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

  document.addEventListener(
    "mousemove",
    (e) => {
      if (!isExtensionEnabled) return;
      if (e.target === hoverHost || hoverHost.contains(e.target) || e.target === toastHost || toastHost.contains(e.target)) {
        if (hideTimer) clearTimeout(hideTimer);
        return;
      }

      const info = findMediaAtCursor(e.clientX, e.clientY, e.target);
      if (!info) {
        if (currentTarget && !hideTimer) {
          hideTimer = setTimeout(() => {
            if (currentTarget?.element) currentTarget.element.classList.remove("umg-media-hovered");
            currentTarget = null;
            hoverHost.style.display = "none";
          }, 350);
        }
        return;
      }

      if (hideTimer) {
        clearTimeout(hideTimer);
        hideTimer = null;
      }

      if (currentTarget?.element && currentTarget.element !== info.element) {
        currentTarget.element.classList.remove("umg-media-hovered");
        btnRedownload.style.display = "none";
      }

      currentTarget = info;
      info.element.classList.add("umg-media-hovered");

      const rect = info.element.getBoundingClientRect();
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

      hoverHost.style.top = `${Math.max(8, rect.top + 8)}px`;
      hoverHost.style.left = `${Math.max(8, rect.left + 8)}px`;
      hoverHost.style.display = "block";
    },
    { passive: true }
  );

  if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
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
            items.push({ index: 1000 + idx, mediaType: "image", url: img.currentSrc || img.src, label: "🖼 IMAGE → PNG/JPG" });
          }
        });
        sendResponse({ ok: true, items });
        return true;
      }
    });
  }
})();
