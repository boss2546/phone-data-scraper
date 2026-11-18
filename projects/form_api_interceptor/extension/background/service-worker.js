// background/service-worker.js
// Form & API Interceptor Background Service Worker (Manifest V3)

chrome.runtime.onInstalled.addListener(async () => {
  console.log('[FormAPIInterceptor] Background service worker installed.');
  const initialData = await chrome.storage.local.get([
    'isRecording',
    'activeSession',
    'recordedSessions',
    'webhookUrl',
    'autoWebhook'
  ]);

  const updates = {};
  if (initialData.isRecording === undefined) updates.isRecording = false;
  if (!initialData.activeSession) updates.activeSession = null;
  if (!Array.isArray(initialData.recordedSessions)) updates.recordedSessions = [];
  if (!initialData.webhookUrl) updates.webhookUrl = 'http://127.0.0.1:8091/api/capture';
  if (initialData.autoWebhook === undefined) updates.autoWebhook = false;

  if (Object.keys(updates).length > 0) {
    await chrome.storage.local.set(updates);
  }
});

// Broadcast state change to all tabs
async function broadcastToTabs(message) {
  try {
    const tabs = await chrome.tabs.query({});
    for (const tab of tabs) {
      if (tab.id && tab.url && !tab.url.startsWith('chrome://')) {
        try {
          await chrome.tabs.sendMessage(tab.id, message);
        } catch (_) {
          // Tab might not have content script injected yet, ignore
        }
      }
    }
  } catch (err) {
    console.warn('[FormAPIInterceptor] Broadcast error:', err);
  }
}

// =========================================================================
// Cookie & Auth Token Extraction Engine (Manifest V3)
// =========================================================================

// Helper: Get all cookies for a given URL (including HttpOnly & Secure)
async function getCookiesForUrl(url) {
  if (!url || !chrome.cookies) return { cookies: [], cookieString: '', cookieMap: {} };
  try {
    const cookies = await chrome.cookies.getAll({ url: url });
    const cookieMap = {};
    const parts = [];
    cookies.forEach(c => {
      cookieMap[c.name] = c.value;
      parts.push(`${c.name}=${c.value}`);
    });
    return {
      cookies: cookies.map(c => ({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        httpOnly: c.httpOnly,
        secure: c.secure,
        sameSite: c.sameSite,
        session: c.session,
        expirationDate: c.expirationDate || null
      })),
      cookieString: parts.join('; '),
      cookieMap: cookieMap
    };
  } catch (err) {
    console.warn('[FormAPIInterceptor] Cookie fetch error:', err);
    return { cookies: [], cookieString: '', cookieMap: {} };
  }
}

// Helper: Extract Auth Tokens, Bearer, and API Keys from API calls
function extractAuthSummary(apiCalls, cookieData) {
  const bearerTokens = new Set();
  const apiKeys = {};
  const customAuthHeaders = {};

  if (Array.isArray(apiCalls)) {
    apiCalls.forEach(call => {
      const headers = call.headers || call.requestHeaders || {};
      for (const [key, rawVal] of Object.entries(headers)) {
        const lowerKey = key.toLowerCase();
        const val = String(rawVal);
        if (lowerKey === 'authorization') {
          if (val.toLowerCase().startsWith('bearer ')) {
            bearerTokens.add(val.substring(7).trim());
          } else {
            customAuthHeaders[key] = val;
          }
        } else if (lowerKey.includes('api-key') || lowerKey.includes('apikey') || lowerKey === 'x-api-key') {
          apiKeys[key] = val;
        } else if (lowerKey.includes('auth') || lowerKey.includes('token') || lowerKey === 'x-access-token') {
          customAuthHeaders[key] = val;
        }
      }
    });
  }

  const cookiesList = (cookieData && cookieData.cookies) ? cookieData.cookies : [];
  return {
    bearerTokens: Array.from(bearerTokens),
    apiKeys: apiKeys,
    customAuthHeaders: customAuthHeaders,
    cookiesCount: cookiesList.length,
    cookieNames: cookiesList.map(c => c.name)
  };
}

