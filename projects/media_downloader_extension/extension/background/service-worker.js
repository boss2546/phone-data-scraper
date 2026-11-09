// Universal Media Grabber — Manifest V3 Background Service Worker
// 1. ดักจับ URL สตรีมวิดีโอจริงในแต่ละแท็บ (webRequest Sniffer) สำหรับวิดีโอแบบ blob: / HLS (.m3u8) / MP4
// 2. สั่งปลุก Companion Server (127.0.0.1:8765) อัตโนมัติ (รองรับทั้ง FFmpeg + yt-dlp)
// 3. รองรับโหมด Standalone (OffscreenCanvas) สำหรับรูปภาพทุกชนิด

const COMPANION_URL = "http://127.0.0.1:8765";
const NATIVE_HOST = "com.meuu.umg_companion";
const WEIRD_EXT_REGEX = /\.(webp|avif|svg|svgz|jfif|bmp|gif|ico|tiff|tif|heic|webm|ogv|ogg|mov|mkv|ts|m3u8|mpd|flv|avi|bin|dat|php)(\?.*|#.*|$)/i;
const VIDEO_STREAM_REGEX = /\.(mp4|m3u8|webm|mov|mkv|ogv|ts|m4v)(\?.*|#.*|$)/i;

// เก็บรายการ URL สตรีมวิดีโอล่าสุดที่ดักจับได้ของแต่ละ Tab (เก็บสูงสุด 12 รายการต่อแท็บ + ล้างเมื่อปิดแท็บ)
const tabSniffedVideoMap = new Map();

if (chrome.webRequest && chrome.webRequest.onBeforeRequest) {
  chrome.webRequest.onBeforeRequest.addListener(
    (details) => {
      if (details.tabId < 0 || !details.url) return;
      if (details.url.startsWith(COMPANION_URL)) return;
      if (details.type === "media" || VIDEO_STREAM_REGEX.test(details.url)) {
        const list = tabSniffedVideoMap.get(details.tabId) || [];
        // ข้ามชิ้นส่วน .ts ย่อยๆ ถ้ามี .m3u8 อยู่แล้วในรายการ
        if (details.url.includes(".ts") && list.some((u) => u.includes(".m3u8"))) return;
        const filtered = list.filter((u) => u !== details.url);
        filtered.unshift(details.url);
        tabSniffedVideoMap.set(details.tabId, filtered.slice(0, 12));
      }
    },
    { urls: ["<all_urls>"] }
  );
}

if (chrome.tabs && chrome.tabs.onRemoved) {
  chrome.tabs.onRemoved.addListener((tabId) => {
    tabSniffedVideoMap.delete(tabId);
  });
}

// เก็บชื่อไฟล์ที่ต้องการบังคับใช้เมื่อสั่ง chrome.downloads.download
const pendingDownloadFilenameById = new Map();

if (chrome.downloads && chrome.downloads.onDeterminingFilename) {
  chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
    const forced = pendingDownloadFilenameById.get(item.id);
    if (forced) {
      pendingDownloadFilenameById.delete(item.id);
      suggest({ filename: forced, conflictAction: "uniquify" });
      return;
    }
    suggest();
  });
}

function triggerManagedChromeDownload(url, filename) {
  return new Promise((resolve) => {
    chrome.downloads.download(
      {
        url,
        filename: filename || undefined,
        conflictAction: "uniquify",
        saveAs: false,
      },
      (downloadId) => {
        if (downloadId && filename) {
          pendingDownloadFilenameById.set(downloadId, filename);
          setTimeout(() => pendingDownloadFilenameById.delete(downloadId), 30000);
        }
        resolve(downloadId);
      }
    );
  });
}

function formatNowTimestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function extractSiteBrand(urlOrPage) {
  try {
    const u = new URL(urlOrPage);
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
    "untitled", "download", "file",
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

function sanitizeCleanStem(rawName, prefix = "รูปภาพ", pageUrl = "", pageTitle = "", siteName = "") {
  const typePrefix = prefix === "video" || prefix === "วิดีโอ" ? "วิดีโอ" : "รูปภาพ";
  const site = siteName || extractSiteBrand(pageUrl) || extractSiteBrand(rawName);
  const ts = formatNowTimestamp();
  let stem = "";

  if (pageTitle) {
    const cleaned = cleanPageTitle(pageTitle);
    if (cleaned && !isGibberishOrHash(cleaned)) stem = cleaned;
  }
  if (!stem && rawName && !String(rawName).startsWith("http") && !String(rawName).startsWith("data:") && !String(rawName).startsWith("blob:")) {
    const cleaned = cleanPageTitle(rawName);
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
  if (site) parts.push(site);
  if (stem && (!site || stem.toLowerCase() !== site.toLowerCase())) parts.push(stem);
  parts.push(ts);
  return parts.join("_").replace(/_+/g, "_").slice(0, 90);
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

async function convertImageStandaloneInWorker(urlOrDataUrl, targetFormat, rawFilename, pageUrl = "", pageTitle = "", siteName = "") {
  const fmt = targetFormat === "jpg" ? "jpg" : "png";
  const mime = fmt === "jpg" ? "image/jpeg" : "image/png";
  const filename = `${sanitizeCleanStem(rawFilename || urlOrDataUrl, "รูปภาพ", pageUrl, pageTitle, siteName)}.${fmt}`;

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
  const { mediaType, url, resourceUrls = [], pageUrl, pageTitle = "", siteName = "", base64Data, svgText, targetFormat, filename, autoDownload = true } = payload;
  const fmt = mediaType === "video" ? "mp4" : (targetFormat === "jpg" ? "jpg" : "png");
  const endpoint = mediaType === "video" ? "/api/convert/video" : "/api/convert/image";
  const sniffedList = senderTabId >= 0 ? (tabSniffedVideoMap.get(senderTabId) || []) : [];
  const sniffedUrl = Array.isArray(sniffedList) ? (sniffedList[0] || "") : String(sniffedList || "");
  const mergedResourceUrls = [...new Set([...resourceUrls, ...(Array.isArray(sniffedList) ? sniffedList : [])])];

  const alive = await autoWakeupCompanionServer();
  if (alive) {
    try {
      const resp = await fetch(`${COMPANION_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          resourceUrls: mergedResourceUrls,
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
          await triggerManagedChromeDownload(data.downloadUrl, data.filename);
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
    const converted = await convertImageStandaloneInWorker(inputUrl, fmt, filename, pageUrl, pageTitle, siteName);
    if (autoDownload) {
      await triggerManagedChromeDownload(converted.dataUrl, converted.filename);
    }
    return {
      ok: true,
      filename: converted.filename,
      downloadUrl: converted.dataUrl,
      mode: "standalone",
    };
  } else {
    const cleanMp4 = `${sanitizeCleanStem(filename || url, "วิดีโอ", pageUrl, pageTitle, siteName)}.mp4`;
    const bestFallbackUrl =
      base64Data ||
      (url && !url.startsWith("blob:") ? url : "") ||
      sniffedUrl ||
      (resourceUrls.length > 0 ? resourceUrls[0] : "");
    if (!bestFallbackUrl) {
      throw new Error("วิดีโอนี้เป็นสตรีมเข้ารหัส กรุณารอเซิร์ฟเวอร์ประมวลผล");
    }
    if (autoDownload) {
      await triggerManagedChromeDownload(bestFallbackUrl, cleanMp4);
    }
    return {
      ok: true,
      filename: cleanMp4,
      downloadUrl: bestFallbackUrl,
      mode: "standalone",
    };
  }
}

function updateBadge(enabled) {
  if (!chrome.action) return;
  chrome.action.setBadgeText({ text: enabled ? "ON" : "OFF" });
  chrome.action.setBadgeBackgroundColor({ color: enabled ? "#10b981" : "#64748b" });
}

async function reinjectIntoAllOpenTabs() {
  if (!chrome.tabs || !chrome.scripting) return;
  try {
    const tabs = await chrome.tabs.query({ url: ["http://*/*", "https://*/*"] });
    for (const tab of tabs) {
      if (!tab.id) continue;
      try {
        await chrome.scripting.insertCSS({
          target: { tabId: tab.id, allFrames: true },
          files: ["content/content.css"],
        });
        await chrome.scripting.executeScript({
          target: { tabId: tab.id, allFrames: true },
          files: ["content/content.js"],
        });
      } catch (_) {}
    }
  } catch (_) {}
}

chrome.runtime.onStartup?.addListener(() => {
  autoWakeupCompanionServer();
  reinjectIntoAllOpenTabs();
});

chrome.runtime.onInstalled.addListener(() => {
  autoWakeupCompanionServer();
  reinjectIntoAllOpenTabs();
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
    const fmt = info.menuItemId === "umg-save-jpg" ? "jpg" : "png";
    if (tabId >= 0) {
      chrome.tabs.sendMessage(tabId, { type: "UMG_SHOW_PROCESSING", mediaType: "image", targetFormat: fmt }, () => void chrome.runtime.lastError);
    }
    handleSmartConvertAndDownload(
      {
        mediaType: "image",
        url: info.srcUrl,
        pageUrl: tabUrl,
        pageTitle: tabTitle,
        targetFormat: fmt,
        filename: tabTitle || info.srcUrl,
      },
      tabId
    ).then((res) => {
      if (tabId >= 0 && res && res.ok) {
        chrome.tabs.sendMessage(tabId, { type: "UMG_SHOW_FINISHED", downloadUrl: res.downloadUrl, filename: res.filename, mediaType: "image" }, () => void chrome.runtime.lastError);
      }
    });
  } else if (info.menuItemId === "umg-save-mp4") {
    if (tabId >= 0) {
      chrome.tabs.sendMessage(tabId, { type: "UMG_SHOW_PROCESSING", mediaType: "video", targetFormat: "mp4" }, () => void chrome.runtime.lastError);
    }
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
    ).then((res) => {
      if (tabId >= 0 && res && res.ok) {
        chrome.tabs.sendMessage(tabId, { type: "UMG_SHOW_FINISHED", downloadUrl: res.downloadUrl, filename: res.filename, mediaType: "video" }, () => void chrome.runtime.lastError);
      }
    });
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const tabId = sender && sender.tab ? sender.tab.id : -1;
  if (msg.type === "UMG_DIRECT_DOWNLOAD" && msg.url) {
    triggerManagedChromeDownload(msg.url, msg.filename).then((downloadId) => {
      sendResponse({ ok: true, downloadId });
    });
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
