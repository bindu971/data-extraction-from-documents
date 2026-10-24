"use strict";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// The page is served by the FastAPI app itself, so the API is same-origin.
const API_BASE = "";

// Mirrors the extension check in service/api.py (POST /extract).
const SUPPORTED_EXTENSIONS = [".docx", ".png", ".jpg", ".jpeg"];
const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"];

const HEALTH_TIMEOUT_MS = 5000;
const HEALTH_INTERVAL_MS = 30000;
// The backend allows Ollama up to 600 s per attempt with two attempts.
const EXTRACT_TIMEOUT_MS = 20 * 60 * 1000;

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

class ApiError extends Error {
  constructor(kind, message, status) {
    super(message);
    this.kind = kind; // "network" | "timeout" | "cancelled" | "http" | "invalid"
    this.status = status;
  }
}

async function request(path, { method = "GET", body, timeoutMs, controller } = {}) {
  controller = controller || new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  let response;
  try {
    response = await fetch(API_BASE + path, { method, body, signal: controller.signal });
  } catch (err) {
    if (timedOut) throw new ApiError("timeout", "The request timed out.");
    if (err.name === "AbortError") throw new ApiError("cancelled", "The request was cancelled.");
    throw new ApiError("network", err.message);
  } finally {
    clearTimeout(timer);
  }

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // Non-JSON bodies (e.g. FastAPI's plain-text 500) are handled below.
  }

  if (!response.ok) {
    throw new ApiError("http", describeHttpError(response.status, data), response.status);
  }
  if (data === null) {
    throw new ApiError("invalid", "The server returned a response that is not valid JSON.");
  }
  return data;
}

function describeHttpError(status, data) {
  const detail = data && data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length && detail[0].msg) return detail[0].msg;
  return `HTTP ${status}`;
}

const api = {
  health: () => request("/health", { timeoutMs: HEALTH_TIMEOUT_MS }),
  fields: () => request("/fields", { timeoutMs: HEALTH_TIMEOUT_MS }),
  extract(file, controller) {
    const form = new FormData();
    form.append("file", file, file.name);
    return request("/extract", { method: "POST", body: form, timeoutMs: EXTRACT_TIMEOUT_MS, controller });
  },
};

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------

const $ = (id) => document.getElementById(id);

const el = {
  health: $("health"),
  healthText: $("health-text"),
  dropzone: $("dropzone"),
  fileInput: $("file-input"),
  browseBtn: $("browse-btn"),
  formats: $("formats"),
  fileCard: $("file-card"),
  fileThumb: $("file-thumb"),
  fileName: $("file-name"),
  fileDetails: $("file-details"),
  replaceBtn: $("replace-btn"),
  removeBtn: $("remove-btn"),
  message: $("message"),
  messageTitle: $("message-title"),
  messageText: $("message-text"),
  progress: $("progress"),
  elapsed: $("elapsed"),
  extractBtn: $("extract-btn"),
  extractLabel: $("extract-label"),
  cancelBtn: $("cancel-btn"),
  resultsSubtitle: $("results-subtitle"),
  resultActions: $("result-actions"),
  copyAllBtn: $("copy-all-btn"),
  downloadBtn: $("download-btn"),
  newBtn: $("new-btn"),
  summary: $("summary"),
  fields: $("fields"),
  fieldsEmpty: $("fields-empty"),
  toast: $("toast"),
};

const ICONS = {
  value: '<svg viewBox="0 0 24 24"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/></svg>',
  date: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg>',
  notice: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  party: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
  field: '<svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
  copy: '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>',
  docx: '<svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/></svg>',
  error: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/></svg>',
  warning: '<svg viewBox="0 0 24 24"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
  info: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg>',
  check: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/></svg>',
};

