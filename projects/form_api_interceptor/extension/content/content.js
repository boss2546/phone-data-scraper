// content/content.js
// Runs in ISOLATED world
// Coordinates DOM Form tracking, collects API events from MAIN world, and manages on-page UI

(function() {
  let isRecording = false;
  let recordedFieldsMap = new Map(); // selector -> field info
  let recordedSubmitButton = null;
  let floatingBadge = null;
  let lastFormInteractionTime = 0;
  let lastSubmitClickTime = 0;

  // Initialize state
  chrome.storage.local.get(['isRecording', 'activeSession'], (res) => {
    isRecording = !!res.isRecording;
    if (isRecording) {
      if (res.activeSession && Array.isArray(res.activeSession.formFields)) {
        res.activeSession.formFields.forEach(f => {
          recordedFieldsMap.set(f.selector || f.id || f.name, f);
        });
      }
      showFloatingBadge();
    }
  });

  // Listen for background state changes
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'RECORDING_STATE_CHANGED') {
      isRecording = message.isRecording;
      if (isRecording) {
        recordedFieldsMap.clear();
        recordedSubmitButton = null;
        showFloatingBadge();
      } else {
        hideFloatingBadge();
      }
      sendResponse({ success: true });
    } else if (message.type === 'ACTION_AUTO_FILL') {
      const result = executeAutoFill(message.fields, message.autoSubmit, message.submitSelector);
      sendResponse(result);
    } else if (message.type === 'ACTION_REPLAY_API') {
      // Replay API directly inside the authenticated web page context!
      (async () => {
        try {
          const opts = {
            method: message.method || 'GET',
            headers: Object.assign({}, message.headers || {}),
            credentials: 'include'
          };
          delete opts.headers['host'];
          delete opts.headers['content-length'];

          if (['POST', 'PUT', 'PATCH'].includes(opts.method) && message.body) {
            opts.body = typeof message.body === 'object' ? JSON.stringify(message.body) : message.body;
          }

          const res = await fetch(message.url, opts);
          const text = await res.text();
          let data = text;
          try { data = JSON.parse(text); } catch (_) {}
          sendResponse({
            success: true,
            status: res.status,
            statusText: res.statusText,
            data: data
          });
        } catch (err) {
          sendResponse({ success: false, error: err.message });
        }
      })();
      return true; // Keep sendResponse open for async
    } else if (message.type === 'GET_PAGE_SUMMARY') {
      sendResponse({
        url: window.location.href,
        title: document.title,
        fieldsCount: recordedFieldsMap.size,
        fields: Array.from(recordedFieldsMap.values()),
        submitButton: recordedSubmitButton
      });
    }
    return true;
  });

  // ==========================================
  // 1. Selector & XPath Generators
  // ==========================================
  function getUniqueCssSelector(el) {
    if (!(el instanceof Element)) return '';
    if (el.id) {
      // Escape special characters in ID
      const safeId = CSS.escape(el.id);
      return `#${safeId}`;
    }

    if (el.name && (el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA')) {
      const form = el.closest('form');
      const formSelector = form && form.id ? `#${CSS.escape(form.id)} ` : '';
      return `${formSelector}${el.tagName.toLowerCase()}[name="${CSS.escape(el.name)}"]`;
    }

    if (el.getAttribute('data-testid')) {
      return `[data-testid="${CSS.escape(el.getAttribute('data-testid'))}"]`;
    }

    const path = [];
    while (el && el.nodeType === Node.ELEMENT_NODE) {
      let selector = el.nodeName.toLowerCase();
      if (el.id) {
        selector = '#' + CSS.escape(el.id);
        path.unshift(selector);
        break;
      } else {
        let sib = el, nth = 1;
        while ((sib = sib.previousElementSibling)) {
          if (sib.nodeName.toLowerCase() === selector) nth++;
        }
        if (nth !== 1) selector += `:nth-of-type(${nth})`;
      }
      path.unshift(selector);
      el = el.parentNode;
      if (path.length > 5) break; // Limit depth for readability
    }
    return path.join(' > ');
  }

  function getElementXPath(el) {
    if (!el || el.nodeType !== 1) return '';
    if (el.id) return `//*[@id="${el.id}"]`;
    if (el.name) return `//${el.tagName.toLowerCase()}[@name="${el.name}"]`;

    const parts = [];
    while (el && el.nodeType === 1) {
      let count = 0;
      let sibling = el.previousSibling;
      while (sibling) {
        if (sibling.nodeType === 1 && sibling.tagName === el.tagName) {
          count++;
        }
        sibling = sibling.previousSibling;
      }
      const tagName = el.tagName.toLowerCase();
      const pathIndex = count > 0 ? `[${count + 1}]` : '[1]';
      parts.unshift(tagName + pathIndex);
      el = el.parentNode;
      if (parts.length > 6) break;
    }
    return '/' + parts.join('/');
  }

  function findAssociatedLabel(el) {
    if (!el) return '';
    // 1. label[for="id"]
    if (el.id) {
      const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (label && label.innerText.trim()) return label.innerText.trim();
    }
    // 2. Closest parent <label>
    const parentLabel = el.closest('label');
    if (parentLabel && parentLabel.innerText.trim()) {
      return parentLabel.innerText.trim().replace(el.value || '', '').trim();
    }
    // 3. aria-label or placeholder
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label').trim();
    if (el.placeholder) return el.placeholder.trim();
    if (el.title) return el.title.trim();

    // 4. Preceding sibling label or span
    let prev = el.previousElementSibling;
    if (prev && (prev.tagName === 'LABEL' || prev.tagName === 'SPAN' || prev.tagName === 'DIV')) {
      const text = prev.innerText.trim();
      if (text && text.length < 50) return text;
    }

    return el.name || el.id || '';
  }

  // ==========================================
  // 2. Form Field Tracking (DOM Events)
  // ==========================================
  function handleFieldChange(e) {
    if (!isRecording) return;
    const el = e.target;
    if (!el || !(el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA')) {
      return;
    }

    // Skip hidden fields or passwords if not desired (we capture everything for automation)
    const type = (el.type || el.tagName).toLowerCase();
    const selector = getUniqueCssSelector(el);
    const xpath = getElementXPath(el);
    const label = findAssociatedLabel(el);

    let val = el.value;
    if (type === 'checkbox') val = el.checked;
    else if (type === 'radio') {
      if (!el.checked) return; // Only record selected radio
      val = el.value || true;
    }

    const fieldData = {
      tag: el.tagName.toLowerCase(),
      type: type,
      name: el.name || '',
      id: el.id || '',
      label: label,
      selector: selector,
      xpath: xpath,
      placeholder: el.placeholder || '',
      value: val,
      formId: el.form ? (el.form.id || el.form.name || '') : '',
      pageUrl: window.location.href,
      updatedAt: Date.now()
    };

    recordedFieldsMap.set(selector, fieldData);
    lastFormInteractionTime = Date.now();
    saveCurrentSessionToStorage();
    updateFloatingBadge();
  }

  document.addEventListener('input', handleFieldChange, true);
  document.addEventListener('change', handleFieldChange, true);
  document.addEventListener('focusout', handleFieldChange, true);

  // ==========================================
  // 3. Submit & Button Click Tracking
  // ==========================================
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button, input[type="submit"], [role="button"], a.btn, a.button');
    if (btn) {
      lastSubmitClickTime = Date.now();
      if (!isRecording) return;
      const text = (btn.innerText || btn.value || '').trim();
      const selector = getUniqueCssSelector(btn);
      const xpath = getElementXPath(btn);

      recordedSubmitButton = {
        text: text,
        selector: selector,
        xpath: xpath,
        type: btn.type || 'button',
        timestamp: Date.now()
      };

      saveCurrentSessionToStorage();
      console.log('[FormAPIInterceptor] Submit action detected:', text, selector);
    }
  }, true);

  // ==========================================
  // 4. API Calls Interception (Custom Event)
  // ==========================================
  window.addEventListener('__FORM_API_INTERCEPTED__', (event) => {
    try {
      const apiData = JSON.parse(event.detail);
      const now = Date.now();

      // Smart Form-Correlation & Categorization
      const isRecentFormInput = (now - lastFormInteractionTime) < 4500;
      const isRecentSubmitClick = (now - lastSubmitClickTime) < 3500;
      const hasFormElements = recordedFieldsMap.size > 0;
      const isFormTriggered = (isRecentSubmitClick || isRecentFormInput) && hasFormElements;

      if (isFormTriggered) {
        apiData.isForm = true;
        apiData.category = 'FORM';
        apiData.badge = '📝 FORM';
        apiData.associatedFormSnapshot = Array.from(recordedFieldsMap.values());
        apiData.associatedSubmitButton = recordedSubmitButton;
      } else {
        apiData.isForm = false;
        apiData.associatedFormSnapshot = null;
        apiData.associatedSubmitButton = null;
        if (apiData.method === 'GET') {
          apiData.category = 'GET';
          apiData.badge = '📥 GET';
        } else if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(apiData.method)) {
          apiData.category = 'POST';
          apiData.badge = '📤 ' + apiData.method;
        } else {
          apiData.category = 'OTHER';
          apiData.badge = '🌐 ' + apiData.method;
        }
      }

      console.log(`[FormAPIHarvester:${apiData.category}]`, apiData.method, apiData.url);

      // Always maintain rolling liveApiBuffer (last 50 calls) for instant inspection
      chrome.storage.local.get(['liveApiBuffer', 'activeSession'], (res) => {
        const liveBuffer = Array.isArray(res.liveApiBuffer) ? res.liveApiBuffer : [];
        liveBuffer.unshift(apiData);
        if (liveBuffer.length > 60) liveBuffer.length = 60;

        const storageUpdates = { liveApiBuffer: liveBuffer };

        // If recording is active, append to activeSession
        if (isRecording && res.activeSession) {
          const session = res.activeSession;
          if (!Array.isArray(session.apiCalls)) session.apiCalls = [];
          session.apiCalls.push(apiData);
          session.formFields = Array.from(recordedFieldsMap.values());
          if (apiData.clientAuth && Object.keys(apiData.clientAuth).length > 0) {
            session.clientAuth = Object.assign(session.clientAuth || {}, apiData.clientAuth);
          }
          storageUpdates.activeSession = session;
        }

        chrome.storage.local.set(storageUpdates, () => {
          if (isRecording) updateFloatingBadge();
        });
      });
    } catch (err) {
      console.warn('[FormAPIInterceptor] Error receiving API event:', err);
    }
  });

  // Sync to storage
  function saveCurrentSessionToStorage() {
    chrome.storage.local.get(['activeSession'], (res) => {
      if (!res.activeSession) return;
      const session = res.activeSession;
      session.formFields = Array.from(recordedFieldsMap.values());
      session.submitButton = recordedSubmitButton;
      chrome.storage.local.set({ activeSession: session });
    });
  }

  // ==========================================
  // 5. Auto-Fill & Replay Engine
  // ==========================================
  function executeAutoFill(fields, autoSubmit = false, submitSelector = null) {
    if (!Array.isArray(fields) || fields.length === 0) {
      return { success: false, error: 'No fields provided' };
    }

    let filledCount = 0;
    const errors = [];

    fields.forEach(f => {
      let el = null;
      // Try ID
      if (f.id) el = document.getElementById(f.id);
      // Try Selector
      if (!el && f.selector) {
        try { el = document.querySelector(f.selector); } catch (_) {}
      }
      // Try Name
      if (!el && f.name) {
        try { el = document.querySelector(`[name="${CSS.escape(f.name)}"]`); } catch (_) {}
      }
      // Try XPath
      if (!el && f.xpath) {
        try {
          const res = document.evaluate(f.xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
          el = res.singleNodeValue;
        } catch (_) {}
      }

      if (el) {
        try {
          el.focus();
          if (f.type === 'checkbox') {
            el.checked = Boolean(f.value);
          } else if (f.type === 'radio') {
            if (el.value === f.value || f.value === true) el.checked = true;
          } else {
            el.value = f.value !== undefined ? f.value : '';
          }

          // Trigger standard reactive framework events
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          el.dispatchEvent(new Event('blur', { bubbles: true }));
          filledCount++;
        } catch (err) {
          errors.push(`Field ${f.name || f.id}: ${err.message}`);
        }
      } else {
        errors.push(`Element not found for ${f.name || f.id || f.selector}`);
      }
    });

    if (autoSubmit) {
      setTimeout(() => {
        let btn = null;
        if (submitSelector) {
          try { btn = document.querySelector(submitSelector); } catch (_) {}
        }
        if (!btn) {
          btn = document.querySelector('button[type="submit"], input[type="submit"]');
        }
        if (btn) {
          btn.click();
        }
      }, 300);
    }

    return {
      success: filledCount > 0,
      filledCount: filledCount,
      totalFields: fields.length,
      errors: errors
    };
  }

  // ==========================================
  // 6. Floating On-Screen Recording Badge
  // ==========================================
  function showFloatingBadge() {
    if (floatingBadge) return;
    floatingBadge = document.createElement('div');
    floatingBadge.id = '__form_api_interceptor_badge__';
    floatingBadge.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="display:inline-block; width:10px; height:10px; background:#EF4444; border-radius:50%; animation: pulse 1.5s infinite;"></span>
        <strong style="color: #fff; font-size: 12px; font-family: system-ui;">REC: Interceptor</strong>
      </div>
      <div id="__badge_stats__" style="color: #94A3B8; font-size: 11px; margin-top: 2px;">
        ฟอร์ม: 0 | API: 0
      </div>
    `;

    Object.assign(floatingBadge.style, {
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      zIndex: '2147483647',
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      backdropFilter: 'blur(8px)',
      border: '1px solid rgba(14, 165, 233, 0.4)',
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.5)',
      borderRadius: '10px',
      padding: '8px 14px',
      cursor: 'pointer',
      userSelect: 'none',
      transition: 'transform 0.2s ease'
    });

    floatingBadge.addEventListener('click', () => {
      chrome.runtime.sendMessage({ type: 'OPEN_SIDEPANEL' });
    });

    document.body.appendChild(floatingBadge);
  }

  function updateFloatingBadge() {
    if (!floatingBadge) return;
    const stats = floatingBadge.querySelector('#__badge_stats__');
    if (!stats) return;

    chrome.storage.local.get(['activeSession'], (res) => {
      const formCount = recordedFieldsMap.size;
      const apiCount = (res.activeSession && res.activeSession.apiCalls) ? res.activeSession.apiCalls.length : 0;
      stats.innerText = `ฟอร์ม: ${formCount} ช่อง | API: ${apiCount} รายการ`;
    });
  }

  function hideFloatingBadge() {
    if (floatingBadge && floatingBadge.parentNode) {
      floatingBadge.parentNode.removeChild(floatingBadge);
      floatingBadge = null;
    }
  }

})();
