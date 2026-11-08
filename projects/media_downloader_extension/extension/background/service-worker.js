// Universal Media Grabber — Manifest V3 Background Service Worker
// ความสามารถพิเศษ:
// 1. สั่งปลุก Companion Server (127.0.0.1:8765) เองอัตโนมัติผ่าน Native Messaging / Auto-Start Daemon เมื่อต้องใช้เซิร์ฟเวอร์แปลงไฟล์
// 2. รองรับโหมด Standalone (OffscreenCanvas) ในตัว Extension เอง
// 3. ส่งสถานะ "กำลังประมวลผล..." ➔ "ประมวลผลเสร็จแล้ว! กดโหลดอีกครั้ง" กลับไปยังหน้าเว็บ พร้อมลิงก์ดาวน์โหลดซ้ำได้ทันที

const COMPANION_URL = "http://127.0.0.1:8765";
const NATIVE_HOST = "com.meuu.umg_companion";
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

  // สั่งปลุกผ่าน Chrome Native Messaging Host ถ้าลงทะเบียนไว้
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

async function handleSmartConvertAndDownload({ mediaType, url, base64Data, svgText, targetFormat, filename, autoDownload = true }) {
  const fmt = mediaType === "video" ? "mp4" : (targetFormat === "jpg" ? "jpg" : "png");
  const endpoint = mediaType === "video" ? "/api/convert/video" : "/api/convert/image";

  // 1. ตรวจสอบหรือสั่งปลุก Companion Server อัตโนมัติ
  const alive = await autoWakeupCompanionServer();
  if (alive) {
    try {
      const resp = await fetch(`${COMPANION_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, base64Data, svgText, targetFormat: fmt, filename }),
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

  // 2. ถ้าเป็นรูปภาพและไม่ได้ใช้เซิร์ฟเวอร์ แปลงใน OffscreenCanvas ของ Extension ทันที
  if (mediaType === "image") {
    const inputUrl = base64Data || url;
    const converted = await convertImageStandaloneInWorker(inputUrl, fmt, filename);
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
    const cleanMp4 = `${sanitizeCleanStem(filename || url, "video")}.mp4`;
    const downloadSource = base64Data || url;
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

chrome.runtime.onInstalled.addListener(() => {
  autoWakeupCompanionServer();
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
