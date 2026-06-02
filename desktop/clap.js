// ── DOUBLE CLAP DETECTION ─────────────────────────────────────────
// Runs in background via Web Audio API
// Two loud claps within 1.5 seconds wakes JARVIS

let clapAudioCtx = null;
let clapAnalyser = null;
let clapData = null;
let lastClapTime = 0;
let clapCount = 0;
let jarvisAwake = false;

const CLAP_THRESHOLD = 180;   // Volume threshold for clap
const CLAP_WINDOW = 1500;     // Max ms between two claps
const CLAP_COOLDOWN = 300;    // Min ms between clap detections

async function initClapDetection() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    clapAudioCtx = new AudioContext();
    const source = clapAudioCtx.createMediaStreamSource(stream);
    clapAnalyser = clapAudioCtx.createAnalyser();
    clapAnalyser.fftSize = 256;
    source.connect(clapAnalyser);
    clapData = new Uint8Array(clapAnalyser.frequencyBinCount);

    console.log('[Clap] Double clap detection active');
    detectClapLoop();
  } catch(e) {
    console.warn('[Clap] Mic access failed:', e);
  }
}

function detectClapLoop() {
  if (!clapAnalyser) return;

  clapAnalyser.getByteFrequencyData(clapData);

  let max = 0;
  for (let i = 0; i < clapData.length; i++) {
    if (clapData[i] > max) max = clapData[i];
  }

  if (max > CLAP_THRESHOLD) {
    const now = Date.now();
    if (now - lastClapTime > CLAP_COOLDOWN) {
      lastClapTime = now;
      clapCount++;
      console.log(`[Clap] Clap detected! Count: ${clapCount}, Volume: ${max}`);

      if (clapCount === 1) {
        // Start window for second clap
        setTimeout(() => {
          if (clapCount === 1) {
            // Only one clap — reset
            clapCount = 0;
          }
        }, CLAP_WINDOW);
      } else if (clapCount >= 2) {
        // Double clap detected!
        clapCount = 0;
        console.log('[Clap] DOUBLE CLAP DETECTED — Waking JARVIS!');
        wakeJarvis();
      }
    }
  }

  requestAnimationFrame(detectClapLoop);
}

function wakeJarvis() {
  if (!jarvisAwake) {
    jarvisAwake = true;
    // Send wake signal to Electron main process
    if (window.ipcRenderer) {
      window.ipcRenderer.send('wake-jarvis');
    }
    // Also show UI directly
    document.body.style.display = 'flex';
    // Connect to agent if not connected
    if (typeof connect === 'function') connect();
    // Flash orb
    if (typeof setOrb === 'function') setOrb('listening');
    setTimeout(() => { if (typeof setOrb === 'function') setOrb('idle'); }, 2000);
  }
}

// Start clap detection when page loads
window.addEventListener('load', () => {
  setTimeout(initClapDetection, 1000);
});
