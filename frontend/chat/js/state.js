/**
 * QUANTA Secure Chat - State Store
 * Manages active session, crypto-agility tier, participants, and message states.
 * Adheres strictly to Zero-Key-Leakage: No private keys or raw secrets are stored.
 */

const State = {
  activeTier: 1, // Tier 1: Full PQC Hybrid, Tier 4: Classical Compatibility
  tierSpecs: {
    1: {
      name: "Tier 1: Full PQC Hybrid",
      level: "NIST Level 3 · Post-Quantum",
      kem: "ML-KEM-768 + X25519",
      sig: "ML-DSA-65",
      enc: "AES-256-GCM",
      sessionType: "SHST (Stateless Hybrid Session Token)"
    },
    4: {
      name: "Tier 4: Classical Compatibility",
      level: "Legacy Classical (FIPS 140-3)",
      kem: "X25519 (ECDH)",
      sig: "ECDSA P-256",
      enc: "AES-128-GCM",
      sessionType: "Standard Token"
    }
  },
  
  // Session details from handshake
  sessionId: null,
  shstToken: null,
  shstExpiresAt: null,
  handshakeLatencyMs: null,
  
  // Connection and system status
  connectionStatus: 'connecting', // 'connected' | 'connecting' | 'disconnected'
  apiBaseUrl: 'http://localhost:8000',
  isProcessing: false,
  
  // Participants
  sender: {
    id: "alice_client_01",
    name: "Alice (Sender)",
    role: "Originating Endpoint",
    color: "alice"
  },
  receiver: {
    id: "bob_client_02",
    name: "Bob (Receiver)",
    role: "Verifying Endpoint",
    color: "bob"
  },
  
  // Message history
  messages: [],
  
  // Active timeline state
  currentTimeline: [],
  
  // Event listeners for state changes
  listeners: [],
  
  subscribe(fn) {
    this.listeners.push(fn);
  },
  
  notify(event, payload) {
    this.listeners.forEach(fn => {
      try {
        fn(event, payload);
      } catch (err) {
        console.error("State listener error:", err);
      }
    });
  },
  
  setTier(tier) {
    this.activeTier = parseInt(tier, 10);
    this.notify('tier_changed', { tier: this.activeTier, spec: this.tierSpecs[this.activeTier] });
  },
  
  setSession(sessionData) {
    this.sessionId = sessionData.session_id;
    this.shstToken = sessionData.shst_token;
    this.shstExpiresAt = sessionData.shst_expires_at;
    this.handshakeLatencyMs = sessionData.timing ? (sessionData.timing.total_ms || 1.2) : 1.2;
    this.connectionStatus = 'connected';
    this.notify('session_updated', sessionData);
  },
  
  setConnectionStatus(status) {
    this.connectionStatus = status;
    this.notify('connection_status_changed', { status });
  },
  
  addMessage(msg) {
    this.messages.push(msg);
    this.notify('message_added', msg);
  }
};

window.State = State;
