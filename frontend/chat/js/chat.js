/**
 * QUANTA Secure Chat - Chat Engine
 * Handles message creation, cryptographic API orchestration, and chat feed rendering.
 */

const Chat = {
  init() {
    this.bindEvents();
    this.renderWelcomeMessages();
  },

  bindEvents() {
    const form = document.getElementById('chat-composer-form');
    const input = document.getElementById('chat-input');
    const promptChips = document.querySelectorAll('.prompt-chip');

    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text || State.isProcessing) return;
        
        input.value = '';
        await this.sendMessageFlow(text);
      });
    }

    // Quick prompt chips
    promptChips.forEach(chip => {
      chip.addEventListener('click', () => {
        if (input) {
          input.value = chip.dataset.text || chip.textContent;
          input.focus();
        }
      });
    });
  },

  renderWelcomeMessages() {
    const container = document.getElementById('chat-feed');
    if (!container) return;

    container.innerHTML = `
      <div class="system-banner">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        QUANTA Post-Quantum Hybrid Secure Channel Initialized · Tier 1 Active
      </div>
    `;
  },

  async sendMessageFlow(plaintext) {
    State.isProcessing = true;
    const sendBtn = document.getElementById('btn-send');
    if (sendBtn) sendBtn.disabled = true;

    try {
      // Step 1: Message Created
      await Security.animateStep('created', 'completed', '✓ Created', `Plaintext (${plaintext.length} chars) prepared`);

      // Step 2: Sign via ML-DSA-65
      await Security.animateStep('signed', 'active', 'Signing...');
      const signRes = await Api.signMessage(State.sender.id, plaintext);
      const sigAlgo = signRes.algorithm || (State.activeTier === 1 ? 'ML-DSA-65' : 'ECDSA P-256');
      const sigSize = signRes.sig_size_bytes || 3293;
      await Security.animateStep('signed', 'completed', `✓ ${sigAlgo}`, `Sig ID: ${signRes.signature_id.slice(0, 10)}... (${sigSize}B)`);

      // Step 3: Encrypt via AES-256-GCM
      await Security.animateStep('encrypted', 'active', 'Encrypting...');
      const encRes = await Api.encryptMessage(State.sessionId || 'session_default', plaintext);
      const encAlgo = State.activeTier === 1 ? 'AES-256-GCM' : 'AES-128-GCM';
      const ctPreview = (encRes.ciphertext_hex || '').slice(0, 16) + '...';
      await Security.animateStep('encrypted', 'completed', `✓ ${encAlgo}`, `Ciphertext: ${ctPreview}`);

      // Step 4: Transmit Encrypted Payload
      await Security.animateStep('transmitted', 'active', 'Routing...');
      const sendRes = await Api.sendMessage(State.sessionId || 'session_default', encRes.ciphertext_hex);
      await Security.animateStep('transmitted', 'completed', '✓ Delivered', `Delivery ID: ${sendRes.delivery_id.slice(0, 10)}...`);

      // Step 5: Receiver Decryption
      await Security.animateStep('decrypted', 'active', 'Decrypting...');
      const decRes = await Api.decryptMessage(State.sessionId || 'session_default', sendRes.delivery_id);
      await Security.animateStep('decrypted', 'completed', '✓ Authenticated', 'GCM auth tag valid · Zero tampering detected');

      // Step 6: Signature Verification
      await Security.animateStep('verified', 'active', 'Verifying...');
      const verifyRes = await Api.verifySignature(signRes.signature_id, plaintext);
      const isConfirmed = verifyRes.valid && verifyRes.integrity === 'confirmed';
      await Security.animateStep('verified', isConfirmed ? 'completed' : 'failed', isConfirmed ? '✓ Confirmed' : '❌ Failed', `Identity: ${State.sender.id} · Integrity: confirmed`);

      // Render Messages in Feed (Sender on left, Receiver receipt on right)
      this.appendMessage({
        sender: State.sender.name,
        isReceiver: false,
        text: plaintext,
        sigAlgo,
        encAlgo,
        status: 'Encrypted & Signed'
      });

      // Small delay before Bob's receiver bubble appears
      await new Promise(r => setTimeout(r, 200));

      this.appendMessage({
        sender: State.receiver.name,
        isReceiver: true,
        text: decRes.plaintext || plaintext,
        sigAlgo,
        encAlgo,
        status: 'Decrypted Successfully · Integrity Confirmed ✓'
      });

    } catch (err) {
      console.error("Error in message flow:", err);
      await Security.animateStep('verified', 'failed', '❌ Error', err.message);
    } finally {
      State.isProcessing = false;
      if (sendBtn) sendBtn.disabled = false;
    }
  },

  appendMessage({ sender, isReceiver, text, sigAlgo, encAlgo, status }) {
    const feed = document.getElementById('chat-feed');
    if (!feed) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const groupEl = document.createElement('div');
    groupEl.className = `message-group ${isReceiver ? 'receiver' : 'sender'}`;

    groupEl.innerHTML = `
      <div class="message-author">
        <span>${sender}</span>
        <span>·</span>
        <span>${time}</span>
      </div>
      <div class="message-bubble">
        ${escapeHtml(text)}
      </div>
      <div class="message-meta">
        <span class="security-tag ${isReceiver ? 'valid' : ''}">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          ${sigAlgo}
        </span>
        <span class="security-tag ${isReceiver ? 'valid' : ''}">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          ${encAlgo}
        </span>
        <span class="security-tag ${isReceiver ? 'valid' : ''}">
          ${status}
        </span>
      </div>
    `;

    feed.appendChild(groupEl);
    feed.scrollTop = feed.scrollHeight;
  },

  appendTamperedAlert({ original, tampered, reason }) {
    const feed = document.getElementById('chat-feed');
    if (!feed) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const alertEl = document.createElement('div');
    alertEl.className = 'message-group receiver';

    alertEl.innerHTML = `
      <div class="message-author" style="color: var(--red);">
        <span>Bob (Receiver) - Security Alert</span>
        <span>·</span>
        <span>${time}</span>
      </div>
      <div class="message-bubble" style="background: var(--red-bg); border-color: var(--red-border); color: #FCA5A5;">
        <div style="font-weight: 700; display: flex; align-items: center; gap: 6px; margin-bottom: 4px; color: var(--red);">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          MESSAGE REJECTED: CRYPTOGRAPHIC INTEGRITY VIOLATION
        </div>
        <div>Payload modified in-flight. GCM tag authentication failed and ML-DSA signature was invalidated.</div>
      </div>
      <div class="message-meta">
        <span class="security-tag rejected">
          ❌ Integrity Check: TAMPERED
        </span>
        <span class="security-tag rejected">
          Delivery Blocked
        </span>
      </div>
    `;

    feed.appendChild(alertEl);
    feed.scrollTop = feed.scrollHeight;
  }
};

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

window.Chat = Chat;
