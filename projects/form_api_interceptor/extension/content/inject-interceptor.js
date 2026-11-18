// content/inject-interceptor.js
// Runs in MAIN world (Page Context)
// Intercepts window.fetch and window.XMLHttpRequest without interfering with page operations

(function() {
  if (window.__FORM_API_INTERCEPTOR_INJECTED__) return;
  window.__FORM_API_INTERCEPTOR_INJECTED__ = true;

  console.log('[FormAPIInterceptor:MAIN] Network hook active.');

  function shouldIgnoreUrl(url) {
    if (!url) return true;
    const lower = url.toLowerCase();
    // Ignore static asset requests to keep data clean
    return lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg') ||
           lower.endsWith('.gif') || lower.endsWith('.webp') || lower.endsWith('.svg') ||
           lower.endsWith('.ico') || lower.endsWith('.css') || lower.endsWith('.woff') ||
           lower.endsWith('.woff2') || lower.endsWith('.ttf');
  }

  function extractClientAuthTokens() {
    const tokens = {};
    try {
      if (document.cookie) {
        tokens.documentCookie = document.cookie;
      }
      if (window.localStorage) {
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key) {
            const lower = key.toLowerCase();
            if (lower.includes('token') || lower.includes('auth') || lower.includes('jwt') || lower.includes('key')) {
              tokens['local_' + key] = localStorage.getItem(key);
            }
          }
        }
      }
      if (window.sessionStorage) {
        for (let i = 0; i < sessionStorage.length; i++) {
          const key = sessionStorage.key(i);
          if (key) {
            const lower = key.toLowerCase();
            if (lower.includes('token') || lower.includes('auth') || lower.includes('jwt') || lower.includes('key')) {
              tokens['session_' + key] = sessionStorage.getItem(key);
            }
          }
        }
      }
    } catch (_) {}
    return tokens;
  }

  function notifyInterceptor(data) {
    try {
      data.clientAuth = extractClientAuthTokens();
      window.dispatchEvent(new CustomEvent('__FORM_API_INTERCEPTED__', {
        detail: JSON.stringify(data)
      }));
    } catch (err) {
      console.warn('[FormAPIInterceptor] Event dispatch error:', err);
    }
  }

  function parseBody(body) {
    if (!body) return null;
    if (typeof body === 'string') {
      try {
        return JSON.parse(body);
      } catch (_) {
        return body;
      }
    }
    if (body instanceof FormData) {
      const obj = {};
      body.forEach((value, key) => {
        if (value instanceof File) {
          obj[key] = `[File: ${value.name} (${value.size} bytes, ${value.type})]`;
        } else {
          obj[key] = value;
        }
      });
      return { _formData: obj };
    }
    if (body instanceof URLSearchParams) {
      const obj = {};
      body.forEach((val, key) => { obj[key] = val; });
      return { _urlSearchParams: obj, raw: body.toString() };
    }
    try {
      return JSON.parse(JSON.stringify(body));
    } catch (_) {
      return String(body);
    }
  }

  function extractHeaders(headersInput) {
    const result = {};
    if (!headersInput) return result;

    if (headersInput instanceof Headers) {
      headersInput.forEach((value, key) => {
        result[key] = value;
      });
    } else if (Array.isArray(headersInput)) {
      headersInput.forEach(([key, val]) => {
        result[key] = val;
      });
    } else if (typeof headersInput === 'object') {
      Object.assign(result, headersInput);
    }
    return result;
  }

  function extractQueryParams(fullUrl) {
    try {
      const u = new URL(fullUrl, window.location.href);
      const params = {};
      u.searchParams.forEach((v, k) => { params[k] = v; });
      return params;
    } catch (_) {
      return {};
    }
  }

  // ==========================================
  // 1. Hook window.fetch
  // ==========================================
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const startTime = Date.now();
    let url = '';
    let method = 'GET';
    let requestHeaders = {};
    let requestBody = null;

    try {
      if (typeof args[0] === 'string') {
        url = args[0];
      } else if (args[0] && args[0].url) {
        url = args[0].url;
        method = args[0].method || 'GET';
      }

      if (args[1]) {
        if (args[1].method) method = args[1].method.toUpperCase();
        if (args[1].headers) requestHeaders = extractHeaders(args[1].headers);
        if (args[1].body) requestBody = parseBody(args[1].body);
      }
    } catch (e) {
      console.warn('[FormAPIInterceptor] Error parsing fetch args:', e);
    }

    try {
      // Execute original fetch
      const response = await originalFetch.apply(this, args);

      if (!shouldIgnoreUrl(url)) {
        try {
          const clone = response.clone();
          clone.text().then(text => {
            let parsedResponse = text;
            try {
              parsedResponse = JSON.parse(text);
            } catch (_) {}

            const responseHeaders = {};
            clone.headers.forEach((v, k) => { responseHeaders[k] = v; });

            const resolvedUrl = url.startsWith('http') ? url : new URL(url, window.location.href).href;
            notifyInterceptor({
              type: 'FETCH',
              url: resolvedUrl,
              pathname: new URL(resolvedUrl).pathname,
              queryParams: extractQueryParams(resolvedUrl),
              method: method,
              requestHeaders: requestHeaders,
              requestBody: requestBody,
              status: response.status,
              statusText: response.statusText,
              responseHeaders: responseHeaders,
              responseBody: parsedResponse,
              durationMs: Date.now() - startTime,
              timestamp: Date.now()
            });
          }).catch(() => {});
        } catch (_) {}
      }

      return response;
    } catch (err) {
      if (!shouldIgnoreUrl(url)) {
        notifyInterceptor({
          type: 'FETCH',
          url: url.startsWith('http') ? url : new URL(url, window.location.href).href,
          method: method,
          requestHeaders: requestHeaders,
          requestBody: requestBody,
          error: err.message,
          durationMs: Date.now() - startTime,
          timestamp: Date.now()
        });
      }
      throw err;
    }
  };

  // ==========================================
  // 2. Hook XMLHttpRequest
  // ==========================================
  const originalXhrOpen = XMLHttpRequest.prototype.open;
  const originalXhrSend = XMLHttpRequest.prototype.send;
  const originalXhrSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;

  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this._interceptorData = {
      type: 'XHR',
      method: (method || 'GET').toUpperCase(),
      url: url ? (url.startsWith('http') ? url : new URL(url, window.location.href).href) : '',
      requestHeaders: {},
      requestBody: null,
      startTime: Date.now()
    };
    return originalXhrOpen.apply(this, [method, url, ...rest]);
  };

  XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
    if (this._interceptorData && this._interceptorData.requestHeaders) {
      this._interceptorData.requestHeaders[header] = value;
    }
    return originalXhrSetRequestHeader.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function(body) {
    if (this._interceptorData) {
      this._interceptorData.requestBody = parseBody(body);
      const data = this._interceptorData;

      this.addEventListener('load', function() {
        if (!shouldIgnoreUrl(data.url)) {
          let responseBody = this.responseText;
          try {
            responseBody = JSON.parse(this.responseText);
          } catch (_) {}

          notifyInterceptor({
            type: 'XHR',
            url: data.url,
            pathname: new URL(data.url).pathname,
            queryParams: extractQueryParams(data.url),
            method: data.method,
            requestHeaders: data.requestHeaders,
            requestBody: data.requestBody,
            status: this.status,
            statusText: this.statusText,
            responseBody: responseBody,
            durationMs: Date.now() - data.startTime,
            timestamp: Date.now()
          });
        }
      });

      this.addEventListener('error', function() {
        if (!shouldIgnoreUrl(data.url)) {
          notifyInterceptor({
            type: 'XHR',
            url: data.url,
            method: data.method,
            requestHeaders: data.requestHeaders,
            requestBody: data.requestBody,
            error: 'Network Error',
            durationMs: Date.now() - data.startTime,
            timestamp: Date.now()
          });
        }
      });
    }

    return originalXhrSend.apply(this, arguments);
  };

})();