// Handle runtime messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    switch (message.type) {
      case 'START_RECORDING': {
        const sessionId = 'session_' + Date.now();
        let targetUrl = message.url || (sender.tab ? sender.tab.url : '');
        let targetTitle = message.title || (sender.tab ? sender.tab.title : '');

        if (!targetUrl) {
          try {
            const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (activeTab) {
              targetUrl = activeTab.url;
              targetTitle = activeTab.title;
            }
          } catch (_) {}
        }

        // Auto-capture cookies for this URL right at start!
        const cookieData = await getCookiesForUrl(targetUrl);

        const activeSession = {
          id: sessionId,
          startTime: Date.now(),
          url: targetUrl,
          title: targetTitle,
          cookies: cookieData.cookies,
          cookieString: cookieData.cookieString,
          cookieMap: cookieData.cookieMap,
          authSummary: {
            bearerTokens: [],
            apiKeys: {},
            customAuthHeaders: {},
            cookiesCount: cookieData.cookies.length,
            cookieNames: cookieData.cookies.map(c => c.name)
          },
          formFields: [],
          apiCalls: [],
          status: 'RECORDING'
        };

        await chrome.storage.local.set({
          isRecording: true,
          activeSession: activeSession
        });

        await broadcastToTabs({
          type: 'RECORDING_STATE_CHANGED',
          isRecording: true,
          sessionId: sessionId
        });

        // Update badge
        await chrome.action.setBadgeText({ text: 'REC' });
        await chrome.action.setBadgeBackgroundColor({ color: '#EF4444' });

        sendResponse({ success: true, sessionId: sessionId, cookiesCaptured: cookieData.cookies.length });
        break;
      }

      case 'STOP_RECORDING': {
        const { activeSession, recordedSessions = [] } = await chrome.storage.local.get([
          'activeSession',
          'recordedSessions'
        ]);

        if (activeSession) {
          activeSession.endTime = Date.now();
          activeSession.status = 'COMPLETED';

          // Re-fetch fresh cookies upon completion (to capture login/session cookies created during interaction)
          if (activeSession.url) {
            const freshCookies = await getCookiesForUrl(activeSession.url);
            if (freshCookies.cookies.length > 0) {
              activeSession.cookies = freshCookies.cookies;
              activeSession.cookieString = freshCookies.cookieString;
              activeSession.cookieMap = freshCookies.cookieMap;
            }
          }

          // Extract API keys, Bearer tokens, and Auth headers from captured calls
          activeSession.authSummary = extractAuthSummary(activeSession.apiCalls, {
            cookies: activeSession.cookies || []
          });

          recordedSessions.unshift(activeSession);
          // Keep maximum 50 sessions
          if (recordedSessions.length > 50) {
            recordedSessions.length = 50;
          }

          await chrome.storage.local.set({
            isRecording: false,
            activeSession: null,
            recordedSessions: recordedSessions
          });

          // Forward to local webhook if configured
          const { autoWebhook, webhookUrl } = await chrome.storage.local.get(['autoWebhook', 'webhookUrl']);
          if (autoWebhook && webhookUrl) {
            try {
              fetch(webhookUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(activeSession)
              }).catch(() => {});
            } catch (_) {}
          }
        } else {
          await chrome.storage.local.set({ isRecording: false });
        }

        await broadcastToTabs({
          type: 'RECORDING_STATE_CHANGED',
          isRecording: false
        });

        await chrome.action.setBadgeText({ text: '' });
        sendResponse({ success: true, savedSession: activeSession });
        break;
      }

      case 'CAPTURE_CURRENT_AUTH': {
        // Direct one-click capture of cookies & auth for active tab
        try {
          const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
          if (!activeTab || !activeTab.url) {
            sendResponse({ success: false, error: 'No active tab found' });
            return;
          }
          const cookieData = await getCookiesForUrl(activeTab.url);
          sendResponse({
            success: true,
            url: activeTab.url,
            title: activeTab.title,
            cookies: cookieData.cookies,
            cookieString: cookieData.cookieString,
            cookieMap: cookieData.cookieMap,
            count: cookieData.cookies.length
          });
        } catch (err) {
          sendResponse({ success: false, error: err.message });
        }
        break;
      }

      case 'GET_STATUS': {
        const data = await chrome.storage.local.get([
          'isRecording',
          'activeSession',
          'recordedSessions',
          'webhookUrl',
          'autoWebhook'
        ]);
        sendResponse({ success: true, data });
        break;
      }

      case 'CLEAR_LIVE_BUFFER': {
        await chrome.storage.local.set({ liveApiBuffer: [] });
        sendResponse({ success: true });
        break;
      }

      case 'OPEN_SIDEPANEL': {
        let tabId = sender.tab ? sender.tab.id : null;
        let windowId = sender.tab ? sender.tab.windowId : null;

        if (!tabId || !windowId) {
          const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
          if (activeTab) {
            tabId = activeTab.id;
            windowId = activeTab.windowId;
          }
        }

        if (windowId && chrome.sidePanel && chrome.sidePanel.open) {
          try {
            await chrome.sidePanel.open({ windowId: windowId });
            sendResponse({ success: true });
          } catch (err) {
            sendResponse({ success: false, error: err.message });
          }
        } else {
          sendResponse({ success: false, error: 'SidePanel API not available' });
        }
        break;
      }

      case 'CLEAR_RECORDINGS': {
        await chrome.storage.local.set({ recordedSessions: [] });
        sendResponse({ success: true });
        break;
      }

      default:
        sendResponse({ success: false, error: 'Unknown message type' });
    }
  })();

  return true; // Keep message channel open for async response
});
