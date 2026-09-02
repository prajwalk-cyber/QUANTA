/**
 * QUANTA Secure Chat - Main Application Bootstrap
 */

document.addEventListener('DOMContentLoaded', async () => {
  console.log("Initializing QUANTA Secure Chat Proof-of-Concept Client...");

  // Initialize Modules
  Security.init();
  Chat.init();

  // Perform Initial Channel Handshake with QUANTA Backend
  try {
    const statusBadge = document.getElementById('api-status-badge');
    if (statusBadge) {
      statusBadge.innerHTML = `<span class="pulse-dot"></span> CONNECTING...`;
      statusBadge.className = 'badge badge-amber';
    }

    const sessionData = await Api.establishHandshake(State.activeTier);
    State.setSession(sessionData);

    if (statusBadge) {
      statusBadge.innerHTML = `<span class="pulse-dot"></span> QUANTA API CONNECTED`;
      statusBadge.className = 'badge badge-green';
    }

    console.log("QUANTA Secure Channel established successfully:", sessionData);
  } catch (err) {
    console.error("Initial handshake encountered error:", err);
    const statusBadge = document.getElementById('api-status-badge');
    if (statusBadge) {
      statusBadge.innerHTML = `<span class="pulse-dot"></span> OFFLINE (SIMULATED)`;
      statusBadge.className = 'badge badge-amber';
    }
  }
});
