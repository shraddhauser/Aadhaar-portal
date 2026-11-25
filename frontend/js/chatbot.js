/**
 * ================================================================
 * Aadhaar Analytics Portal — USTAD Chatbot Engine
 * Anthropic Claude-powered AI assistant via secure backend proxy
 * ================================================================
 *
 * Architecture:
 *   User types question → Frontend sends to /api/chat/ask →
 *   Backend fetches live data, builds system prompt, calls Anthropic Claude →
 *   Response returned to frontend. API key never touches client.
 */

/* ──────────────────────────────────────────────────────────────
   1. STATE & CONFIG
   ────────────────────────────────────────────────────────────── */

const ChatBot = (() => {
  // Private state
  let isOpen = false;
  let isLoading = false;
  let conversationHistory = [];
  let chipsShown = true;

  const QUICK_REPLIES = [
    'Coverage gaps today',
    'Why are biometric scores 0%?',
    'Explain the rejection rate',
    'Recommend action for Mumbai',
    'How to export PDF?',
  ];

  /* ──────────────────────────────────────────────────────────────
     2. DOM INJECTION — Create chatbot UI on load
     ────────────────────────────────────────────────────────────── */

  function injectHTML() {
    const chatHTML = `
      <!-- Floating Label -->
      <div class="chatbot-label" id="chatbotLabel">✨ Ask USTAD</div>

      <!-- Floating Toggle Button -->
      <button class="chatbot-toggle" id="chatbotToggle" title="Ask USTAD" aria-label="Open USTAD Chat">
        <span class="chat-icon">💬</span>
        <span class="close-icon">✕</span>
      </button>

      <!-- Chat Panel -->
      <div class="chatbot-panel" id="chatbotPanel" role="dialog" aria-label="USTAD Chat Assistant">
        <!-- Header -->
        <div class="chatbot-header">
          <div class="chatbot-avatar">U</div>
          <div class="chatbot-header-text">
            <div class="chatbot-header-title">USTAD</div>
            <div class="chatbot-header-sub">
              <span class="live-dot"></span>
              AI Analytics Assistant · Anthropic Claude (live)
            </div>
          </div>
          <button class="chatbot-header-close" id="chatbotClose" title="Close chat" aria-label="Close chat">✕</button>
        </div>

        <!-- Messages Area -->
        <div class="chatbot-messages" id="chatbotMessages">
          <!-- Welcome message injected on first open -->
        </div>

        <!-- Input Area -->
        <div class="chatbot-input-area">
          <div class="chatbot-input-wrap">
            <textarea
              class="chatbot-input"
              id="chatbotInput"
              placeholder="Ask about enrollments, anomalies, trends..."
              rows="1"
              aria-label="Type your question"
            ></textarea>
          </div>
          <button class="chatbot-send" id="chatbotSend" title="Send message" aria-label="Send">
            ➤
          </button>
        </div>
      </div>
    `;

    const container = document.createElement('div');
    container.id = 'chatbot-container';
    container.innerHTML = chatHTML;
    document.body.appendChild(container);
  }


  /* ──────────────────────────────────────────────────────────────
     3. EVENT BINDING
     ────────────────────────────────────────────────────────────── */

  function bindEvents() {
    const toggle      = document.getElementById('chatbotToggle');
    const closeBtn    = document.getElementById('chatbotClose');
    const sendBtn     = document.getElementById('chatbotSend');
    const input       = document.getElementById('chatbotInput');

    toggle.addEventListener('click', togglePanel);
    closeBtn.addEventListener('click', closePanel);
    sendBtn.addEventListener('click', handleSend);

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 80) + 'px';
    });
  }


  /* ──────────────────────────────────────────────────────────────
     4. PANEL TOGGLE
     ────────────────────────────────────────────────────────────── */

  function togglePanel() {
    isOpen ? closePanel() : openPanel();
  }

  function openPanel() {
    isOpen = true;
    const panel  = document.getElementById('chatbotPanel');
    const toggle = document.getElementById('chatbotToggle');
    const label  = document.getElementById('chatbotLabel');

    panel.classList.add('open');
    toggle.classList.add('active');
    label.classList.add('hidden');

    // Show welcome message on first open
    const messages = document.getElementById('chatbotMessages');
    if (messages.children.length === 0) {
      showWelcome();
    }

    // Focus input
    setTimeout(() => {
      document.getElementById('chatbotInput').focus();
    }, 350);
  }

  function closePanel() {
    isOpen = false;
    const panel  = document.getElementById('chatbotPanel');
    const toggle = document.getElementById('chatbotToggle');
    const label  = document.getElementById('chatbotLabel');

    panel.classList.remove('open');
    toggle.classList.remove('active');
    label.classList.remove('hidden');
  }


  /* ──────────────────────────────────────────────────────────────
     5. WELCOME MESSAGE + QUICK REPLY CHIPS
     ────────────────────────────────────────────────────────────── */

  function showWelcome() {
    const welcomeHTML = `
      <p>Namaste! I'm <strong>USTAD</strong> — your AI-powered analytics assistant for the Aadhaar Portal. I can help you with:</p>
      <ul>
        <li>📊 Live enrollment & update statistics</li>
        <li>🗺️ Regional coverage gap analysis</li>
        <li>⚠️ Anomaly explanations & severity</li>
        <li>📈 Historical trends & forecasts</li>
        <li>💡 Actionable policy recommendations</li>
        <li>🔬 Portal navigation & methodology</li>
      </ul>
      <p style="margin-top:6px;opacity:0.7;font-size:0.78rem;">Ask me anything or try a quick question below:</p>
    `;

    appendMessage('bot', welcomeHTML, true);
    showQuickReplies();
  }

  function showQuickReplies() {
    if (!chipsShown) return;
    const messages = document.getElementById('chatbotMessages');
    const chipsDiv = document.createElement('div');
    chipsDiv.className = 'chatbot-chips';
    chipsDiv.id = 'chatbotChips';

    QUICK_REPLIES.forEach(text => {
      const chip = document.createElement('button');
      chip.className = 'chatbot-chip';
      chip.textContent = text;
      chip.addEventListener('click', () => {
        removeChips();
        sendMessage(text);
      });
      chipsDiv.appendChild(chip);
    });

    messages.appendChild(chipsDiv);
    scrollToBottom();
  }

  function removeChips() {
    chipsShown = false;
    const chips = document.getElementById('chatbotChips');
    if (chips) chips.remove();
  }


  /* ──────────────────────────────────────────────────────────────
     6. MESSAGE RENDERING
     ────────────────────────────────────────────────────────────── */

  function appendMessage(role, content, isHTML = false) {
    const messages = document.getElementById('chatbotMessages');
    const msgDiv   = document.createElement('div');
    msgDiv.className = `chat-msg ${role}`;

    const avatarLabel = role === 'bot' ? 'U' : 'AD';
    const bubbleContent = isHTML ? content : escapeHTML(content);

    msgDiv.innerHTML = `
      <div class="chat-msg-avatar">${avatarLabel}</div>
      <div class="chat-msg-bubble">${bubbleContent}</div>
    `;

    messages.appendChild(msgDiv);
    scrollToBottom();
  }

  function showTyping() {
    const messages = document.getElementById('chatbotMessages');
    const typing   = document.createElement('div');
    typing.className = 'chat-typing';
    typing.id = 'chatbotTyping';
    typing.innerHTML = `
      <div class="chat-msg-avatar">U</div>
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    `;
    messages.appendChild(typing);
    scrollToBottom();
  }

  function hideTyping() {
    const typing = document.getElementById('chatbotTyping');
    if (typing) typing.remove();
  }

  function showError(message, retryFn) {
    const messages = document.getElementById('chatbotMessages');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'chat-error';
    errorDiv.innerHTML = `
      ⚠️ ${escapeHTML(message)}
      <br>
      <button class="retry-btn" id="chatRetry">Try Again</button>
    `;
    messages.appendChild(errorDiv);
    scrollToBottom();

    if (retryFn) {
      errorDiv.querySelector('#chatRetry').addEventListener('click', () => {
        errorDiv.remove();
        retryFn();
      });
    }
  }

  function scrollToBottom() {
    const messages = document.getElementById('chatbotMessages');
    requestAnimationFrame(() => {
      messages.scrollTop = messages.scrollHeight;
    });
  }


  /* ──────────────────────────────────────────────────────────────
     7. SEND MESSAGE LOGIC
     ────────────────────────────────────────────────────────────── */

  function handleSend() {
    const input = document.getElementById('chatbotInput');
    const text  = input.value.trim();
    if (!text || isLoading) return;

    input.value = '';
    input.style.height = 'auto';
    removeChips();
    sendMessage(text);
  }

  async function sendMessage(text) {
    if (isLoading) return;

    // Show user message
    appendMessage('user', text);
    conversationHistory.push({ role: 'user', content: text });

    // Show typing indicator
    isLoading = true;
    updateSendButton();
    showTyping();

    try {
      const response = await fetch(`${API}/chat/ask`, {
        method: 'POST',
        headers: hdrs(),
        body: JSON.stringify({
          message: text,
          history: conversationHistory.slice(-20),
        }),
      });

      hideTyping();

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        const detail = err.detail || `Server error (${response.status})`;
        throw new Error(detail);
      }

      const data = await response.json();
      const reply = data.reply || 'I apologize, I received an empty response. Please try again.';

      // Format and show bot response
      const formattedReply = formatBotReply(reply);
      appendMessage('bot', formattedReply, true);
      conversationHistory.push({ role: 'assistant', content: reply });

    } catch (err) {
      hideTyping();
      console.error('Chat error:', err);

      let errorMsg = err.message;
      if (err.message.includes('ANTHROPIC_API_KEY')) {
        errorMsg = 'USTAD is not configured. Admin needs to set the ANTHROPIC_API_KEY in .env file.';
      } else if (err.message.toLowerCase().includes('rate limit') || err.message.toLowerCase().includes('quota') || err.message.toLowerCase().includes('limit') || err.message.toLowerCase().includes('overloaded') || err.message.includes('429')) {
        errorMsg = 'AI API rate limit reached. Please wait 30 seconds and try again.';
      } else if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        errorMsg = 'Unable to reach the server. Please check your connection.';
      }

      showError(errorMsg, () => sendMessage(text));

      // Remove last user message from history since it failed
      conversationHistory.pop();
    } finally {
      isLoading = false;
      updateSendButton();
    }
  }

  function updateSendButton() {
    const btn = document.getElementById('chatbotSend');
    btn.disabled = isLoading;
  }


  /* ──────────────────────────────────────────────────────────────
     8. RESPONSE FORMATTING
     ────────────────────────────────────────────────────────────── */

  function formatBotReply(text) {
    // Convert markdown-like formatting to HTML

    // Bold: **text** or __text__
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');

    // Italic: *text* or _text_
    text = text.replace(/\*(?!\*)(.*?)\*/g, '<em>$1</em>');

    // Inline code: `code`
    text = text.replace(/`(.*?)`/g, '<code>$1</code>');

    // Bullet points: lines starting with - or •
    text = text.replace(/^[\-•]\s+(.+)$/gm, '<li>$1</li>');

    // Numbered lists: lines starting with 1. 2. etc.
    text = text.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');

    // Wrap consecutive <li> elements in <ul>
    text = text.replace(/((?:<li>.*?<\/li>\s*)+)/gs, '<ul>$1</ul>');

    // Paragraphs: double newlines
    text = text.replace(/\n\n+/g, '</p><p>');

    // Single newlines (that aren't already in list items)
    text = text.replace(/(?<!\>)\n(?!\<)/g, '<br>');

    // Wrap in paragraph
    if (!text.startsWith('<')) {
      text = '<p>' + text + '</p>';
    }

    return text;
  }

  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }


  /* ──────────────────────────────────────────────────────────────
     9. INITIALIZATION
     ────────────────────────────────────────────────────────────── */

  function init() {
    injectHTML();
    bindEvents();
    console.log('[USTAD] AI Analytics Assistant initialized');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Public API (for external integration if needed)
  return {
    open: openPanel,
    close: closePanel,
    toggle: togglePanel,
    send: sendMessage,
  };
})();
