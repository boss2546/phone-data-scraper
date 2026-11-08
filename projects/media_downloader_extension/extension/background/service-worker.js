// Universal Media Grabber — Manifest V3 Background Service Worker
const COMPANION_URL = "http://127.0.0.1:8765";

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

chrome.contextMenus.onClicked.addListener(async (info) => {
  const srcUrl = info.srcUrl;
  if (!srcUrl) return;

  if (info.menuItemId === "umg-save-png" || info.menuItemId === "umg-save-jpg") {
    const targetFormat = info.menuItemId === "umg-save-jpg" ? "jpg" : "png";
    const resp = await fetch(`${COMPANION_URL}/api/convert/image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: srcUrl, targetFormat }),
    });
    const data = await resp.json();
    if (data.ok && data.downloadUrl) {
      chrome.downloads.download({ url: data.downloadUrl, filename: data.filename, saveAs: false });
    }
  } else if (info.menuItemId === "umg-save-mp4") {
    const resp = await fetch(`${COMPANION_URL}/api/convert/video`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: srcUrl, targetFormat: "mp4" }),
    });
    const data = await resp.json();
    if (data.ok && data.downloadUrl) {
      chrome.downloads.download({ url: data.downloadUrl, filename: data.filename, saveAs: false });
    }
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
});

