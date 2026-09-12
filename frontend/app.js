/**
 * PTT Voice Assistant — app.js
 *
 * Connects to the FastAPI backend at /api/v1/chat.
 * Records audio while the button is held, decodes it via WebAudioAPI
 * into a proper WAV file (which Groq Whisper always accepts), then POSTs
 * it and plays back the base64-encoded response.
 *
 * Why WAV? Browser MediaRecorder outputs webm/ogg containers that Groq
 * sometimes rejects with "invalid_media_file". WAV is a raw PCM container
 * that Whisper accepts universally. We encode it ourselves in ~30 lines.
 */

// ─── Config ────────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:8000";           // change to "http://localhost:8000" if on a different port
const CHAT_ENDPOINT = `${API_BASE}/api/v1/chat`;

// Record in whatever the browser prefers — we'll transcode to WAV anyway.
const RECORD_MIME = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
  ? "audio/webm;codecs=opus"
  : "audio/ogg;codecs=opus";

// ─── State ─────────────────────────────────────────────────────────────────
let mediaRecorder = null;
let audioChunks   = [];
let stream        = null;
let isProcessing  = false;
let audioCtx      = null;

// ─── DOM refs ──────────────────────────────────────────────────────────────
const pttBtn          = document.getElementById("pttBtn");
const statusLabel     = document.getElementById("statusLabel");
const waveform        = document.getElementById("waveform");
const pulseRing       = document.getElementById("pulseRing");
const hintText        = document.getElementById("hintText");
const exchangeContainer = document.getElementById("exchangeContainer");
const emptyState      = document.getElementById("emptyState");
const connectionDot   = document.getElementById("connectionDot");

// ─── Server health check ───────────────────────────────────────────────────
async function checkServer() {
  try {
    const res = await fetch(`${API_BASE}/`, { method: "GET" });
    if (res.ok) {
      connectionDot.classList.add("online");
      connectionDot.title = "Server online";
    } else {
      throw new Error("non-ok");
    }
  } catch {
    connectionDot.classList.remove("online");
    connectionDot.classList.add("error");
    connectionDot.title = "Server unreachable";
  }
}

checkServer();

// ─── Mic access ────────────────────────────────────────────────────────────
async function getMicStream() {
  if (stream) return stream;
  stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  return stream;
}

// ─── UI state helpers ──────────────────────────────────────────────────────
function setIdle() {
  pttBtn.classList.remove("recording", "processing");
  pttBtn.setAttribute("aria-pressed", "false");
  pttBtn.disabled = false;
  statusLabel.textContent = "Hold to speak";
  statusLabel.style.color = "";
  waveform.classList.remove("active", "processing");
  hintText.style.opacity = "1";
}

function setRecording() {
  pttBtn.classList.add("recording");
  pttBtn.setAttribute("aria-pressed", "true");
  statusLabel.textContent = "Recording…";
  waveform.classList.add("active");
  waveform.classList.remove("processing");
  hintText.style.opacity = "0";
}

function setProcessing() {
  pttBtn.classList.remove("recording");
  pttBtn.classList.add("processing");
  pttBtn.disabled = true;
  statusLabel.textContent = "Thinking…";
  waveform.classList.remove("active");
  waveform.classList.add("processing");
  waveform.style.opacity = "1";
}

// ─── Transcript helpers ────────────────────────────────────────────────────
function clearEmptyState() {
  if (emptyState && emptyState.parentNode) {
    emptyState.parentNode.removeChild(emptyState);
  }
}

function appendMessage(role, text) {
  clearEmptyState();

  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const roleEl = document.createElement("span");
  roleEl.className = "message-role";
  roleEl.textContent = role === "user" ? "You" : "Assistant";

  const textEl = document.createElement("p");
  textEl.className = "message-text";
  textEl.textContent = text;

  wrapper.appendChild(roleEl);
  wrapper.appendChild(textEl);
  exchangeContainer.appendChild(wrapper);

  // Scroll to latest
  wrapper.scrollIntoView({ behavior: "smooth", block: "end" });
}

// ─── Error toast ────────────────────────────────────────────────────────────
function showError(msg) {
  // Remove any existing toast first
  document.querySelectorAll(".error-toast").forEach(t => t.remove());

  const toast = document.createElement("div");
  toast.className = "error-toast";
  toast.textContent = msg;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 3500);
}

