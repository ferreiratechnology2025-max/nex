/**
 * NEX CHAT — Frontend Controller v2
 * Comunicação com API local · sem textos hardcoded
 */

(function () {
    'use strict';

    // ================================================================
    // State
    // ================================================================

    const STATE = {
        isStreaming: false,
        ws: null,
        statsInterval: null,
    };

    // ================================================================
    // DOM refs
    // ================================================================

    const $ = (sel) => document.querySelector(sel);

    const dom = {
        sidebar:       $('#sidebar'),
        sidebarToggle: $('#sidebarToggle'),
        menuBtn:       $('#menuBtn'),
        newSessionBtn: $('#newSessionBtn'),
        sessionsList:  $('#sessionsList'),
        chatMessages:  $('#chatMessages'),
        welcomeScreen: $('#welcomeScreen'),
        messageInput:  $('#messageInput'),
        sendBtn:       $('#sendBtn'),
        charCount:     $('#charCount'),
        resetBtn:      $('#resetBtn'),
        clearCacheBtn: $('#clearCacheBtn'),
        uploadBtn:     $('#uploadBtn'),
        fileInput:     $('#fileInput'),
        webSearchToggle: $('#webSearchToggle'),
        memoryToggle:  $('#memoryToggle'),
        notification:  $('#notification'),
        statBackend:   $('#statBackend'),
        statSessions:  $('#statSessions'),
        statUptime:    $('#statUptime'),
        statusDot:     $('#statusDot'),
        badgeModel:    $('#badgeModel'),
    };

    // ================================================================
    // API helpers
    // ================================================================

    async function api(method, path, body) {
        const opts = { method, headers: { 'Content-Type': 'application/json' } };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(path, opts);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    }

    // ================================================================
    // Notifications / Toast
    // ================================================================

    function notify(msg, type) {
        const el = dom.notification;
        el.textContent = msg;
        el.className = 'toast show' + (type ? ' ' + type : '');
        clearTimeout(notify._t);
        notify._t = setTimeout(function() { el.className = 'toast'; }, 3200);
    }

    // ================================================================
    // Rendering helpers
    // ================================================================

    function hideWelcome() {
        if (dom.welcomeScreen) dom.welcomeScreen.style.display = 'none';
    }

    function timeStr() {
        return new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    }

    function escapeHtml(str) {
        var m = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return str.replace(/[&<>"']/g, function(c) { return m[c]; });
    }

    function addMessage(role, text) {
        hideWelcome();
        var msg = document.createElement('div');
        msg.className = 'message ' + role;
        var initial = role === 'user' ? 'U' : 'N';
        msg.innerHTML = 
            '<div class="message-avatar">' + initial + '</div>' +
            '<div class="message-body">' +
                '<div class="message-content">' + escapeHtml(text) + '</div>' +
                '<div class="message-meta">' +
                    '<span class="message-time">' + timeStr() + '</span>' +
                '</div>' +
            '</div>';
        dom.chatMessages.appendChild(msg);
        scrollToBottom();
        return msg;
    }

    function addTypingIndicator() {
        hideWelcome();
        var el = document.createElement('div');
        el.className = 'message assistant';
        el.id = 'typingMsg';
        el.innerHTML = 
            '<div class="message-avatar">N</div>' +
            '<div class="message-body">' +
                '<div class="typing-indicator"><span></span><span></span><span></span></div>' +
            '</div>';
        dom.chatMessages.appendChild(el);
        scrollToBottom();
        return el;
    }

    function removeTypingIndicator() {
        var el = document.getElementById('typingMsg');
        if (el) el.remove();
    }

    function replaceTypingWithMessage(text) {
        removeTypingIndicator();
        addMessage('assistant', text);
    }

    function scrollToBottom() {
        requestAnimationFrame(function() {
            dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
        });
    }

    // ================================================================
    // WebSocket
    // ================================================================

    function connectWebSocket() {
        if (STATE.ws && STATE.ws.readyState === WebSocket.OPEN) return STATE.ws;
        var wsUrl = (location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + location.host + '/ws/chat';
        var ws = new WebSocket(wsUrl);
        ws.onopen  = function() { console.log('[nex] ws open'); updateStatusDot(true); };
        ws.onerror = function(e) { console.warn('[nex] ws error', e); };
        ws.onclose = function() { STATE.ws = null; updateStatusDot(false); };
        STATE.ws = ws;
        return ws;
    }
    
    function updateStatusDot(online) {
        if (dom.statusDot) {
            dom.statusDot.className = 'status-dot ' + (online ? 'online' : 'error');
        }
    }

    // ================================================================
    // Upload
    // ================================================================

    async function handleFileUpload(file) {
        if (!file) return;
        var formData = new FormData();
        formData.append('file', file);
        formData.append('summarize', 'true');
        addMessage('user', '[📄 Enviando: ' + file.name + ']');
        addTypingIndicator();
        try {
            var res = await fetch('/upload', { method: 'POST', body: formData });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            var data = await res.json();
            removeTypingIndicator();
            var msg = '📄 Arquivo **' + data.filename + '** carregado (' + (data.size_chars || '?') + ' chars)';
            if (data.summary) msg += '\n\n📝 ' + data.summary;
            addMessage('assistant', msg);
            notify(data.filename + ' carregado', 'success');
        } catch(e) {
            removeTypingIndicator();
            addMessage('assistant', '❌ Erro ao enviar arquivo: ' + e.message);
            notify('Falha no upload', 'error');
        }
    }

    // ================================================================
    // Send message
    // ================================================================

    async function sendMessage() {
        var text = dom.messageInput.value.trim();
        if (!text || STATE.isStreaming) return;

        STATE.isStreaming = true;
        dom.messageInput.value = '';
        autoResizeInput();
        updateSendBtn();
        addMessage('user', text);
        addTypingIndicator();

        var useWebSearch = dom.webSearchToggle ? dom.webSearchToggle.checked : false;
        var useMemory = dom.memoryToggle ? dom.memoryToggle.checked : true;

        try {
            var ws = connectWebSocket();

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ text: text, use_web_search: useWebSearch }));
                var response = await new Promise(function(resolve, reject) {
                    var timeout = setTimeout(function() { reject(new Error('Timeout')); }, 60000);
                    ws.onmessage = function(event) {
                        clearTimeout(timeout);
                        try {
                            var data = JSON.parse(event.data);
                            if (data.error) {
                                reject(new Error(data.error));
                            } else {
                                resolve(data.response || data.text || data);
                            }
                        } catch(e) {
                            resolve(event.data);
                        }
                    };
                    ws.onerror = function(e) { clearTimeout(timeout); reject(e); };
                });
                removeTypingIndicator();
                addMessage('assistant', response);
            } else {
                throw new Error('ws not ready');
            }

        } catch(e) {
            try {
                var data = await api('POST', '/ask', {
                    text: text,
                    use_web_search: useWebSearch,
                    max_tokens: 2048,
                    temperature: 0.7,
                    stream: false,
                    use_memory: useMemory
                });
                replaceTypingWithMessage(data.response);
            } catch(e2) {
                replaceTypingWithMessage('Erro ao comunicar com o servidor.');
                notify('Falha na comunicação: ' + e2.message, 'error');
            }
        } finally {
            STATE.isStreaming = false;
            updateSendBtn();
        }
    }

    // ================================================================
    // Sessions
    // ================================================================

    async function loadSessions() {
        if (dom.sessionsList) {
            dom.sessionsList.innerHTML = '<div style="color:var(--text-2);font-size:0.75rem;padding:6px 4px;">Memória persistente ativa</div>';
        }
    }

    async function newSession() {
        dom.chatMessages.innerHTML = '';
        location.reload();
    }

    // ================================================================
    // Stats
    // ================================================================

    async function loadStats() {
        try {
            var data = await api('GET', '/health');
            var model = data.model || '—';

            if (dom.statBackend)  dom.statBackend.textContent  = model;
            if (dom.statSessions) dom.statSessions.textContent = data.memory_count || 0;
            if (dom.statUptime)  dom.statUptime.textContent  = data.status || 'OK';
            if (dom.badgeModel)  dom.badgeModel.textContent  = model;

            if (dom.statusDot) {
                dom.statusDot.className = 'status-dot ' + (data.status === 'ok' || data.status === 'healthy' ? 'online' : 'error');
            }

        } catch(_) {}
    }

    // ================================================================
    // Input handling
    // ================================================================

    function autoResizeInput() {
        var el = dom.messageInput;
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }

    function updateSendBtn() {
        var hasText = dom.messageInput.value.trim().length > 0;
        dom.sendBtn.disabled = !hasText || STATE.isStreaming;
    }

    function updateCharCount() {
        var len = dom.messageInput.value.length;
        dom.charCount.textContent = len + '/4000';
    }

    // ================================================================
    // Event Bindings
    // ================================================================

    function init() {
        // Input events
        dom.messageInput.addEventListener('input', function() {
            autoResizeInput();
            updateSendBtn();
            updateCharCount();
        });

        dom.messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        dom.sendBtn.addEventListener('click', sendMessage);

        // Sidebar toggle
        dom.sidebarToggle.addEventListener('click', function() {
            dom.sidebar.classList.toggle('collapsed');
        });

        dom.menuBtn.addEventListener('click', function() {
            dom.sidebar.classList.toggle('open');
        });

        // Close sidebar on outside click (mobile)
        dom.chatMessages.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                dom.sidebar.classList.remove('open');
            }
        });

        // New session
        if (dom.newSessionBtn) {
            dom.newSessionBtn.addEventListener('click', newSession);
        }

        // Reset button
        if (dom.resetBtn) {
            dom.resetBtn.addEventListener('click', function() {
                dom.chatMessages.innerHTML = '';
                notify('Conversa limpa', 'success');
            });
        }

        // Upload button
        if (dom.uploadBtn && dom.fileInput) {
            dom.uploadBtn.addEventListener('click', function() {
                dom.fileInput.click();
            });
            dom.fileInput.addEventListener('change', function(e) {
                var file = e.target.files[0];
                if (file) handleFileUpload(file);
                dom.fileInput.value = '';
            });
        }

        // Clear cache
        if (dom.clearCacheBtn) {
            dom.clearCacheBtn.addEventListener('click', function() {
                notify('A memória é persistente e não precisa ser limpa', 'success');
            });
        }

        // Suggestion chips
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('suggestion-chip')) {
                dom.messageInput.value = e.target.dataset.text || e.target.textContent;
                autoResizeInput();
                updateSendBtn();
                updateCharCount();
                dom.messageInput.focus();
            }
        });

        // Initialize
        loadSessions();
        loadStats();
        if (STATE.statsInterval) clearInterval(STATE.statsInterval);
        STATE.statsInterval = setInterval(loadStats, 30000);

        // Try connect WS for status dot
        try { connectWebSocket(); } catch(_) {}

        // Focus input
        dom.messageInput.focus();
    }

    // ================================================================
    // Boot
    // ================================================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();