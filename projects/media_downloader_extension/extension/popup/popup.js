const COMPANION_URL = "http://127.0.0.1:8765";
const statusEl = document.getElementById("server-status");
const listEl = document.getElementById("media-list");
const dropzone = document.getElementById("dropzone");

async function checkServer() {
  try {
    const res = await fetch(`${COMPANION_URL}/api/health`);
    const data = await res.json();
    if (data.ok) {
      statusEl.textContent = `ออนไลน์ (${data.totalConverted} ไฟล์)`;
    }
  } catch (_) {
    statusEl.textContent = "ออฟไลน์ (รัน run.py)";
    statusEl.style.color = "#f87171";
  }
}

async function convertAndDownload(item, targetFormat) {
  const endpoint = item.mediaType === "video" ? "/api/convert/video" : "/api/convert/image";
  const res = await fetch(`${COMPANION_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url: item.url || "",
      svgText: item.svgText || "",
      base64Data: item.base64Data || "",
      targetFormat,
    }),
  });
  const data = await res.json();
  if (data.ok && data.downloadUrl) {
    chrome.downloads.download({ url: data.downloadUrl, filename: data.filename, saveAs: false });
    checkServer();
  }
}

document.getElementById("btn-scan").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;
  chrome.tabs.sendMessage(tab.id, { type: "UMG_SCAN_PAGE" }, (res) => {
    listEl.innerHTML = "";
    if (!res || !res.items) return;
    res.items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "item";
      const label = document.createElement("span");
      label.textContent = `[${item.label}] ${item.url || "Inline Media"}`;
      const btn = document.createElement("button");
      const fmt = item.mediaType === "video" ? "mp4" : "png";
      btn.textContent = `.${fmt.toUpperCase()}`;
      btn.onclick = () => convertAndDownload(item, fmt);
      row.appendChild(label);
      row.appendChild(btn);
      listEl.appendChild(row);
    });
  });
});

document.getElementById("btn-sandbox").addEventListener("click", () => {
  chrome.tabs.create({ url: `${COMPANION_URL}/sandbox` });
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", async (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  const url = e.dataTransfer.getData("text/uri-list") || e.dataTransfer.getData("text/plain");
  if (url) {
    const isVid = /\.(webm|ogv|mov|mkv|ts|m3u8|mp4)(\?|$)/i.test(url);
    await convertAndDownload({ mediaType: isVid ? "video" : "image", url }, isVid ? "mp4" : "png");
  }
});

checkServer();