async function blobToWav(blob) {
  const arrayBuffer = await blob.arrayBuffer();
  console.log("ArrayBuffer size:", arrayBuffer.byteLength);
  console.log("AudioContext state:", audioCtx.state);
  try {
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    console.log("Decoded OK:", audioBuffer.duration, "seconds");
    return audioBufferToWav(audioBuffer);
  } catch (err) {
    console.error("decodeAudioData failed:", err.name, err.message);
    throw err;
  }
}

// ─── Core: record → send → play ────────────────────────────────────────────
async function startRecording() {
  if (isProcessing) return;

  try {
    const mic = await getMicStream();
    audioChunks = [];

    // ← CREATE AudioContext here, inside the user gesture
    if (!audioCtx || audioCtx.state === "closed") {
      audioCtx = new AudioContext();
    }

    mediaRecorder = new MediaRecorder(mic, { mimeType: RECORD_MIME });
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };
    mediaRecorder.start(100);
    setRecording();
  } catch (err) {
    console.error("Mic error:", err);
    showError("Microphone access denied. Check browser permissions.");
    setIdle();
  }
}

async function stopRecordingAndSend() {
  if (!mediaRecorder || mediaRecorder.state === "inactive") {
    setIdle();
    return;
  }

  setProcessing();
  isProcessing = true;

  await new Promise((resolve) => {
    mediaRecorder.addEventListener("stop", resolve, { once: true });
    mediaRecorder.requestData();
    mediaRecorder.stop();
  });

  const mimeType = RECORD_MIME.split(";")[0];
  const blob = new Blob(audioChunks, { type: mimeType });

  console.log("Blob size:", blob.size, "type:", blob.type);

  if (blob.size === 0) {
    showError("Recording was empty — hold the button longer before releasing.");
    isProcessing = false;
    setIdle();
    return;
  }

  const formData = new FormData();
  // Try sending as mp4 filename — Groq accepts this container from browsers
  formData.append("audio", blob, "recording.mp4");

  try {
    const res = await fetch(CHAT_ENDPOINT, { method: "POST", body: formData });

    if (!res.ok) {
      const detail = await res.text();
      console.error("Server error:", detail);
      throw new Error(`Server ${res.status}: ${detail}`);
    }

    const data = await res.json();
    if (data.user_text)      appendMessage("user",      data.user_text);
    if (data.assistant_text) appendMessage("assistant", data.assistant_text);
    if (data.audio_base64)   await playBase64Audio(data.audio_base64);

  } catch (err) {
    console.error("Request error:", err);
    showError(err.message || "Something went wrong. Try again.");
  } finally {
    isProcessing = false;
    setIdle();
  }
}

async function playBase64Audio(base64) {
  const binary  = atob(base64);
  const bytes   = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

  const audioBlob = new Blob([bytes], { type: "audio/mpeg" });
  const url       = URL.createObjectURL(audioBlob);
  const audio     = new Audio(url);

  try {
    await new Promise((resolve, reject) => {
      audio.onended = resolve;
      audio.onerror = (e) => {
        console.error("Audio playback error:", e);  // ← ADD
        reject(e);
      };
      audio.play().catch((e) => {
        console.error("audio.play() rejected:", e); // ← ADD
        reject(e);
      });
    });
  } finally {
    URL.revokeObjectURL(url);
  }
}

// ─── Button event wiring ────────────────────────────────────────────────────
// Mouse
pttBtn.addEventListener("mousedown",  (e) => { e.preventDefault(); startRecording(); });
pttBtn.addEventListener("mouseup",    ()  => stopRecordingAndSend());
pttBtn.addEventListener("mouseleave", ()  => {
  if (mediaRecorder && mediaRecorder.state === "recording") stopRecordingAndSend();
});

// Touch (mobile)
pttBtn.addEventListener("touchstart", (e) => { e.preventDefault(); startRecording(); }, { passive: false });
pttBtn.addEventListener("touchend",   (e) => { e.preventDefault(); stopRecordingAndSend(); });

// Keyboard (spacebar = hold to talk)
let spaceHeld = false;
document.addEventListener("keydown", (e) => {
  if (e.code === "Space" && !e.repeat && !spaceHeld) {
    e.preventDefault();
    spaceHeld = true;
    startRecording();
  }
});
document.addEventListener("keyup", (e) => {
  if (e.code === "Space") {
    spaceHeld = false;
    stopRecordingAndSend();
  }
});

// Guard: if user releases mouse outside the window
window.addEventListener("mouseup", () => {
  if (mediaRecorder && mediaRecorder.state === "recording") stopRecordingAndSend();
});