function iconForField(name) {
  const lower = name.toLowerCase();
  if (lower.includes("date")) return ICONS.date;
  if (lower.includes("value")) return ICONS.value;
  if (lower.includes("notice")) return ICONS.notice;
  if (lower.includes("party")) return ICONS.party;
  return ICONS.field;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function extensionOf(name) {
  const dot = name.lastIndexOf(".");
  return dot === -1 ? "" : name.slice(dot).toLowerCase();
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(ms) {
  const total = Math.floor(ms / 1000);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

// A value counts as missing when the backend returned an empty string or null.
function isMissing(value) {
  return value === null || value === undefined || String(value).trim() === "";
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const state = {
  file: null,
  thumbUrl: null,
  fieldNames: [],      // from GET /fields
  fieldsFailed: false, // GET /fields could not be loaded
  result: null,        // last successful POST /extract response
  controller: null,    // AbortController of the running extraction
  timer: null,
  startedAt: 0,
};

// ---------------------------------------------------------------------------
// Backend status
// ---------------------------------------------------------------------------

function setHealth(stateName, text) {
  el.health.dataset.state = stateName;
  el.healthText.textContent = text;
}

async function checkHealth() {
  try {
    const data = await api.health();
    if (data && data.status === "ok") {
      setHealth("online", "Connected");
      if (!state.fieldNames.length) loadFields();
      return true;
    }
  } catch (err) {
    console.warn("Health check failed:", err);
  }
  setHealth("offline", "Backend unavailable");
  if (!state.fieldNames.length && !state.fieldsFailed) {
    state.fieldsFailed = true;
    if (!state.result) renderPlaceholderFields();
  }
  return false;
}

async function loadFields() {
  try {
    const data = await api.fields();
    if (data && Array.isArray(data.fields) && data.fields.every((f) => typeof f === "string")) {
      state.fieldNames = data.fields;
      state.fieldsFailed = false;
      if (!state.result) renderPlaceholderFields();
      return;
    }
    console.warn("Unexpected /fields response:", data);
  } catch (err) {
    console.warn("Could not load fields:", err);
  }
  state.fieldsFailed = true;
  if (!state.result) renderPlaceholderFields();
}

// ---------------------------------------------------------------------------
// Messages
// ---------------------------------------------------------------------------

function showMessage(tone, title, text = "") {
  el.message.dataset.tone = tone;
  el.message.querySelector(".alert-icon").innerHTML = ICONS[tone === "danger" ? "error" : tone];
  el.messageTitle.textContent = title;
  el.messageText.textContent = text;
  el.messageText.hidden = !text;
  el.message.hidden = false;
}

function clearMessage() {
  el.message.hidden = true;
}

let toastTimer = null;
function toast(text) {
  el.toast.textContent = text;
  el.toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.toast.hidden = true; }, 2200);
}

// ---------------------------------------------------------------------------
// File selection
// ---------------------------------------------------------------------------

function selectFile(file) {
  clearMessage();
  el.dropzone.classList.remove("is-invalid");

  const ext = extensionOf(file.name);
  if (!SUPPORTED_EXTENSIONS.includes(ext)) {
    el.dropzone.classList.add("is-invalid");
    showMessage(
      "danger",
      "Unsupported file type",
      `"${file.name}" cannot be processed. Supported formats: ${SUPPORTED_EXTENSIONS.join(", ")}.`
    );
    return;
  }

  setFile(file);
}

function setFile(file) {
  if (state.thumbUrl) {
    URL.revokeObjectURL(state.thumbUrl);
    state.thumbUrl = null;
  }
  state.file = file;
  el.fileInput.value = "";

  if (!file) {
    el.fileCard.hidden = true;
    el.dropzone.hidden = false;
    updateControls();
    return;
  }

  const ext = extensionOf(file.name);
  const isImage = IMAGE_EXTENSIONS.includes(ext);
  if (isImage) {
    state.thumbUrl = URL.createObjectURL(file);
    el.fileThumb.innerHTML = `<img src="${state.thumbUrl}" alt="">`;
  } else {
    el.fileThumb.innerHTML = ICONS.docx;
  }

  el.fileName.textContent = file.name;
  el.fileName.title = file.name;
  const kind = isImage ? "Scanned image · OCR" : "Word document";
  el.fileDetails.textContent = `${kind} · ${ext.slice(1).toUpperCase()} · ${formatSize(file.size)}`;

  el.fileCard.hidden = false;
  el.dropzone.hidden = true;
  updateControls();
  el.extractBtn.focus();
}

function openFilePicker() {
  if (!state.controller) el.fileInput.click();
}

// ---------------------------------------------------------------------------
// Extraction
// ---------------------------------------------------------------------------

function updateControls() {
  const busy = Boolean(state.controller);
  el.extractBtn.disabled = busy || !state.file;
  el.extractBtn.classList.toggle("is-loading", busy);
  el.extractLabel.textContent = busy ? "Extracting…" : "Extract Metadata";
  el.cancelBtn.hidden = !busy;
  el.progress.hidden = !busy;
  el.replaceBtn.disabled = busy;
  el.removeBtn.disabled = busy;
  el.browseBtn.disabled = busy;
  el.dropzone.classList.toggle("is-disabled", busy);
  el.newBtn.disabled = busy;
}

async function runExtraction() {
  if (state.controller) return; // already running
  if (!state.file) {
    showMessage("danger", "No document selected", "Please select a document before extracting metadata.");
    return;
  }

  clearMessage();
  const file = state.file;
  // Clear the previous document's results so they are not mistaken for this one.
  state.result = null;
  renderPlaceholderFields();
  el.resultsSubtitle.textContent = `Extracting from ${file.name}…`;

  const controller = new AbortController();
  state.controller = controller;
  state.startedAt = Date.now();
  el.elapsed.textContent = "0:00";
  state.timer = setInterval(() => {
    el.elapsed.textContent = formatDuration(Date.now() - state.startedAt);
  }, 1000);
  updateControls();

  try {
    const data = await api.extract(file, controller);
    const fields = data && data.extracted_fields;
    if (!fields || typeof fields !== "object" || Array.isArray(fields)) {
      throw new ApiError("invalid", "The response did not contain extracted fields.");
    }
    state.result = { filename: data.filename || file.name, extracted_fields: fields };
    renderResult(state.result, Date.now() - state.startedAt);
  } catch (err) {
    handleExtractionError(err);
  } finally {
    clearInterval(state.timer);
    state.controller = null;
    updateControls();
  }
}

function handleExtractionError(err) {
  console.error("Extraction failed:", err);

  if (!(err instanceof ApiError)) {
    showMessage("danger", "Extraction failed", "An unexpected error occurred. Please try again.");
    return;
  }

  switch (err.kind) {
    case "cancelled":
      showMessage("info", "Extraction cancelled", "The server may still finish processing this document in the background.");
      break;
    case "timeout":
      showMessage("danger", "Request timed out", "The backend took too long to respond. Please try again.");
      break;
    case "network":
      showMessage("danger", "Backend unavailable", "The backend is currently unavailable. Please check that the API server is running.");
      checkHealth();
      break;
    case "invalid":
      showMessage("danger", "Unexpected response", "The server returned a response in an unexpected format. Please try again.");
      break;
    case "http":
      if (err.status === 400 || err.status === 422) {
        showMessage("danger", "Document rejected", err.message);
      } else if (err.status >= 500) {
        showMessage(
          "danger",
          "Extraction failed",
          "The server could not process this document. Check that Ollama is running with the model available, then try again."
        );
      } else {
        showMessage("danger", "Extraction failed", `The request failed (${err.message}). Please try again.`);
      }
      break;
  }
}

function cancelExtraction() {
  if (state.controller) state.controller.abort();
}

function resetAll() {
  if (state.controller) return;
  state.result = null;
  setFile(null);
  clearMessage();
  el.dropzone.classList.remove("is-invalid");
  renderPlaceholderFields();
  el.browseBtn.focus();
}

// ---------------------------------------------------------------------------
// Results rendering
// ---------------------------------------------------------------------------

function renderPlaceholderFields() {
  el.summary.hidden = true;
  el.resultActions.hidden = true;
  el.resultsSubtitle.textContent = "Results appear here after extraction";
  el.fieldsEmpty.hidden = state.fieldNames.length > 0 || !state.fieldsFailed;
  el.fields.innerHTML = state.fieldNames.map((name) => `
    <div class="field">
      <div class="field-icon" aria-hidden="true">${iconForField(name)}</div>
      <div class="field-body">
        <dt class="field-label">${escapeHtml(name)}</dt>
        <dd class="field-value is-pending">—</dd>
      </div>
    </div>`).join("");
}

function orderedFieldNames(fields) {
  // Use the order from GET /fields, then append anything else the API returned.
  const names = state.fieldNames.filter((name) => name in fields);
  for (const name of Object.keys(fields)) {
    if (!names.includes(name)) names.push(name);
  }
  return names;
}

function renderResult(result, durationMs) {
  const fields = result.extracted_fields;
  const names = orderedFieldNames(fields);
  const missing = names.filter((name) => isMissing(fields[name])).length;
  const found = names.length - missing;

  el.fieldsEmpty.hidden = true;
  el.fields.innerHTML = names.map((name, index) => {
    const value = fields[name];
    const absent = isMissing(value);
    return `
      <div class="field ${absent ? "" : "is-found"}">
        <div class="field-icon" aria-hidden="true">${iconForField(name)}</div>
        <div class="field-body">
          <dt class="field-label">${escapeHtml(name)}</dt>
          <dd class="field-value ${absent ? "is-missing" : ""}">${absent ? "Not found" : escapeHtml(value)}</dd>
        </div>
        ${absent ? "" : `<button type="button" class="icon-btn" data-copy-index="${index}"
            aria-label="Copy ${escapeHtml(name)}" title="Copy">${ICONS.copy}</button>`}
      </div>`;
  }).join("");
  el.fields.dataset.names = JSON.stringify(names);

  el.resultsSubtitle.textContent = `${result.filename} · ${formatDuration(durationMs)} elapsed`;
  el.resultActions.hidden = false;

  if (names.length === 0 || found === 0) {
    el.summary.dataset.tone = "warning";
    el.summary.innerHTML = `${ICONS.warning}<span>Extraction completed, but no metadata fields were found in this document.</span>`;
  } else if (missing > 0) {
    el.summary.dataset.tone = "warning";
    el.summary.innerHTML = `${ICONS.warning}<span>Extraction completed, but ${missing} of ${names.length} fields were not found.</span>`;
  } else {
    el.summary.dataset.tone = "success";
    el.summary.innerHTML = `${ICONS.check}<span>Extraction completed: all ${names.length} fields found.</span>`;
  }
  el.summary.hidden = false;
}

// ---------------------------------------------------------------------------
// Copy and download
// ---------------------------------------------------------------------------

async function copyText(text, label) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      area.remove();
      if (!ok) throw new Error("execCommand copy failed");
    }
    toast(`${label} copied to clipboard`);
  } catch (err) {
    console.warn("Copy failed:", err);
    toast("Could not copy to clipboard");
  }
}

