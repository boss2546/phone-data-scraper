// popup/popup.js

document.addEventListener('DOMContentLoaded', async () => {
  const toggleBtn = document.getElementById('toggle-record-btn');
  const btnText = document.getElementById('btn-text');
  const statusPill = document.getElementById('status-pill');
  const fieldsCountEl = document.getElementById('stat-fields-count');
  const apiCountEl = document.getElementById('stat-api-count');
  const authCountEl = document.getElementById('stat-auth-count');
  const previewEl = document.getElementById('latest-preview');
  const pageTag = document.getElementById('page-tag');
  const openSidepanelBtn = document.getElementById('open-sidepanel-btn');
  const quickRefillBtn = document.getElementById('quick-refill-btn');
  const exportJsonBtn = document.getElementById('export-json-btn');

  let currentTab = null;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tab;
    if (tab && tab.url) {
      try {
        const urlObj = new URL(tab.url);
        pageTag.innerText = urlObj.hostname;
      } catch (_) {
        pageTag.innerText = tab.title || 'Tab';
      }
    }
  } catch (_) {}

  // Load and render status
  async function refreshState() {
    const { isRecording, activeSession, recordedSessions = [] } = await chrome.storage.local.get([
      'isRecording',
      'activeSession',
      'recordedSessions'
    ]);

    if (isRecording) {
      statusPill.innerText = 'REC 🔴';
      statusPill.className = 'status-pill recording';
      toggleBtn.className = 'btn btn-record is-recording';
      btnText.innerText = '⏹️ หยุดและบันทึกผล (Stop & Save)';

      const fieldsCount = (activeSession && activeSession.formFields) ? activeSession.formFields.length : 0;
      const apiCount = (activeSession && activeSession.apiCalls) ? activeSession.apiCalls.length : 0;
      const authCount = (activeSession && activeSession.cookies) ? activeSession.cookies.length : 0;

      fieldsCountEl.innerText = fieldsCount;
      apiCountEl.innerText = apiCount;
      if (authCountEl) authCountEl.innerText = authCount;

      renderPreview(activeSession);
    } else {
      statusPill.innerText = 'IDLE ⚪';
      statusPill.className = 'status-pill idle';
      toggleBtn.className = 'btn btn-record';
      btnText.innerText = '🔴 เริ่มบันทึก (Start Recording)';

      const latest = recordedSessions[0];
      if (latest) {
        fieldsCountEl.innerText = (latest.formFields || []).length;
        apiCountEl.innerText = (latest.apiCalls || []).length;
        if (authCountEl) authCountEl.innerText = (latest.cookies || []).length;
        renderPreview(latest);
      } else {
        fieldsCountEl.innerText = '0';
        apiCountEl.innerText = '0';
        if (authCountEl) authCountEl.innerText = '0';
        previewEl.innerHTML = '<p class="empty-hint">ยังไม่มีการบันทึก กดปุ่ม "เริ่มบันทึก" แล้วกรอกฟอร์มจริงบนหน้าเว็บได้เลยค่ะ</p>';
      }
    }
  }

  function renderPreview(session) {
    if (!session) return;
    const fields = session.formFields || [];
    const apis = session.apiCalls || [];

    if (fields.length === 0 && apis.length === 0) {
      previewEl.innerHTML = '<p class="empty-hint">กำลังรอการกรอกฟอร์มหรือยิง API...</p>';
      return;
    }

    let html = '';
    // Show up to 2 recent fields
    fields.slice(-2).forEach(f => {
      const label = f.label || f.name || f.id || 'ฟิลด์';
      html += `
        <div class="preview-item">
          <span class="preview-key">📝 ${escapeHtml(label)}:</span>
          <span class="preview-val">${escapeHtml(String(f.value))}</span>
        </div>
      `;
    });

    // Show up to 2 recent APIs
    apis.slice(-2).forEach(a => {
      let urlPath = a.url;
      try {
        const u = new URL(a.url);
        urlPath = u.pathname;
      } catch (_) {}

      html += `
        <div class="preview-item">
          <span class="preview-key" style="color:#10B981">🌐 [${a.method}]</span>
          <span class="preview-val" title="${escapeHtml(a.url)}">${escapeHtml(urlPath)}</span>
        </div>
      `;
    });

    previewEl.innerHTML = html;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // Toggle Recording
  toggleBtn.addEventListener('click', async () => {
    const { isRecording } = await chrome.storage.local.get(['isRecording']);
    if (isRecording) {
      chrome.runtime.sendMessage({ type: 'STOP_RECORDING' }, () => {
        refreshState();
      });
    } else {
      chrome.runtime.sendMessage({
        type: 'START_RECORDING',
        url: currentTab ? currentTab.url : '',
        title: currentTab ? currentTab.title : ''
      }, () => {
        refreshState();
      });
    }
  });

  // Open SidePanel
  openSidepanelBtn.addEventListener('click', async () => {
    if (currentTab && currentTab.windowId && chrome.sidePanel && chrome.sidePanel.open) {
      await chrome.sidePanel.open({ windowId: currentTab.windowId });
      window.close();
    } else {
      chrome.runtime.sendMessage({ type: 'OPEN_SIDEPANEL' }, () => {
        window.close();
      });
    }
  });

  // Quick Refill
  quickRefillBtn.addEventListener('click', async () => {
    const { recordedSessions = [] } = await chrome.storage.local.get(['recordedSessions']);
    const latest = recordedSessions[0];
    if (!latest || !latest.formFields || latest.formFields.length === 0) {
      alert('ยังไม่มีข้อมูลฟอร์มที่เคยบันทึกไว้ค่ะ');
      return;
    }

    if (!currentTab || !currentTab.id) return;
    try {
      chrome.tabs.sendMessage(currentTab.id, {
        type: 'ACTION_AUTO_FILL',
        fields: latest.formFields,
        autoSubmit: false
      }, (res) => {
        if (res && res.success) {
          alert(`กรอกข้อมูลสำเร็จ ${res.filledCount} ช่องค่ะ! ⚡`);
        } else {
          alert(`ไม่พบช่องตรงกันบนหน้านี้ค่ะ (${(res && res.errors) ? res.errors[0] : 'Mismatch'})`);
        }
      });
    } catch (e) {
      alert('ไม่สามารถเชื่อมต่อกับหน้าเว็บนี้ได้ค่ะ');
    }
  });

  // 🤖 Generate Master AI Prompt for Vibe Coding
  function generateAiPrompt(session) {
    if (!session) return '';

    const url = session.url || (currentTab ? currentTab.url : '-');
    const title = session.title || (currentTab ? currentTab.title : '-');
    const dateStr = session.startTime ? new Date(session.startTime).toLocaleString('th-TH') : new Date().toLocaleString('th-TH');

    // Auth Summary
    const authSummary = session.authSummary || {};
    const bearerToken = (authSummary.bearerTokens && authSummary.bearerTokens[0]) 
      ? authSummary.bearerTokens[0] 
      : (session.clientAuth ? (session.clientAuth.local_token || session.clientAuth.session_token || 'None') : 'None');
    const cookieStr = session.cookieString || '-';

    // Form Fields Table
    const fields = session.formFields || [];
    let formTable = '';
    if (fields.length > 0) {
      formTable = `| ลำดับ | ชื่อฟิลด์ (Label / Name) | HTML Tag & ID | CSS Selector | ค่าที่กรอกจริง (Value) |\n| :--- | :--- | :--- | :--- | :--- |\n`;
      fields.forEach((f, idx) => {
        const label = f.label || f.name || f.id || `Field_${idx + 1}`;
        const tagId = `${f.tag || 'input'}${f.id ? ' (#' + f.id + ')' : ''}`;
        const val = f.value !== undefined ? String(f.value) : '';
        formTable += `| ${idx + 1} | **${label}** | \`${tagId}\` | \`${f.selector || '-'}\` | \`${val}\` |\n`;
      });
    } else {
      formTable = `*(ไม่มีข้อมูลฟอร์มบนหน้านี้ เป็นการเรียก Network API โดยตรง)*\n`;
    }

    // APIs Section
    const apis = session.apiCalls || [];
    let apiDetails = '';
    if (apis.length > 0) {
      const prioritizedApis = apis.slice(-6);
      prioritizedApis.forEach((a, idx) => {
        let bodyFormatted = 'ไม่มี Payload (No Body)';
        if (a.requestBody) {
          try {
            bodyFormatted = typeof a.requestBody === 'object' ? JSON.stringify(a.requestBody, null, 2) : String(a.requestBody);
          } catch (_) {
            bodyFormatted = String(a.requestBody);
          }
        }

        let resFormatted = 'ไม่มี Response Body';
        if (a.responseBody) {
          try {
            resFormatted = typeof a.responseBody === 'object' ? JSON.stringify(a.responseBody, null, 2) : String(a.responseBody);
            if (resFormatted.length > 2500) resFormatted = resFormatted.slice(0, 2500) + '\n... (ตัดทอนเพื่อความกระชับ)';
          } catch (_) {
            resFormatted = String(a.responseBody).slice(0, 1000);
          }
        }

        apiDetails += `
### 🌐 API รายการที่ ${idx + 1}: \`[${a.method}] ${a.url}\`
* **สถานะตอบกลับ (Status):** \`${a.status || '-'} ${a.statusText || ''}\` (ใช้เวลา ${a.durationMs || 0}ms)
* **หมวดหมู่:** \`${a.category || (a.isForm ? 'FORM SUBMIT' : a.method)}\`
* **Request Headers ที่จำเป็น:**
\`\`\`json
${JSON.stringify(a.requestHeaders || {}, null, 2)}
\`\`\`
* **Request Body / Payload:**
\`\`\`json
${bodyFormatted}
\`\`\`
* **Response Output:**
\`\`\`json
${resFormatted}
\`\`\`
`;
      });
    } else {
      apiDetails = `*(ยังไม่มี Network API บันทึกไว้)*\n`;
    }

    return `# 🤖 [AI Automation Request] ข้อมูลหน้าเว็บจริงที่ดักจับได้ (AI-Ready Context)

> **สำหรับ AI Assistant (Claude / ChatGPT / Cursor / Antigravity):**
> ผู้ใช้งานคือผู้พัฒนาสาย Vibe Coding (ไม่ได้เขียนโค้ดด้วยตัวเอง) ต้องการให้คุณทำหน้าที่เป็น Senior Full-Stack & Automation Engineer ช่วยวิเคราะห์ข้อมูลที่ดักจับได้สด ๆ จากเบราว์เซอร์ด้านล่างนี้ แล้วเขียนโค้ดอัตโนมัติที่พร้อมรัน (100% Ready-to-Run) ตามคำสั่งที่ผู้ใช้ต้องการ

---

## 📌 1. บริบทหน้าเว็บ & การยืนยันตัวตน (Context & Auth)
* **URL:** \`${url}\`
* **หัวข้อหน้าเว็บ (Title):** \`${title}\`
* **เวลาที่ดักจับ:** \`${dateStr}\`
* **🔑 Bearer Token:**
\`\`\`text
${bearerToken}
\`\`\`
* **🍪 Cookie Header:**
\`\`\`text
${cookieStr}
\`\`\`

---

## 📝 2. โครงสร้างฟอร์มที่กรอกจริงบนหน้าเว็บ (DOM Form Fields)
${formTable}

---

## 📡 3. รายการ Network API ที่ดักจับได้จริง (Intercepted API Calls)
${apiDetails}

---

## 🎯 4. คำสั่งที่ต้องการให้ AI ปฏิบัติการ (Instructions for AI)
โปรดวิเคราะห์ข้อมูลข้างต้น แล้วเขียนโค้ดอัตโนมัติให้ผู้ใช้ทันที:
1. **กรณีต้องการยิง API ตรง:** เขียนสคริปต์ Python (\`requests\`) ที่มี Headers, Auth/Cookies, และ Payload ครบถ้วน พร้อมระบบ Retry และข้อความแสดงผลภาษาไทย
2. **กรณีต้องการสร้างบอทจำลองเบราว์เซอร์:** เขียนสคริปต์ Playwright (Python หรือ Node.js) กรอกข้อมูลตามพิกัด CSS Selector ด้านบนทีละช่องเหมือนมนุษย์
3. **กรณีนำเข้าข้อมูลจำนวนมาก (Batch Import):** เขียนระบบอ่านไฟล์ CSV/Excel แล้วนำไปวนลูปยิง API สร้างข้อมูลต่อเนื่องพร้อมหน่วงเวลา (Rate-limit delay)
*(โปรดเขียนโค้ดฉบับสมบูรณ์ ไม่ย่อ ไม่ใช้ Mock data และแนะนำคำสั่งรันใน Terminal แบบเข้าใจง่าย)*
`;
  }

  // Copy AI Prompt Button Handler
  const copyAiPromptBtn = document.getElementById('copy-ai-prompt-btn');
  const copyAiText = document.getElementById('copy-ai-text');

  if (copyAiPromptBtn) {
    copyAiPromptBtn.addEventListener('click', async () => {
      const { activeSession, recordedSessions = [], liveApiBuffer = [] } = await chrome.storage.local.get([
        'activeSession',
        'recordedSessions',
        'liveApiBuffer'
      ]);

      let targetData = activeSession || recordedSessions[0];
      if (!targetData && liveApiBuffer.length > 0) {
        targetData = {
          url: currentTab ? currentTab.url : '',
          title: currentTab ? currentTab.title : '',
          apiCalls: liveApiBuffer,
          formFields: [],
          status: 'LIVE'
        };
      }

      if (!targetData) {
        alert('ยังไม่มีข้อมูลให้สร้าง Prompt ค่ะ ลองเปิดบันทึกหรือใช้งานหน้าเว็บก่อนนะคะ');
        return;
      }

      const promptText = generateAiPrompt(targetData);
      try {
        await navigator.clipboard.writeText(promptText);
        copyAiPromptBtn.classList.add('copied');
        if (copyAiText) copyAiText.innerText = '✅ คัดลอกสำเร็จ! แปะถาม AI ได้เลย';
        setTimeout(() => {
          copyAiPromptBtn.classList.remove('copied');
          if (copyAiText) copyAiText.innerText = 'คัดลอก Prompt สำหรับ AI (1 คลิก)';
        }, 3000);
      } catch (err) {
        // Fallback copy using textarea
        const ta = document.createElement('textarea');
        ta.value = promptText;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
        alert('📋 คัดลอก Prompt สำหรับ AI เรียบร้อยแล้วค่ะ!');
      }
    });
  }

  // Export JSON
  exportJsonBtn.addEventListener('click', async () => {
    const { activeSession, recordedSessions = [] } = await chrome.storage.local.get([
      'activeSession',
      'recordedSessions'
    ]);
    const targetData = activeSession || recordedSessions[0];
    if (!targetData) {
      alert('ยังไม่มีข้อมูลให้ดาวน์โหลดค่ะ');
      return;
    }

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(targetData, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `form_api_capture_${Date.now()}.json`);
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();
  });

  // Polling update while popup is open
  await refreshState();
  setInterval(refreshState, 1000);
});
