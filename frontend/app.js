const API_BASE = window.SME_ASSIST_API_BASE || "";
const byId = (id) => document.getElementById(id);
const fileInput = byId("file-input");
const dropZone = byId("drop-zone");
const analyzeButton = byId("analyze-button");
const selectedFile = byId("selected-file");
const analysisStatus = byId("analysis-status");
const chatMessages = byId("chat-messages");
let currentFile = null;
let currentContext = "";
let latestAnalysis = null;
let recordCount = Number(localStorage.getItem("smeAssistRecordCount") || 0);

function setIcons() {
    if (window.lucide) window.lucide.createIcons();
}

function setStatus(message, isError = false) {
    analysisStatus.textContent = message;
    analysisStatus.classList.toggle("error", isError);
    analysisStatus.classList.remove("hidden");
}

function showToast(message) {
    const toast = byId("toast");
    toast.textContent = message;
    toast.classList.remove("hidden");
    window.setTimeout(() => toast.classList.add("hidden"), 3200);
}

function chooseFile(file) {
    if (!file) return;
    const allowed = /\.(pdf|txt|xls|xlsx)$/i.test(file.name);
    if (!allowed) {
        showToast("Choose a PDF, TXT, XLS, or XLSX file.");
        return;
    }
    if (file.size > 20 * 1024 * 1024) {
        showToast("Files must be smaller than 20 MB.");
        return;
    }
    currentFile = file;
    byId("file-name").textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`;
    selectedFile.classList.remove("hidden");
    dropZone.classList.add("hidden");
    analyzeButton.disabled = false;
    setIcons();
}

fileInput.addEventListener("change", () => chooseFile(fileInput.files[0]));
for (const eventName of ["dragenter", "dragover"]) {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("drag-over");
    });
}
for (const eventName of ["dragleave", "drop"]) {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("drag-over");
    });
}
dropZone.addEventListener("drop", (event) => chooseFile(event.dataTransfer.files[0]));
byId("remove-file").addEventListener("click", () => {
    currentFile = null;
    fileInput.value = "";
    selectedFile.classList.add("hidden");
    dropZone.classList.remove("hidden");
    analyzeButton.disabled = true;
});

function formatMarkdown(text) {
    const raw = window.marked ? window.marked.parse(text || "") : `<p>${escapeHtml(text || "No content returned.")}</p>`;
    return window.DOMPurify ? window.DOMPurify.sanitize(raw) : raw;
}

function escapeHtml(text) {
    return text.replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
}

const reportContent = {summary: "", balance: "", tax: ""};
function activateReport(name) {
    document.querySelectorAll(".report-tab").forEach((tab) => {
        const active = tab.dataset.report === name;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
    });
    byId("report-body").innerHTML = formatMarkdown(reportContent[name]);
}
document.querySelectorAll(".report-tab").forEach((tab) => tab.addEventListener("click", () => activateReport(tab.dataset.report)));

analyzeButton.addEventListener("click", async () => {
    if (!currentFile) return;
    analyzeButton.disabled = true;
    analyzeButton.innerHTML = '<i data-lucide="loader-circle"></i> Analysing…';
    setStatus("Reviewing your document. This can take a little while.");
    setIcons();
    const form = new FormData();
    form.append("file", currentFile);
    try {
        const response = await fetch(`${API_BASE}/analyze`, {method: "POST", body: form});
        if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(payload.detail || `Analysis failed (${response.status}).`);
        }
        latestAnalysis = await response.json();
        currentContext = [latestAnalysis.summary, latestAnalysis.balance_sheet, latestAnalysis.tax_return].join("\n\n").slice(0, 4000);
        reportContent.summary = latestAnalysis.summary;
        reportContent.balance = latestAnalysis.balance_sheet;
        reportContent.tax = latestAnalysis.tax_return;
        byId("report-title").textContent = latestAnalysis.filename || "Analysis results";
        byId("report-subtitle").textContent = "Review the AI-assisted drafts below.";
        byId("reports").classList.remove("hidden");
        activateReport("summary");
        recordCount += 1;
        localStorage.setItem("smeAssistRecordCount", String(recordCount));
        byId("metric-records").textContent = String(recordCount);
        setStatus("Analysis ready. Review the drafts carefully before using them.");
        byId("reports").scrollIntoView({behavior: "smooth", block: "start"});
    } catch (error) {
        setStatus(error.message || "Could not analyse this file. Please try again.", true);
    } finally {
        analyzeButton.disabled = !currentFile;
        analyzeButton.innerHTML = '<i data-lucide="sparkles"></i> Analyse records';
        setIcons();
    }
});

function appendMessage(text, role) {
    const wrapper = document.createElement("div");
    wrapper.className = role === "user" ? "user-message" : "assistant-message";
    if (role !== "user") {
        const mark = document.createElement("span");
        mark.className = "message-mark";
        const icon = document.createElement("i");
        icon.setAttribute("data-lucide", "sparkles");
        mark.append(icon);
        wrapper.append(mark);
    }
    const body = document.createElement("p");
    body.textContent = text;
    wrapper.append(body);
    chatMessages.append(wrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    setIcons();
}

async function sendChatMessage(message) {
    appendMessage(message, "user");
    const pending = document.createElement("div");
    pending.className = "assistant-message";
    pending.innerHTML = '<span class="message-mark"><i data-lucide="loader-circle"></i></span><p>Checking the guidance…</p>';
    chatMessages.append(pending);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    setIcons();
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message, language: byId("language-select").value, context: currentContext})
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "The assistant is unavailable. Try again shortly.");
        pending.remove();
        appendMessage(payload.reply, "assistant");
    } catch (error) {
        pending.remove();
        appendMessage(error.message, "assistant");
    }
}

byId("chat-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = byId("chat-input");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    input.style.height = "auto";
    await sendChatMessage(message);
});
byId("chat-input").addEventListener("input", (event) => {
    event.target.style.height = "auto";
    event.target.style.height = `${Math.min(event.target.scrollHeight, 82)}px`;
});
document.querySelectorAll(".suggestion").forEach((button) => button.addEventListener("click", () => sendChatMessage(button.textContent.trim())));

async function loadDeadlines() {
    const list = byId("deadline-list");
    try {
        const response = await fetch(`${API_BASE}/compliance/deadlines`);
        if (!response.ok) throw new Error("Could not load calendar");
        const deadlines = await response.json();
        if (!deadlines.length) throw new Error("No deadlines returned");
        const next = deadlines[0];
        byId("metric-next").textContent = next.due_date;
        byId("metric-next-name").textContent = next.obligation;
        list.replaceChildren(...deadlines.slice(0, 4).map((deadline) => {
            const row = document.createElement("div");
            row.className = "deadline-item";
            const icon = document.createElement("span");
            icon.className = "deadline-icon";
            const iconElement = document.createElement("i");
            iconElement.setAttribute("data-lucide", deadline.icon || "calendar-days");
            icon.append(iconElement);
            const detail = document.createElement("div");
            const title = document.createElement("p");
            title.className = "deadline-title";
            title.textContent = deadline.obligation;
            const subtitle = document.createElement("p");
            subtitle.className = "deadline-subtitle";
            subtitle.textContent = deadline.description;
            detail.append(title, subtitle);
            const date = document.createElement("div");
            date.className = "deadline-date";
            const dateValue = document.createElement("strong");
            dateValue.textContent = deadline.due_date;
            const status = document.createElement("span");
            status.className = "deadline-status";
            status.textContent = deadline.days_remaining < 0 ? `${Math.abs(deadline.days_remaining)} days overdue` : deadline.days_remaining === 0 ? "Due today" : `${deadline.days_remaining} days left`;
            date.append(dateValue, status);
            row.append(icon, detail, date);
            return row;
        }));
        setIcons();
    } catch {
        list.innerHTML = '<div class="loading-line">Calendar unavailable. Verify filing dates with KRA.</div>';
        byId("metric-next").textContent = "Check KRA";
        byId("metric-next-name").textContent = "Calendar unavailable";
    }
}

function startDashboard() {
    const now = new Date();
    byId("today-label").textContent = new Intl.DateTimeFormat("en-KE", {day: "numeric", month: "short", year: "numeric"}).format(now);
    byId("metric-records").textContent = String(recordCount);
    setIcons();
    loadDeadlines();
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", startDashboard);
else startDashboard();
