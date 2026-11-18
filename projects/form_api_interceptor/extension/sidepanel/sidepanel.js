// sidepanel/sidepanel.js
// Form & API Interceptor Studio Controller

document.addEventListener('DOMContentLoaded', async () => {
  // Elements
  const recordToggleBtn = document.getElementById('record-toggle-btn');
  const recLabel = document.getElementById('rec-label');
  const countApiEl = document.getElementById('count-api');
  const countFormEl = document.getElementById('count-form');
  const countAuthEl = document.getElementById('count-auth');

  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  const apiListEl = document.getElementById('api-list');
  const apiDetailEl = document.getElementById('api-detail');
  const detailMethod = document.getElementById('detail-method');
  const detailUrl = document.getElementById('detail-url');
  const detailHeaders = document.getElementById('detail-headers');
  const detailBody = document.getElementById('detail-body');
  const detailResponse = document.getElementById('detail-response');
  const detailStatus = document.getElementById('detail-status');
  const btnToggleEditPayload = document.getElementById('btn-toggle-edit-payload');
  const editPayloadTextarea = document.getElementById('edit-payload-textarea');

  const btnReplayApi = document.getElementById('btn-replay-api');
  const btnCopyCurl = document.getElementById('btn-copy-curl');
  const btnCopyPython = document.getElementById('btn-copy-python');
  const btnClearApis = document.getElementById('btn-clear-apis');

  // Filter & Search Elements
  const apiTotalStat = document.getElementById('api-total-stat');
  const fCountAll = document.getElementById('f-count-all');
  const fCountForm = document.getElementById('f-count-form');
  const fCountGet = document.getElementById('f-count-get');
  const fCountPost = document.getElementById('f-count-post');
  const apiSearchInput = document.getElementById('api-search-input');
  const detailCategoryBadge = document.getElementById('detail-category-badge');
  const detailAssociatedFormBox = document.getElementById('detail-associated-form-box');
  const formSnapshotCount = document.getElementById('form-snapshot-count');
  const formSnapshotList = document.getElementById('form-snapshot-list');

  let currentApiFilter = 'all';
  let apiSearchQuery = '';

  // Auth Tab Elements
  const btnSyncAuth = document.getElementById('btn-sync-auth');
  const authDomainText = document.getElementById('auth-domain-text');
  const authCookiesCount = document.getElementById('auth-cookies-count');
  const authBearerText = document.getElementById('auth-bearer-text');
  const btnCopyCookieStr = document.getElementById('btn-copy-cookie-str');
  const btnCopyAuthToken = document.getElementById('btn-copy-auth-token');
  const authCookieStringDisplay = document.getElementById('auth-cookie-string-display');
  const authTokensDisplay = document.getElementById('auth-tokens-display');
  const authCookiesDetailCount = document.getElementById('auth-cookies-detail-count');
  const authCookiesTableBody = document.getElementById('auth-cookies-table-body');

  const formFieldsContainer = document.getElementById('form-fields-container');
  const submitButtonCard = document.getElementById('submit-button-card');
  const submitBtnText = document.getElementById('submit-btn-text');
  const submitBtnSelector = document.getElementById('submit-btn-selector');
  const btnRefillDom = document.getElementById('btn-refill-dom');

  const codegenTarget = document.getElementById('codegen-target');
  const generatedCodeDisplay = document.getElementById('generated-code-display');
  const btnCopyCode = document.getElementById('btn-copy-code');

  const webhookUrlInput = document.getElementById('webhook-url-input');
  const autoWebhookToggle = document.getElementById('auto-webhook-toggle');
  const btnSaveSettings = document.getElementById('btn-save-settings');
  const historyListEl = document.getElementById('history-list');
  const btnClearHistory = document.getElementById('btn-clear-history');
  const toastMsg = document.getElementById('toast-msg');

  let activeSessionData = null;
  let selectedApiIndex = 0;

  // Tabs Switching
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-tab');
      tabButtons.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const activeContent = document.getElementById(target);
      if (activeContent) activeContent.classList.add('active');

      if (target === 'tab-codegen') {
        updateCodeGenerator();
      }
    });
  });

  function showToast(text) {
    toastMsg.innerText = text;
    toastMsg.classList.add('show');
    setTimeout(() => {
      toastMsg.classList.remove('show');
    }, 2200);
  }

  // Load Settings
  const settings = await chrome.storage.local.get(['webhookUrl', 'autoWebhook']);
  if (settings.webhookUrl) webhookUrlInput.value = settings.webhookUrl;
  if (settings.autoWebhook !== undefined) autoWebhookToggle.checked = settings.autoWebhook;

  btnSaveSettings.addEventListener('click', async () => {
    await chrome.storage.local.set({
      webhookUrl: webhookUrlInput.value.trim(),
      autoWebhook: autoWebhookToggle.checked
    });
    showToast('บันทึกการตั้งค่า Webhook สำเร็จค่ะ 💾');
  });

  // Record Toggle
  recordToggleBtn.addEventListener('click', async () => {
    const { isRecording } = await chrome.storage.local.get(['isRecording']);
    if (isRecording) {
      chrome.runtime.sendMessage({ type: 'STOP_RECORDING' }, () => {
        refreshStudio();
        showToast('⏹️ หยุดและบันทึกประวัติเรียบร้อยค่ะ');
      });
    } else {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      chrome.runtime.sendMessage({
        type: 'START_RECORDING',
        url: tab ? tab.url : '',
        title: tab ? tab.title : ''
      }, () => {
        refreshStudio();
        showToast('🔴 เริ่มบันทึก API และฟอร์มแล้วค่ะ');
      });
    }
  });

  // Fetch & Render Studio State
  async function refreshStudio() {
    const { isRecording, activeSession, recordedSessions = [] } = await chrome.storage.local.get([
      'isRecording',
      'activeSession',
      'recordedSessions'
    ]);

    if (isRecording) {
      recordToggleBtn.className = 'btn-rec is-recording';
      recLabel.innerText = 'หยุดบันทึก';
      activeSessionData = activeSession;
    } else {
      recordToggleBtn.className = 'btn-rec';
      recLabel.innerText = 'เริ่มบันทึก';
      activeSessionData = activeSession || recordedSessions[0] || null;
    }

    renderCounters(activeSessionData);
    renderApiTab(activeSessionData);
    renderFormTab(activeSessionData);
    renderAuthTab(activeSessionData);
    renderHistoryTab(recordedSessions);
  }

  function renderCounters(session) {
    const apiCount = (session && session.apiCalls) ? session.apiCalls.length : 0;
    const formCount = (session && session.formFields) ? session.formFields.length : 0;
    const authCount = (session && session.cookies) ? session.cookies.length : 0;
    countApiEl.innerText = apiCount;
    countFormEl.innerText = formCount;
    if (countAuthEl) countAuthEl.innerText = authCount;
  }

  // Render API Tab (Universal Harvester with Smart Form Separation)
  async function renderApiTab(session) {
    let allApis = (session && Array.isArray(session.apiCalls)) ? session.apiCalls : [];
    
    // Fallback: If no session APIs, display rolling live buffer
    if (allApis.length === 0) {
      const { liveApiBuffer = [] } = await chrome.storage.local.get(['liveApiBuffer']);
      if (liveApiBuffer.length > 0) {
        allApis = liveApiBuffer;
      }
    }

    // Update Counter Stats
    const countAll = allApis.length;
    const countForm = allApis.filter(a => a.isForm || a.category === 'FORM' || (a.associatedFormSnapshot && a.associatedFormSnapshot.length > 0)).length;
    const countGet = allApis.filter(a => a.method === 'GET').length;
    const countPost = allApis.filter(a => ['POST', 'PUT', 'PATCH', 'DELETE'].includes(a.method)).length;

    if (apiTotalStat) apiTotalStat.innerText = countAll;
    if (fCountAll) fCountAll.innerText = countAll;
    if (fCountForm) fCountForm.innerText = countForm;
    if (fCountGet) fCountGet.innerText = countGet;
    if (fCountPost) fCountPost.innerText = countPost;

    if (allApis.length === 0) {
      apiListEl.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">📡</span>
          <p>ยังไม่มี API ถูกดักจับ</p>
          <small>ระบบจะดักจับ Network API ทั้งหมดอัตโนมัติขณะเปิดหน้าเว็บค่ะ</small>
        </div>
      `;
      apiDetailEl.style.display = 'none';
      return;
    }

    // Filter APIs according to current active filter & search query
    const filteredApis = allApis.filter(api => {
      if (currentApiFilter === 'form') {
        const isForm = api.isForm || api.category === 'FORM' || (api.associatedFormSnapshot && api.associatedFormSnapshot.length > 0);
        if (!isForm) return false;
      } else if (currentApiFilter === 'get') {
        if (api.method !== 'GET') return false;
      } else if (currentApiFilter === 'post') {
        if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(api.method)) return false;
      }

      if (apiSearchQuery) {
        const matchUrl = (api.url || '').toLowerCase().includes(apiSearchQuery);
        const matchMethod = (api.method || '').toLowerCase().includes(apiSearchQuery);
        const matchBody = typeof api.requestBody === 'string' ? api.requestBody.toLowerCase().includes(apiSearchQuery) : JSON.stringify(api.requestBody || {}).toLowerCase().includes(apiSearchQuery);
        if (!matchUrl && !matchMethod && !matchBody) return false;
      }

      return true;
    });

    if (filteredApis.length === 0) {
      apiListEl.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">🔍</span>
          <p>ไม่พบรายการที่ตรงกับตัวกรอง</p>
          <small>ลองเปลี่ยนตัวกรอง หรือล้างคำค้นหาดูนะคะ</small>
        </div>
      `;
      apiDetailEl.style.display = 'none';
      return;
    }

    // Make sure selectedApiIndex is within bounds
    if (selectedApiIndex >= allApis.length || selectedApiIndex < 0) {
      selectedApiIndex = allApis.indexOf(filteredApis[0]);
    }

    let listHtml = '';
    filteredApis.forEach((api) => {
      const originalIdx = allApis.indexOf(api);
      let pathname = api.url;
      try {
        const u = new URL(api.url);
        pathname = u.pathname + u.search;
      } catch (_) {}

      const cat = api.category || (api.isForm ? 'FORM' : api.method);
      const catBadge = api.badge || (api.isForm ? '📝 FORM' : api.method);
      const activeClass = (originalIdx === selectedApiIndex) ? 'active' : '';

      listHtml += `
        <div class="api-item ${activeClass}" data-index="${originalIdx}">
          <div class="api-item-left">
            <span class="badge-method ${api.method}">${api.method}</span>
            <span class="badge-category ${cat}">${catBadge}</span>
            <span class="api-item-url" title="${escapeHtml(api.url)}">${escapeHtml(pathname)}</span>
          </div>
          <div class="api-item-meta">
            ${api.status ? `<span style="color:${api.status < 400 ? '#10B981':'#EF4444'}">${api.status}</span> • ` : ''}
            <span>${api.durationMs || 0}ms</span>
          </div>
        </div>
      `;
    });

    apiListEl.innerHTML = listHtml;
    apiDetailEl.style.display = 'flex';

    // Bind click event
    apiListEl.querySelectorAll('.api-item').forEach(item => {
      item.addEventListener('click', () => {
        selectedApiIndex = parseInt(item.getAttribute('data-index'), 10);
        apiListEl.querySelectorAll('.api-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        renderApiDetail(allApis[selectedApiIndex]);
      });
    });

    if (allApis[selectedApiIndex]) {
      renderApiDetail(allApis[selectedApiIndex]);
    } else if (filteredApis[0]) {
      selectedApiIndex = allApis.indexOf(filteredApis[0]);
      renderApiDetail(filteredApis[0]);
    }
  }

  function renderApiDetail(api) {
    if (!api) return;
    detailMethod.innerText = api.method;
    detailMethod.className = `badge-method ${api.method}`;
    detailUrl.innerText = api.url;
    detailStatus.innerText = api.status ? `${api.status} ${api.statusText || ''}` : (api.error || 'Pending');

    if (detailCategoryBadge) {
      const cat = api.category || (api.isForm ? 'FORM' : api.method);
      detailCategoryBadge.className = `badge-category ${cat}`;
      detailCategoryBadge.innerText = api.badge || (api.isForm ? '📝 FORM' : api.method);
    }

    // Render Associated Form Snapshot
    if (detailAssociatedFormBox && formSnapshotList) {
      const formFields = api.associatedFormSnapshot || [];
      if (formFields.length > 0) {
        detailAssociatedFormBox.style.display = 'block';
        if (formSnapshotCount) formSnapshotCount.innerText = formFields.length;
        let fieldsHtml = '';
        formFields.forEach(f => {
          fieldsHtml += `
            <div class="snapshot-field-item">
              <span class="snapshot-field-name">${escapeHtml(f.label || f.name || f.id || 'Field')}:</span>
              <span class="snapshot-field-val" title="${escapeHtml(String(f.value || ''))}">${escapeHtml(String(f.value || ''))}</span>
            </div>
          `;
        });
        formSnapshotList.innerHTML = fieldsHtml;
      } else {
        detailAssociatedFormBox.style.display = 'none';
      }
    }

    detailHeaders.innerText = JSON.stringify(api.requestHeaders || {}, null, 2);
    const bodyText = api.requestBody ? (typeof api.requestBody === 'object' ? JSON.stringify(api.requestBody, null, 2) : String(api.requestBody)) : '// (No request payload)';
    detailBody.innerText = bodyText;
    if (editPayloadTextarea) {
      editPayloadTextarea.value = bodyText.startsWith('//') ? '' : bodyText;
    }
    detailResponse.innerText = api.responseBody ? (typeof api.responseBody === 'object' ? JSON.stringify(api.responseBody, null, 2) : String(api.responseBody)) : (api.error ? `Error: ${api.error}` : '// (No response body)');
  }

  // Toggle Edit Payload
  if (btnToggleEditPayload && editPayloadTextarea && detailBody) {
    btnToggleEditPayload.addEventListener('click', () => {
      if (editPayloadTextarea.style.display === 'none') {
        editPayloadTextarea.style.display = 'block';
        detailBody.style.display = 'none';
        btnToggleEditPayload.innerText = '👁️ สลับดูแบบเดิม';
      } else {
        editPayloadTextarea.style.display = 'none';
        detailBody.style.display = 'block';
        btnToggleEditPayload.innerText = '✏️ แก้ไข Payload เพื่อลองยิง';
      }
    });
  }

  // Replay API Test
  btnReplayApi.addEventListener('click', async () => {
    const apis = (activeSessionData && activeSessionData.apiCalls) ? activeSessionData.apiCalls : [];
    const currentApi = apis[selectedApiIndex];
    if (!currentApi) return;

    btnReplayApi.innerText = '⏳ กำลังยิง...';
    try {
      const headers = Object.assign({}, currentApi.requestHeaders || {});
      delete headers['host'];
      delete headers['content-length'];

      // Check if user edited payload
      let bodyToSend = currentApi.requestBody;
      if (editPayloadTextarea && editPayloadTextarea.style.display !== 'none' && editPayloadTextarea.value.trim()) {
        try {
          bodyToSend = JSON.parse(editPayloadTextarea.value);
        } catch (_) {
          bodyToSend = editPayloadTextarea.value;
        }
      }

      let replayedViaTab = false;
      let resStatus = 0;
      let resStatusText = '';
      let parsed = null;

      // 1. Try replaying inside active tab first (preserves Cookies & Auth session!)
      try {
        const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (activeTab && activeTab.id) {
          const tabRes = await new Promise((resolve) => {
            chrome.tabs.sendMessage(activeTab.id, {
              type: 'ACTION_REPLAY_API',
              url: currentApi.url,
              method: currentApi.method,
              headers: headers,
              body: bodyToSend
            }, (response) => {
              if (chrome.runtime.lastError || !response || !response.success) {
                resolve(null);
              } else {
                resolve(response);
              }
            });
          });

          if (tabRes && tabRes.success) {
            replayedViaTab = true;
            resStatus = tabRes.status;
            resStatusText = tabRes.statusText;
            parsed = tabRes.data;
          }
        }
      } catch (_) {}

      // 2. Fallback: Replay directly from sidepanel context
      if (!replayedViaTab) {
        const opts = {
          method: currentApi.method,
          headers: headers
        };
        if (['POST', 'PUT', 'PATCH'].includes(currentApi.method) && bodyToSend) {
          opts.body = typeof bodyToSend === 'object' ? JSON.stringify(bodyToSend) : bodyToSend;
        }

        const res = await fetch(currentApi.url, opts);
        const text = await res.text();
        resStatus = res.status;
        resStatusText = res.statusText;
        parsed = text;
        try { parsed = JSON.parse(text); } catch (_) {}
      }

      const badgeSource = replayedViaTab ? ' (Via Tab Session 🍪⚡)' : ' (Replayed ⚡)';
      detailStatus.innerText = `${resStatus} ${resStatusText}${badgeSource}`;
      detailResponse.innerText = typeof parsed === 'object' ? JSON.stringify(parsed, null, 2) : parsed;
      showToast(`ยิง API สำเร็จ: Status ${resStatus} 🎉`);
    } catch (err) {
      detailStatus.innerText = 'Replay Failed';
      detailResponse.innerText = `Fetch Error: ${err.message}`;
      showToast('เกิดข้อผิดพลาดในการยิง API ค่ะ');
    } finally {
      btnReplayApi.innerText = '🚀 ทดสอบยิง (Replay)';
    }
  });

  // Copy cURL
  btnCopyCurl.addEventListener('click', () => {
    const apis = (activeSessionData && activeSessionData.apiCalls) ? activeSessionData.apiCalls : [];
    const currentApi = apis[selectedApiIndex];
    if (!currentApi) return;
    const curl = generateCurl(currentApi);
    navigator.clipboard.writeText(curl);
    showToast('คัดลอกคำสั่ง cURL เรียบร้อยค่ะ 📋');
  });

  // Copy Python
  btnCopyPython.addEventListener('click', () => {
    const apis = (activeSessionData && activeSessionData.apiCalls) ? activeSessionData.apiCalls : [];
    const currentApi = apis[selectedApiIndex];
    if (!currentApi) return;
    const py = generatePythonRequests(currentApi);
    navigator.clipboard.writeText(py);
    showToast('คัดลอกโค้ด Python เรียบร้อยค่ะ 🐍');
  });

  btnClearApis.addEventListener('click', async () => {
    if (activeSessionData) {
      activeSessionData.apiCalls = [];
      await chrome.storage.local.set({ activeSession: activeSessionData, liveApiBuffer: [] });
    } else {
      await chrome.storage.local.set({ liveApiBuffer: [] });
    }
    refreshStudio();
    showToast('ล้างรายการ API ทั้งหมดเรียบร้อยค่ะ 🧹');
  });

  // Filter Pills Click Listener
  document.querySelectorAll('.filter-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentApiFilter = pill.getAttribute('data-filter') || 'all';
      renderApiTab(activeSessionData);
    });
  });

  // Search Input Listener
  if (apiSearchInput) {
    apiSearchInput.addEventListener('input', (e) => {
      apiSearchQuery = (e.target.value || '').trim().toLowerCase();
      renderApiTab(activeSessionData);
    });
  }

  // Render Form Tab
  function renderFormTab(session) {
    const fields = (session && session.formFields) ? session.formFields : [];
    if (fields.length === 0) {
      formFieldsContainer.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">📝</span>
          <p>ยังไม่พบข้อมูลฟอร์ม</p>
          <small>ลองพิมพ์ข้อความ หรือเลือกตัวเลือกในหน้าเว็บขณะเปิดบันทึกค่ะ</small>
        </div>
      `;
      submitButtonCard.style.display = 'none';
      return;
    }

    let fieldsHtml = '';
    fields.forEach(f => {
      const label = f.label || f.name || f.id || 'ฟิลด์ข้อมูล';
      fieldsHtml += `
        <div class="field-card">
          <div class="field-header">
            <span class="field-label">${escapeHtml(label)}</span>
            <span class="field-type">${f.type || f.tag}</span>
          </div>
          <div class="field-value">${escapeHtml(String(f.value))}</div>
          <div class="field-selectors">
            <span>CSS: <code>${escapeHtml(f.selector || '-')}</code></span><br>
            <span>XPath: <code>${escapeHtml(f.xpath || '-')}</code></span>
          </div>
        </div>
      `;
    });

    formFieldsContainer.innerHTML = fieldsHtml;

    if (session.submitButton) {
      submitButtonCard.style.display = 'block';
      submitBtnText.innerText = session.submitButton.text || '(ไม่มีข้อความ)';
      submitBtnSelector.innerText = session.submitButton.selector || '-';
    } else {
      submitButtonCard.style.display = 'none';
    }
  }

  // Render Auth Tab
  function renderAuthTab(session) {
    if (!session) {
      if (authDomainText) authDomainText.innerText = '-';
      if (authCookiesCount) authCookiesCount.innerText = '0 รายการ';
      if (authBearerText) authBearerText.innerText = 'ไม่พบ';
      if (authCookieStringDisplay) authCookieStringDisplay.value = '';
      if (authTokensDisplay) authTokensDisplay.innerText = 'ยังไม่พบ Token ใน LocalStorage หรือ Header';
      if (authCookiesDetailCount) authCookiesDetailCount.innerText = '0';
      if (authCookiesTableBody) authCookiesTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #888;">ไม่มีคุกกี้</td></tr>';
      return;
    }

    let domain = '-';
    if (session.url) {
      try {
        domain = new URL(session.url).hostname;
      } catch (_) { domain = session.url; }
    }
    if (authDomainText) authDomainText.innerText = domain;

    const cookies = session.cookies || [];
    if (authCookiesCount) authCookiesCount.innerText = `${cookies.length} รายการ`;
    if (authCookiesDetailCount) authCookiesDetailCount.innerText = cookies.length;

    const cookieStr = session.cookieString || (cookies.map(c => `${c.name}=${c.value}`).join('; '));
    if (authCookieStringDisplay) {
      authCookieStringDisplay.value = cookieStr;
    }

    // Check Bearer & Auth Headers
    const authSummary = session.authSummary || {};
    const bearerTokens = authSummary.bearerTokens || [];
    const apiKeys = authSummary.apiKeys || {};
    const clientAuth = session.clientAuth || {};

    let hasAuth = false;
    const authDisplayParts = [];

    if (bearerTokens.length > 0) {
      hasAuth = true;
      if (authBearerText) authBearerText.innerText = `ตรวจพบ Bearer (${bearerTokens.length})`;
      bearerTokens.forEach((tok, i) => {
        authDisplayParts.push(`[Bearer Token #${i+1}]:\n${tok}`);
      });
    } else {
      if (authBearerText) authBearerText.innerText = 'ไม่พบ (ใช้ Cookie Session 🍪)';
    }

    if (Object.keys(apiKeys).length > 0) {
      hasAuth = true;
      authDisplayParts.push(`[API Keys]:\n${JSON.stringify(apiKeys, null, 2)}`);
    }

    if (Object.keys(clientAuth).length > 0) {
      hasAuth = true;
      authDisplayParts.push(`[Client Storage Auth Tokens]:\n${JSON.stringify(clientAuth, null, 2)}`);
    }

    if (authTokensDisplay) {
      authTokensDisplay.innerText = hasAuth ? authDisplayParts.join('\n\n') : 'ไม่พบ Header Authorization หรือ API Key เฉพาะเจาะจง (ระบบนี้ใช้ Cookie-based Session 🍪)';
    }

    // Render cookies table
    if (authCookiesTableBody) {
      if (cookies.length === 0) {
        authCookiesTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #888;">ไม่มีคุกกี้ (กดปุ่ม "ดึงคุกกี้ & Token สดเดี๋ยวนี้")</td></tr>';
      } else {
        authCookiesTableBody.innerHTML = cookies.map(c => `
          <tr>
            <td><strong>${escapeHtml(c.name)}</strong></td>
            <td style="max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(c.value)}">${escapeHtml(c.value)}</td>
            <td><span class="badge-${c.httpOnly ? 'http' : 'dom'}">${c.httpOnly ? 'HttpOnly 🛡️' : 'JS'}</span></td>
            <td>${c.secure ? '🔒' : '🔓'}</td>
          </tr>
        `).join('');
      }
    }
  }

  // Auth Quick Actions
  if (btnSyncAuth) {
    btnSyncAuth.addEventListener('click', async () => {
      btnSyncAuth.innerText = '⏳ กำลังดึง...';
      try {
        const res = await new Promise(resolve => {
          chrome.runtime.sendMessage({ type: 'CAPTURE_CURRENT_AUTH' }, resolve);
        });
        if (res && res.success) {
          if (!activeSessionData) {
            activeSessionData = {
              id: 'session_' + Date.now(),
              url: res.url,
              title: res.title,
              formFields: [],
              apiCalls: []
            };
          }
          activeSessionData.cookies = res.cookies;
          activeSessionData.cookieString = res.cookieString;
          activeSessionData.cookieMap = res.cookieMap;
          await chrome.storage.local.set({ activeSession: activeSessionData });
          renderAuthTab(activeSessionData);
          renderCounters(activeSessionData);
          showToast(`ดึงคุกกี้สำเร็จ ${res.count} รายการ 🎉`);
        } else {
          showToast('ไม่สามารถดึงคุกกี้ได้ (แท็บปัจจุบันอาจไม่ใช่หน้าเว็บ)');
        }
      } catch (err) {
        showToast(`ผิดพลาด: ${err.message}`);
      } finally {
        btnSyncAuth.innerText = '⚡ ดึงคุกกี้ & Token สดเดี๋ยวนี้';
      }
    });
  }

  if (btnCopyCookieStr) {
    btnCopyCookieStr.addEventListener('click', () => {
      if (authCookieStringDisplay && authCookieStringDisplay.value) {
        navigator.clipboard.writeText(authCookieStringDisplay.value);
        showToast('คัดลอก Cookie Header สำเร็จแล้วค่ะ 📋🍪');
      } else {
        showToast('ยังไม่มีคุกกี้ให้คัดลอกค่ะ');
      }
    });
  }

  if (btnCopyAuthToken) {
    btnCopyAuthToken.addEventListener('click', () => {
      const auth = (activeSessionData && activeSessionData.authSummary) || {};
      const token = (auth.bearerTokens && auth.bearerTokens[0]) || (authCookieStringDisplay && authCookieStringDisplay.value);
      if (token) {
        navigator.clipboard.writeText(token);
        showToast('คัดลอกกุญแจ Token เรียบร้อยแล้วค่ะ 🔑✨');
      } else {
        showToast('ไม่พบ Token ที่จะคัดลอกค่ะ');
      }
    });
  }

  // Refill DOM Action
  btnRefillDom.addEventListener('click', async () => {
    const fields = (activeSessionData && activeSessionData.formFields) ? activeSessionData.formFields : [];
    if (fields.length === 0) {
      alert('ยังไม่มีข้อมูลฟอร์มให้กรอกค่ะ');
      return;
    }

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) return;

    chrome.tabs.sendMessage(tab.id, {
      type: 'ACTION_AUTO_FILL',
      fields: fields,
      autoSubmit: false
    }, (res) => {
      if (res && res.success) {
        showToast(`กรอกลงหน้าเว็บสำเร็จ ${res.filledCount} ช่องค่ะ ⚡`);
      } else {
        alert('ไม่สามารถกรอกข้อมูลได้ (ตรวจสอบว่าอยู่หน้าเว็บเดิมหรือไม่)');
      }
    });
  });

  // Master AI Prompt Generator for Vibe Coding
  function generateAiPrompt(session) {
    if (!session) return '';

    const url = session.url || '-';
    const title = session.title || '-';
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

  // Header Copy AI Prompt Button
  const btnSidepanelCopyAi = document.getElementById('btn-sidepanel-copy-ai');
  if (btnSidepanelCopyAi) {
    btnSidepanelCopyAi.addEventListener('click', async () => {
      const promptText = generateAiPrompt(activeSessionData);
      if (!promptText) {
        showToast('⚠️ ยังไม่มีข้อมูลให้สร้าง Prompt ค่ะ');
        return;
      }
      await navigator.clipboard.writeText(promptText);
      showToast('🤖 คัดลอก Prompt สำหรับ AI เรียบร้อยแล้วค่ะ!');
    });
  }

  // Code Generator
  codegenTarget.addEventListener('change', updateCodeGenerator);

  function updateCodeGenerator() {
    const target = codegenTarget.value;
    const apis = (activeSessionData && activeSessionData.apiCalls) ? activeSessionData.apiCalls : [];
    const fields = (activeSessionData && activeSessionData.formFields) ? activeSessionData.formFields : [];
    const submitBtn = activeSessionData ? activeSessionData.submitButton : null;
    const currentApi = apis[selectedApiIndex] || apis[0] || null;
    const pageUrl = activeSessionData ? (activeSessionData.url || 'https://example.com') : 'https://example.com';

    let code = '';
    if (target === 'ai-prompt') {
      code = generateAiPrompt(activeSessionData);
    } else if (target === 'python') {
      code = generatePythonRequests(currentApi);
    } else if (target === 'playwright') {
      code = generatePlaywrightScript(pageUrl, fields, submitBtn);
    } else if (target === 'ai-agent') {
      code = generateAiAgentSchema(pageUrl, fields, submitBtn, currentApi);
    } else if (target === 'curl') {
      code = generateCurl(currentApi);
    } else if (target === 'node') {
      code = generateNodeScript(currentApi);
    }

    generatedCodeDisplay.innerText = code;
  }

  btnCopyCode.addEventListener('click', () => {
    navigator.clipboard.writeText(generatedCodeDisplay.innerText);
    showToast('คัดลอกโค้ดสคริปต์เรียบร้อยค่ะ 📋');
  });

  // Codegen Helpers
  function generatePythonRequests(api) {
    if (!api) return '# ไม่พบข้อมูล API ที่ดักจับได้ กรุณาบันทึกข้อมูลก่อนค่ะ';
    const method = api.method.toLowerCase();
    
    // Inject cookies and auth automatically!
    const headers = Object.assign({}, api.requestHeaders || {});
    delete headers['host'];
    delete headers['content-length'];

    if (activeSessionData && activeSessionData.cookieString && !headers['Cookie'] && !headers['cookie']) {
      headers['Cookie'] = activeSessionData.cookieString;
    }

    if (activeSessionData && activeSessionData.authSummary) {
      const tokens = activeSessionData.authSummary.bearerTokens || [];
      if (tokens.length > 0 && !headers['Authorization'] && !headers['authorization']) {
        headers['Authorization'] = `Bearer ${tokens[0]}`;
      }
      for (const [k, v] of Object.entries(activeSessionData.authSummary.apiKeys || {})) {
        if (!headers[k]) headers[k] = v;
      }
    }

    const headersStr = JSON.stringify(headers, null, 4);
    const bodyStr = api.requestBody ? (typeof api.requestBody === 'object' ? JSON.stringify(api.requestBody, null, 4) : JSON.stringify(api.requestBody)) : 'None';

    return `#!/usr/bin/env python3
# ==============================================================================
# 🚀 Python Direct API Automation Script (Ready-to-Run with Cookies 🍪 & Auth 🔑)
# Generated by Form & API Interceptor Studio
# Target Endpoint: ${api.url}
# ==============================================================================

import requests
import json

def run_automation():
    url = "${api.url}"
    
    headers = ${headersStr}
    
    # Payload ข้อมูลที่ดักได้จากหน้าเว็บ
    payload = ${bodyStr}

    print(f"🚀 กำลังส่ง [${api.method}] ไปยัง {url} ...")
    
    response = requests.${method}(
        url,
        headers=headers,
        ${['post', 'put', 'patch'].includes(method) ? (typeof api.requestBody === 'object' ? 'json=payload' : 'data=payload') : ''}
    )
    
    print(f"📥 สถานะการตอบกลับ: {response.status_code}")
    try:
        print("📄 ข้อมูลที่ได้:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print("📄 ข้อมูลแบบข้อความ:", response.text[:500])

if __name__ == "__main__":
    run_automation()
`;
  }

  function generatePlaywrightScript(url, fields, submitBtn) {
    let fieldActions = '';
    fields.forEach(f => {
      const label = f.label || f.name || f.id || 'ฟิลด์';
      const selector = f.selector || (f.id ? `#${f.id}` : `[name="${f.name}"]`);
      if (f.type === 'checkbox') {
        fieldActions += `    # ${label}\n    await page.locator('${selector}').set_checked(${f.value ? 'True' : 'False'})\n`;
      } else if (f.type === 'radio') {
        fieldActions += `    # ${label}\n    await page.locator('${selector}').check()\n`;
      } else {
        const valEscaped = String(f.value || '').replace(/'/g, "\\'");
        fieldActions += `    # ${label}\n    await page.locator('${selector}').fill('${valEscaped}')\n`;
      }
    });

    const submitAction = submitBtn ? `    # กดปุ่ม Submit: ${submitBtn.text || ''}\n    await page.locator('${submitBtn.selector}').click()\n` : `    # กดปุ่ม Submit\n    await page.locator('button[type="submit"]').click()\n`;

    let cookieInjectCode = '';
    if (activeSessionData && activeSessionData.cookies && activeSessionData.cookies.length > 0) {
      const cleanCookies = activeSessionData.cookies.map(c => ({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path
      }));
      cookieInjectCode = `\n        # 🍪 Inject Captured Cookies for instant login!\n        await context.add_cookies(${JSON.stringify(cleanCookies, null, 8)})\n`;
    }

    return `#!/usr/bin/env python3
# ==============================================================================
# 🎭 Playwright Browser Automation Script
# ใช้ในกรณีที่ยิง API ตรงไม่ได้ (ติด Cloudflare, Captcha, หรือ Dynamic Tokens)
# ==============================================================================

import asyncio
from playwright.async_api import async_playwright

async def run_browser_automation():
    async with async_playwright() as p:
        # เปิดเบราว์เซอร์จริง
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
${cookieInjectCode}        page = await context.new_page()

        print("🌐 กำลังเปิดหน้าเว็บ: ${url}")
        await page.goto("${url}", wait_until="networkidle")

        print("📝 กำลังกรอกข้อมูลลงฟอร์มอัตโนมัติ...")
${fieldActions}
        print("🔘 กำลังกดส่งข้อมูล (Submit)...")
${submitAction}
        # รอผลลัพธ์
        await page.wait_for_timeout(3000)
        print("✅ ดำเนินการเสร็จสมบูรณ์!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_browser_automation())
`;
  }

  function generateAiAgentSchema(url, fields, submitBtn, api) {
    const schema = {
      task: "Web Form Filling & Automation",
      target_url: url,
      elements_to_fill: fields.map(f => ({
        label: f.label || f.name,
        type: f.type,
        css_selector: f.selector,
        xpath: f.xpath,
        value: f.value
      })),
      submit_element: submitBtn ? {
        text: submitBtn.text,
        selector: submitBtn.selector,
        xpath: submitBtn.xpath
      } : null,
      expected_api_target: api ? {
        method: api.method,
        url: api.url
      } : null
    };

    return JSON.stringify(schema, null, 2);
  }

  function generateCurl(api) {
    if (!api) return '# ไม่พบข้อมูล API';
    let cmd = `curl -X ${api.method} '${api.url}' \\\n`;
    const headers = Object.assign({}, api.requestHeaders || {});

    // Inject cookies & auth automatically into cURL!
    if (activeSessionData && activeSessionData.cookieString && !headers['Cookie'] && !headers['cookie']) {
      headers['Cookie'] = activeSessionData.cookieString;
    }
    if (activeSessionData && activeSessionData.authSummary && activeSessionData.authSummary.bearerTokens && activeSessionData.authSummary.bearerTokens.length > 0) {
      if (!headers['Authorization'] && !headers['authorization']) {
        headers['Authorization'] = `Bearer ${activeSessionData.authSummary.bearerTokens[0]}`;
      }
    }

    Object.entries(headers).forEach(([k, v]) => {
      if (!['host', 'content-length'].includes(k.toLowerCase())) {
        cmd += `  -H '${k}: ${v}' \\\n`;
      }
    });
    if (api.requestBody && ['POST', 'PUT', 'PATCH'].includes(api.method)) {
      const data = typeof api.requestBody === 'object' ? JSON.stringify(api.requestBody) : api.requestBody;
      cmd += `  --data-raw '${data.replace(/'/g, "'\\''")}'`;
    }
    return cmd.trim();
  }

  function generateNodeScript(api) {
    if (!api) return '// ไม่พบข้อมูล API';
    const headers = Object.assign({}, api.requestHeaders || {});
    if (activeSessionData && activeSessionData.cookieString && !headers['Cookie'] && !headers['cookie']) {
      headers['Cookie'] = activeSessionData.cookieString;
    }
    if (activeSessionData && activeSessionData.authSummary && activeSessionData.authSummary.bearerTokens && activeSessionData.authSummary.bearerTokens.length > 0) {
      if (!headers['Authorization'] && !headers['authorization']) {
        headers['Authorization'] = `Bearer ${activeSessionData.authSummary.bearerTokens[0]}`;
      }
    }

    return `// Node.js Fetch Automation (Ready-to-Run with Cookies 🍪)
const runApi = async () => {
  const url = "${api.url}";
  const options = {
    method: "${api.method}",
    headers: ${JSON.stringify(headers, null, 2)},
    ${api.requestBody ? `body: JSON.stringify(${JSON.stringify(api.requestBody, null, 2)})` : ''}
  };

  console.log("🚀 Sending request...");
  const res = await fetch(url, options);
  const data = await res.json();
  console.log("Response status:", res.status);
  console.log("Response data:", data);
};

runApi();
`;
  }

  // Render History Tab
  function renderHistoryTab(sessions) {
    if (!sessions || sessions.length === 0) {
      historyListEl.innerHTML = '<p class="hint" style="text-align:center; padding:16px;">ยังไม่มีประวัติการบันทึก</p>';
      return;
    }

    let html = '';
    sessions.forEach((s, idx) => {
      const timeStr = new Date(s.startTime).toLocaleTimeString();
      html += `
        <div class="history-item">
          <div>
            <div class="history-title">${escapeHtml(s.title || s.url || 'เซสชัน ' + (idx + 1))}</div>
            <div class="history-time">บันทึกเมื่อ: ${timeStr} • ฟอร์ม: ${(s.formFields||[]).length} ช่อง • API: ${(s.apiCalls||[]).length}</div>
          </div>
          <button class="btn-action" data-restore="${idx}">เรียกดู</button>
        </div>
      `;
    });
    historyListEl.innerHTML = html;

    historyListEl.querySelectorAll('[data-restore]').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.getAttribute('data-restore'), 10);
        activeSessionData = sessions[idx];
        showToast(`โหลดประวัติเซสชันที่ ${idx + 1} เรียบร้อยค่ะ`);
        // Switch to API tab
        tabButtons[0].click();
        refreshStudio();
      });
    });
  }

  btnClearHistory.addEventListener('click', async () => {
    chrome.runtime.sendMessage({ type: 'CLEAR_RECORDINGS' }, () => {
      refreshStudio();
      showToast('ล้างประวัติทั้งหมดเรียบร้อยค่ะ');
    });
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // Initial render & sync polling
  await refreshStudio();
  setInterval(refreshStudio, 1500);
});