function copyAll() {
  if (!state.result) return;
  const fields = state.result.extracted_fields;
  const lines = orderedFieldNames(fields).map(
    (name) => `${name}: ${isMissing(fields[name]) ? "Not found" : fields[name]}`
  );
  copyText([`Document: ${state.result.filename}`, ...lines].join("\n"), "All fields");
}

function downloadJson() {
  if (!state.result) return;
  const blob = new Blob([JSON.stringify(state.result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const base = state.result.filename.replace(/\.[^.]+$/, "") || "document";
  link.href = url;
  link.download = `${base}-metadata.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast("JSON downloaded");
}

// ---------------------------------------------------------------------------
// Event wiring
// ---------------------------------------------------------------------------

function wireEvents() {
  el.browseBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    openFilePicker();
  });
  el.dropzone.addEventListener("click", openFilePicker);
  el.replaceBtn.addEventListener("click", openFilePicker);
  el.removeBtn.addEventListener("click", () => {
    setFile(null);
    clearMessage();
    el.browseBtn.focus();
  });

  el.fileInput.addEventListener("change", () => {
    if (el.fileInput.files.length) selectFile(el.fileInput.files[0]);
  });

  // Drag and drop. The counter avoids flicker when dragging over child elements.
  let dragDepth = 0;
  el.dropzone.addEventListener("dragenter", (event) => {
    event.preventDefault();
    dragDepth += 1;
    el.dropzone.classList.add("is-dragover");
  });
  el.dropzone.addEventListener("dragover", (event) => event.preventDefault());
  el.dropzone.addEventListener("dragleave", () => {
    dragDepth = Math.max(0, dragDepth - 1);
    if (!dragDepth) el.dropzone.classList.remove("is-dragover");
  });
  el.dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dragDepth = 0;
    el.dropzone.classList.remove("is-dragover");
    if (state.controller) return;
    const files = event.dataTransfer.files;
    if (!files.length) return;
    selectFile(files[0]);
    if (files.length > 1 && state.file === files[0]) {
      showMessage("info", "One document at a time", `Only "${files[0].name}" was selected.`);
    }
  });

  // Stop the browser from opening a file dropped outside the drop zone.
  window.addEventListener("dragover", (event) => event.preventDefault());
  window.addEventListener("drop", (event) => event.preventDefault());

  el.extractBtn.addEventListener("click", runExtraction);
  el.cancelBtn.addEventListener("click", cancelExtraction);
  el.newBtn.addEventListener("click", resetAll);
  el.copyAllBtn.addEventListener("click", copyAll);
  el.downloadBtn.addEventListener("click", downloadJson);

  el.fields.addEventListener("click", (event) => {
    const button = event.target.closest("[data-copy-index]");
    if (!button || !state.result) return;
    const names = JSON.parse(el.fields.dataset.names || "[]");
    const name = names[Number(button.dataset.copyIndex)];
    copyText(String(state.result.extracted_fields[name]), name);
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") checkHealth();
  });
}

function init() {
  el.formats.innerHTML = SUPPORTED_EXTENSIONS.map((ext) => `<code>${ext}</code>`).join(" ");
  el.fileInput.accept = SUPPORTED_EXTENSIONS.join(",");
  wireEvents();
  updateControls();
  renderPlaceholderFields();
  checkHealth();
  setInterval(() => {
    if (document.visibilityState === "visible") checkHealth();
  }, HEALTH_INTERVAL_MS);
}

init();
