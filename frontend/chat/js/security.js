/**
 * QUANTA Secure Chat - Security Channel & Protocol Timeline Module
 * Visualizes hybrid PQC session state, live protocol execution, and tampering detection.
 */

const Security = {
  timelineSteps: [
    { id: 'created', title: '1. Message Created', desc: 'Plaintext prepared by application endpoint' },
    { id: 'signed', title: '2. Signature Generated', desc: 'Authenticity seal created via ML-DSA-65' },
    { id: 'encrypted', title: '3. AES-256-GCM Encryption', desc: 'Authenticated payload encryption' },
    { id: 'transmitted', title: '4. Ciphertext Transmitted', desc: 'Encrypted frame routed over network' },
    { id: 'decrypted', title: '5. Receiver Decryption', desc: 'AES-GCM authentication tag verified' },
    { id: 'verified', title: '6. Integrity Confirmed', desc: 'ML-DSA-65 signature verified against identity' }
  ],

  init() {
    this.renderTimelineInitial();
    this.bindEvents();
    
    // Subscribe to state updates
    State.subscribe((event, data) => {
      if (event === 'session_updated' || event === 'tier_changed') {
        this.updateSecurityCard();
      }
    });
  },

  bindEvents() {
    // Tier buttons
    document.querySelectorAll('.tier-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const tier = parseInt(btn.dataset.tier, 10);
        if (tier === State.activeTier) return;
        
        await this.handleTierSwitch(tier);
      });
    });

    // Tamper Button
    const btnTamper = document.getElementById('btn-tamper');
    if (btnTamper) {
      btnTamper.addEventListener('click', () => this.showTamperModal());
    }

    // Modal Close
    const btnCloseModal = document.getElementById('btn-close-tamper');
    if (btnCloseModal) {
      btnCloseModal.addEventListener('click', () => this.hideTamperModal());
    }

    // Execute Tampering Attack
    const btnExecuteTamper = document.getElementById('btn-execute-tamper');
    if (btnExecuteTamper) {
      btnExecuteTamper.addEventListener('click', () => this.executeTamperAttack());
    }
  },

  async handleTierSwitch(tier) {
    try {
      // Call backend tier switch endpoint
      await Api.switchTier(tier);
      
      // Re-run handshake under new tier policy
      const sessionData = await Api.establishHandshake(tier);
      State.setTier(tier);
      State.setSession(sessionData);

      // Update UI active classes
      document.querySelectorAll('.tier-btn').forEach(b => {
        b.classList.toggle('active', parseInt(b.dataset.tier, 10) === tier);
      });

      // Update timeline initial state
      this.resetTimeline(`Tier ${tier} Hybrid Channel Re-established`);
    } catch (err) {
      console.error("Failed to switch tier:", err);
    }
  },

  updateSecurityCard() {
    const spec = State.tierSpecs[State.activeTier];
    
    // Update Session ID & SHST Token (truncated safely)
    const sessionIdEl = document.getElementById('sec-session-id');
    const shstStatusEl = document.getElementById('sec-shst-status');
    const tierNameEl = document.getElementById('sec-tier-name');
    const kemAlgoEl = document.getElementById('sec-kem-algo');
    const sigAlgoEl = document.getElementById('sec-sig-algo');
    const encAlgoEl = document.getElementById('sec-enc-algo');

    if (sessionIdEl) sessionIdEl.textContent = State.sessionId ? State.sessionId.slice(0, 16) + '...' : 'qnt_7f82...';
    if (shstStatusEl) shstStatusEl.innerHTML = `<span class="pulse-dot"></span> Active (${State.handshakeLatencyMs || 1.2}ms)`;
    if (tierNameEl) tierNameEl.textContent = spec.level;
    if (kemAlgoEl) kemAlgoEl.textContent = spec.kem;
    if (sigAlgoEl) sigAlgoEl.textContent = spec.sig;
    if (encAlgoEl) encAlgoEl.textContent = spec.enc;
  },

  renderTimelineInitial() {
    const container = document.getElementById('protocol-timeline');
    if (!container) return;

    container.innerHTML = this.timelineSteps.map((step, idx) => `
      <div class="timeline-step ${idx === 0 ? 'completed' : ''}" id="step-${step.id}">
        <div class="step-marker"></div>
        <div class="step-title">
          <span>${step.title}</span>
          <span class="step-badge" id="badge-${step.id}">${idx === 0 ? '✓ Ready' : 'Pending'}</span>
        </div>
        <div class="step-desc" id="desc-${step.id}">${step.desc}</div>
      </div>
    `).join('');
  },

  resetTimeline(statusText = 'Channel Ready') {
    this.timelineSteps.forEach((step, idx) => {
      const stepEl = document.getElementById(`step-${step.id}`);
      const badgeEl = document.getElementById(`badge-${step.id}`);
      const descEl = document.getElementById(`desc-${step.id}`);
      
      if (stepEl) {
        stepEl.className = `timeline-step ${idx === 0 ? 'completed' : ''}`;
      }
      if (badgeEl) {
        badgeEl.textContent = idx === 0 ? '✓ Ready' : 'Pending';
      }
      if (descEl) {
        descEl.textContent = idx === 0 ? statusText : step.desc;
      }
    });
  },

  async animateStep(stepId, status = 'active', badgeText = 'Running...', customDesc = null) {
    const stepEl = document.getElementById(`step-${stepId}`);
    const badgeEl = document.getElementById(`badge-${stepId}`);
    const descEl = document.getElementById(`desc-${stepId}`);

    if (stepEl) {
      stepEl.className = `timeline-step ${status}`;
    }
    if (badgeEl) {
      badgeEl.textContent = badgeText;
    }
    if (descEl && customDesc) {
      descEl.textContent = customDesc;
    }

    // Small micro-delay for smooth visualization
    await new Promise(r => setTimeout(r, 140));
  },

  // Tamper Simulation Modal
  showTamperModal() {
    const modal = document.getElementById('tamper-modal-overlay');
    if (modal) modal.classList.add('active');
  },

  hideTamperModal() {
    const modal = document.getElementById('tamper-modal-overlay');
    if (modal) modal.classList.remove('active');
  },

  async executeTamperAttack() {
    this.hideTamperModal();

    // 1. Reset timeline
    this.resetTimeline('Simulating Network Tampering Attack...');

    // 2. Animate up to encryption
    await this.animateStep('created', 'completed', '✓ Created', 'Original message: "CONFIDENTIAL MEDICAL CLEARANCE"');
    await this.animateStep('signed', 'completed', '✓ ML-DSA-65', 'Signed with Alice endpoint key (3,293 bytes)');
    await this.animateStep('encrypted', 'completed', '✓ AES-GCM', 'Original ciphertext: 8fa3c91b7e44...');
    
    // 3. Simulate MITM modification in flight
    await this.animateStep('transmitted', 'active', '⚠ MODIFIED IN-FLIGHT', 'Attacker modified byte 0x1B -> 0x1C (8fa3c91c7e44...)');
    
    await new Promise(r => setTimeout(r, 450));

    // 4. Decrypt & Verify failure
    await this.animateStep('decrypted', 'failed', '❌ GCM TAG FAILED', 'Authenticated tag mismatch during GCM check');
    await this.animateStep('verified', 'failed', '❌ REJECTED', 'Integrity check: TAMPERED. Payload dropped.');

    // 5. Add rejected message notification to chat feed
    if (window.Chat) {
      window.Chat.appendTamperedAlert({
        original: "CONFIDENTIAL MEDICAL CLEARANCE",
        tampered: "UNAUTHORIZED_PAYLOAD_CORRUPTED",
        reason: "ML-DSA-65 / AES-256-GCM Authentication Verification Failed"
      });
    }
  }
};

window.Security = Security;
