// Universal Media Grabber — Manifest V3 Background Service Worker
// ทำงานได้ 100% แบบ Standalone (ไม่ต้องรันเซิร์ฟเวอร์!) ด้วย OffscreenCanvas + Background CORS-Free Fetch
// และถ้ามี Companion Server (127.0.0.1:8765) เปิดอยู่ ก็จะใช้ FFmpeg ช่วยแปลงวิดีโอสตรีมมิ่งขั้นสูงให้อัตโนมัติ

const COMPANION_URL = "http://127.0.0.1:8765";
const WEIRD_EXT_REGEX = /\.(webp|avif|svg|svgz|jfif|bmp|gif|ico|tiff|tif|heic|webm|ogv|ogg|mov|mkv|ts|m3u8|mpd|flv|avi|bin|dat|php)(\?.*|#.*|$)/i;

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

function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

// แปลงรูปภาพทุกชนิด (.webp, .avif, .bmp, .gif, .jfif, ข้ามโดเมนติด CORS) ให้เป็น .PNG หรือ .JPG แท้ใน Service Worker โดยไม่ต้องง้อเซิร์ฟเวอร์
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

async function handleSmartConvertAndDownload({ mediaType, url, base64Data, svgText, targetFormat, filename }) {
  const fmt = mediaType === "video" ? "mp4" : (targetFormat === "jpg" ? "jpg" : "png");
  const endpoint = mediaType === "video" ? "/api/convert/video" : "/api/convert/image";

  // 1. ลองถาม Companion Server ก่อน (เผื่อเปิดอยู่ จะได้ใช้ FFmpeg สำหรับวิดีโอ .m3u8/.webm)
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1200);
    const resp = await fetch(`${COMPANION_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, base64Data, svgText, targetFormat: fmt, filename }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    const data = await resp.json();
    if (data && data.ok && data.downloadUrl) {
      await chrome.downloads.download({
        url: data.downloadUrl,
        filename: data.filename,
        conflictAction: "uniquify",
        saveAs: false,
      });
      return { ok: true, filename: data.filename, mode: "companion" };
    }
  } catch (_) {
    // ถ้าไม่ได้เปิดเซิร์ฟเวอร์ไว้ จะสลับมาใช้โหมด Standalone ในตัว Chrome Extension ทันที!
  }

  // 2. โหมด Standalone 100% (ไม่ต้องเปิดเซิร์ฟเวอร์)
  if (mediaType === "image") {
    const inputUrl = base64Data || url;
    const converted = await convertImageStandaloneInWorker(inputUrl, fmt, filename);
    await chrome.downloads.download({
      url: converted.dataUrl,
      filename: converted.filename,
      conflictAction: "uniquify",
      saveAs: false,
    });
    return { ok: true, filename: converted.filename, mode: "standalone" };
  } else {
    const cleanMp4 = `${sanitizeCleanStem(filename || url, "video")}.mp4`;
    const downloadSource = base64Data || url;
    await chrome.downloads.download({
      url: downloadSource,
      filename: cleanMp4,
      conflictAction: "uniquify",
      saveAs: false,
    });
    return { ok: true, filename: cleanMp4, mode: "standalone" };
  }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "umg-save-png",
      title: "🖼 ดาวน์โหลดภาพเป็นไฟล์มาตรฐาน (.PNG)",
      contexts: ["image"],
    });
    chrome.contextMenus.create({
      id: "umg-save-jpg",
      title: "📷 ดาวน์โหลดภาพเป็นไฟล์มาตรฐาน (.JPG)",
      contexts: ["image"],
    });
    chrome.contextMenus.create({
      id: "umg-save-mp4",
      title: "🎬 ดาวน์โหลดวิดีโอเป็นไฟล์มาตรฐาน (.MP4)",
      contexts: ["video", "audio"],
    });
  });
});

chrome.contextMenus.onClicked.addListener((info) => {
  if (!info.srcUrl) return;
  if (info.menuItemId === "umg-save-png" || info.menuItemId === "umg-save-jpg") {
    handleSmartConvertAndDownload({
      mediaType: "image",
      url: info.srcUrl,
      targetFormat: info.menuItemId === "umg-save-jpg" ? "jpg" : "png",
      filename: info.srcUrl,
    });
  } else if (info.menuItemId === "umg-save-mp4") {
    handleSmartConvertAndDownload({
      mediaType: "video",
      url: info.srcUrl,
      targetFormat: "mp4",
      filename: info.srcUrl,
    });
  }
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
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

  if (msg.type === "UMG_SMART_CONVERT_AND_DOWNLOAD") {
    handleSmartConvertAndDownload(msg.payload)
      .then((res) => sendResponse(res))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }
});
