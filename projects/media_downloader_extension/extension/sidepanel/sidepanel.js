const COMPANION_URL = "http://127.0.0.1:8765";
const container = document.getElementById("history-container");

async function loadHistory() {
  try {
    const res = await fetch(`${COMPANION_URL}/api/history`);
    const data = await res.json();
    if (!data.items || data.items.length === 0) {
      container.textContent = "ยังไม่มีประวัติการดาวน์โหลด";
      return;
    }
    container.innerHTML = "";
    data.items.forEach((it) => {
      const div = document.createElement("div");
      div.className = "history-item";
      div.innerHTML = `<b>${it.filename}</b> (${it.sourceFormat} ➔ ${it.targetFormat})<br/><small>${it.timestamp} • ${(it.sizeBytes / 1024).toFixed(1)} KB</small>`;
      container.appendChild(div);
    });
  } catch (_) {
    container.textContent = "ไม่สามารถเชื่อมต่อ Companion Server (127.0.0.1:8765)";
  }
}

loadHistory();
setInterval(loadHistory, 3000);

