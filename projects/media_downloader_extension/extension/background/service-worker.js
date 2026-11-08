// Universal Media Grabber — Manifest V3 Background Service Worker
// 1. ดักจับ URL สตรีมวิดีโอจริงในแต่ละแท็บ (webRequest Sniffer) สำหรับวิดีโอแบบ blob: / HLS (.m3u8) / MP4
// 2. สั่งปลุก Companion Server (127.0.0.1:8765) อัตโนมัติ (รองรับทั้ง FFmpeg + yt-dlp)
// 3. รองรับโหมด Standalone (OffscreenCanvas) สำหรับรูปภาพทุกชนิด

const COMPANION_URL = "http://127.0.0.1:8765";
const NATIVE_HOST = "com.meuu.umg_companion";
const WEIRD_EXT_REGEX = /\.(webp|avif|svg|svgz|jfif|bmp|gif|ico|tiff|tif|heic|webm|ogv|ogg|mov|mkv|ts|m3u8|mpd|flv|avi|bin|dat|php)(\?.*|#.*|$)/i;
const VIDEO_STREAM_REGEX = /\.(mp4|m3u8|webm|mov|mkv|ogv|ts|m4v)(\?.*|#.*|$)/i;

// เก็บ URL สตรีมวิดีโอล่าสุดที่ดักจับได้ของแต่ละ Tab
const tabSniffedVideoMap = new Map();

if (chrome.webRequest && chrome.webRequest.onBeforeRequest) {
  chrome.webRequest.onBeforeRequest.addListener(
    (details) => {
      if (details.tabId < 0 || !details.url) return;
      if (details.url.startsWith(COMPANION_URL)) return;
      if (details.type === "media" || VIDEO_STREAM_REGEX.test(details.url)) {
        // ข้ามชิ้นส่วนย่อยเล็กๆ ถ้ามี .m3u8 อยู่แล้ว
        const prev = tabSniffedVideoMap.get(details.tabId) || "";
        if (prev.includes(".m3u8") && details.url.includes(".ts")) return;
        tabSniffedVideoMap.set(details.tabId, details.url);
      }
    },
    { urls: ["<all_urls>"] }
  );
}

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

function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

async function isCompanionAlive() {
  try {
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 900);
    const res = await fetch(`${COMPANION_URL}/api/health`, { signal: controller.signal });
    clearTimeout(t);
    const data = await res.json();
    return Boolean(data && data.ok);
  } catch (_) {
    return false;
  }
}

async function autoWakeupCompanionServer() {
  if (await isCompanionAlive()) return true;

  if (chrome.runtime && chrome.runtime.sendNativeMessage) {
    try {
      await new Promise((resolve) => {
        chrome.runtime.sendNativeMessage(NATIVE_HOST, { action: "ensure" }, () => {
          void chrome.runtime.lastError;
          resolve();
        });
      });
    } catch (_) {}
  }

  for (let i = 0; i < 10; i++) {
    if (await isCompanionAlive()) return true;
    await new Promise((r) => setTimeout(r, 250));
  }
  return false;
}

async function convertImageStandaloneInWorker(urlOrDataUrl, targetFormat, rawFilename) {
  const fmt = targetFormat === "jpg" ? "jpg" : "png";
  const mime = fmt === "jpg" ? "image/jpeg" : "image/png";
  const filename = `${sanitizeCleanStem(rawFilename || urlOrDataUrl, "image")}.${fmt}`;

  const response = await fetch(urlOrDataUrl);
  const srcBlob = await response.blob();
  const bitmap = await createImageBitmap(srcBlob);

  const canvas = new OffscreenCanvas(bitmap.width || 800, bitmap.height || 600);
  const ctx = canvas.getContext("2d");
  if (fmt === "jpg") {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
  ctx.drawImage(bitmap, 0, 0);
  bitmap.close();

  const outBlob = await canvas.convertToBlob({ type: mime, quality: 0.95 });
  const buf = await outBlob.arrayBuffer();
  const dataUrl = `data:${mime};base64,${arrayBufferToBase64(buf)}`;
  return { dataUrl, filename };
}

async function handleSmartConvertAndDownload(payload, senderTabId = -1) {
  const { mediaType, url, pageUrl, pageTitle = "", siteName = "", base64Data, svgText, targetFormat, filename, autoDownload = true } = payload;
  const fmt = mediaType === "video" ? "mp4" : (targetFormat === "jpg" ? "jpg" : "png");
  const endpoint = mediaType === "video" ? "/api/convert/video" : "/api/convert/image";
  const sniffedUrl = senderTabId >= 0 ? (tabSniffedVideoMap.get(senderTabId) || "") : "";

  const alive = await autoWakeupCompanionServer();
  if (alive) {
    try {
      const resp = await fetch(`${COMPANION_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          pageUrl,
          pageTitle,
          siteName,
          sniffedUrl,
          base64Data,
          svgText,
          targetFormat: fmt,
          filename,
        }),
      });
      const data = await resp.json();
      if (data && data.ok && data.downloadUrl) {
        if (autoDownload) {
          await chrome.downloads.download({
            url: data.downloadUrl,
            filename: data.filename,
            conflictAction: "uniquify",
            saveAs: false,
          });
        }
        return {
          ok: true,
          filename: data.filename,
          downloadUrl: data.downloadUrl,
          mode: "companion_auto",
        };
      }
    } catch (_) {}
  }

  if (mediaType === "image") {
    const inputUrl = base64Data || url;
    const converted = await convertImageStandaloneInWorker(inputUrl, fmt, pageTitle || filename);
    if (autoDownload) {
      await chrome.downloads.download({
        url: converted.dataUrl,
        filename: converted.filename,
        conflictAction: "uniquify",
        saveAs: false,
      });
    }
    return {
      ok: true,
      filename: converted.filename,
      downloadUrl: converted.dataUrl,
      mode: "standalone",
    };
  } else {
    const cleanMp4 = `${sanitizeCleanStem(pageTitle || filename || url || pageUrl, "วิดีโอ")}.mp4`;
    const downloadSource = base64Data || (url && !url.startsWith("blob:") ? url : sniffedUrl);
    if (!downloadSource) {
      throw new Error("วิดีโอนี้เป็นสตรีมเข้ารหัส กรุณารอเซิร์ฟเวอร์ประมวลผล");
    }
    if (autoDownload) {
      await chrome.downloads.download({
        url: downloadSource,
        filename: cleanMp4,
        conflictAction: "uniquify",
        saveAs: false,
      });
    }
    return {
      ok: true,
      filename: cleanMp4,
      downloadUrl: downloadSource,
      mode: "standalone",
    };
  }
}

function updateBadge(enabled) {
  if (!chrome.action) return;
  chrome.action.setBadgeText({ text: enabled ? "ON" : "OFF" });
  chrome.action.setBadgeBackgroundColor({ color: enabled ? "#10b981" : "#64748b" });
}

chrome.runtime.onInstalled.addListener(() => {
  autoWakeupCompanionServer();
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get({ umgEnabled: true }, (res) => {
      updateBadge(res.umgEnabled !== false);
    });
  }
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "umg-save-png",
      title: "🖼 ประมวลผลและโหลดภาพเป็น (.PNG)",
      contexts: ["image"],
    });
    chrome.contextMenus.create({
      id: "umg-save-jpg",
      title: "📷 ประมวลผลและโหลดภาพเป็น (.JPG)",
      contexts: ["image"],
    });
    chrome.contextMenus.create({
      id: "umg-save-mp4",
      title: "🎬 ประมวลผลและโหลดวิดีโอเป็น (.MP4)",
      contexts: ["video", "audio"],
    });
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const tabId = tab ? tab.id : -1;
  const tabTitle = (tab && tab.title) || "";
  const tabUrl = info.pageUrl || (tab && tab.url) || "";
  if (info.menuItemId === "umg-save-png" || info.menuItemId === "umg-save-jpg") {
    if (!info.srcUrl) return;
    handleSmartConvertAndDownload(
      {
        mediaType: "image",
        url: info.srcUrl,
        pageUrl: tabUrl,
        pageTitle: tabTitle,
        targetFormat: info.menuItemId === "umg-save-jpg" ? "jpg" : "png",
        filename: tabTitle || info.srcUrl,
      },
      tabId
    );
  } else if (info.menuItemId === "umg-save-mp4") {
    handleSmartConvertAndDownload(
      {
        mediaType: "video",
        url: info.srcUrl || "",
        pageUrl: tabUrl,
        pageTitle: tabTitle,
        targetFormat: "mp4",
        filename: tabTitle || info.srcUrl || tabUrl,
      },
      tabId
    );
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const tabId = sender && sender.tab ? sender.tab.id : -1;
  if (msg.type === "UMG_DIRECT_DOWNLOAD" && msg.url) {
    chrome.downloads.download(
      {
        url: msg.url,
        filename: msg.filename || undefined,
        conflictAction: "uniquify",
        saveAs: false,
      },
      (downloadId) => {
        sendResponse({ ok: true, downloadId });
      }
    );
    return true;
  }

  if (msg.type === "UMG_SET_ENABLED") {
    const enabled = Boolean(msg.enabled);
    updateBadge(enabled);
    if (chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ umgEnabled: enabled });
    }
    sendResponse({ ok: true, enabled });
    return true;
  }

  if (msg.type === "UMG_SMART_CONVERT_AND_DOWNLOAD") {
    handleSmartConvertAndDownload(msg.payload, tabId)
      .then((res) => sendResponse(res))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }
});
