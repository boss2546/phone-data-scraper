const COMPANION_URL = "http://127.0.0.1:8765";
const statusEl = document.getElementById("server-status");
const listEl = document.getElementById("media-list");
const dropzone = document.getElementById("dropzone");
const powerBox = document.getElementById("power-box");
const powerTitle = document.getElementById("power-title");
const powerSub = document.getElementById("power-sub");
const btnTogglePower = document.getElementById("btn-toggle-power");
const customPrefixInput = document.getElementById("custom-prefix-input");
const btnClearPrefix = document.getElementById("btn-clear-prefix");
const namingPreview = document.getElementById("naming-preview");

let isEnabled = true;

function updateNamingPreview(val) {
  const clean = String(val || "").trim().replace(/[^a-zA-Z0-9ก-๙_\-\s]/g, "").replace(/[\s_]+/g, "_").slice(0, 35);
  if (clean) {
    namingPreview.textContent = `📌 ชื่อไฟล์ที่ได้: ${clean}_รูปภาพ_01.png / ${clean}_วิดีโอ_01.mp4`;
  } else {
    namingPreview.textContent = `✨ โหมดออโต้: รูปภาพ_ชื่อเว็บ_ชื่อสินค้า_01.png / .mp4`;
  }
}

function renderPowerState(enabled) {
  isEnabled = Boolean(enabled);
  if (isEnabled) {
    powerBox.classList.remove("off");
    btnTogglePower.classList.remove("off");
    powerTitle.textContent = "🟢 เปิดใช้งานอยู่ (ON)";
    powerSub.textContent = "วางเมาส์ชี้รูป/วิดีโอเพื่อโหลด (คีย์ลัด Alt+M)";
    btnTogglePower.textContent = "🟢 เปิด (ON)";
  } else {
    powerBox.classList.add("off");
    btnTogglePower.classList.add("off");
    powerTitle.textContent = "⚪ ปิดพักการทำงาน (OFF)";
    powerSub.textContent = "ซ่อนปุ่มลอยบนหน้าเว็บชั่วคราว (คีย์ลัด Alt+M)";
    btnTogglePower.textContent = "⚪ ปิด (OFF)";
  }
}

function initPowerState() {
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get({ umgEnabled: true, umgCustomPrefix: "" }, (res) => {
      renderPowerState(res.umgEnabled !== false);
      const savedPrefix = String(res.umgCustomPrefix || "");
      customPrefixInput.value = savedPrefix;
      updateNamingPreview(savedPrefix);
    });
  }
}

customPrefixInput.addEventListener("input", () => {
  const val = customPrefixInput.value.trim();
  updateNamingPreview(val);
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.set({ umgCustomPrefix: val });
  }
});

btnClearPrefix.addEventListener("click", () => {
  customPrefixInput.value = "";
  updateNamingPreview("");
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.set({ umgCustomPrefix: "" });
  }
});

btnTogglePower.addEventListener("click", () => {
  const nextState = !isEnabled;
  renderPowerState(nextState);
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.set({ umgEnabled: nextState });
  }
  chrome.runtime.sendMessage({ type: "UMG_SET_ENABLED", enabled: nextState });
});

async function checkServer() {
  try {
    const res = await fetch(`${COMPANION_URL}/api/health`);
    const data = await res.json();
    if (data.ok) {
      statusEl.textContent = `⚡ โหมดเต็มรูปแบบ + FFmpeg`;
      return;
    }
  } catch (_) {}
  statusEl.textContent = "🟢 โหมดทำงานเดี่ยว";
  statusEl.style.color = "#34d399";
}

async function convertAndDownload(item, targetFormat) {
  let tabUrl = item.pageUrl || "";
  let tabTitle = "";
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      if (!tabUrl) tabUrl = tab.url || "";
      tabTitle = tab.title || "";
    }
  } catch (_) {}

  chrome.runtime.sendMessage(
    {
      type: "UMG_SMART_CONVERT_AND_DOWNLOAD",
      payload: {
        mediaType: item.mediaType,
        url: item.url || "",
        pageUrl: tabUrl,
        pageTitle: tabTitle,
        svgText: item.svgText || "",
        base64Data: item.base64Data || "",
        targetFormat,
        filename: tabTitle || item.url || `media_${Date.now()}`,
      },
    },
    () => checkServer()
  );
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
      label.textContent = `${item.label}: ${item.url || "Media"}`;
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

initPowerState();
checkServer();
