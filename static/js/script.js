/**
 * DocuMind – Frontend Application Script
 * Vanilla JavaScript (ChatGPT-inspired UX + 21st.dev AI Thinking Orb interactions)
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    let currentConversationId = null;
    let activeDocId = null;
    let isGenerating = false;

    // DOM Elements
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const attachPdfBtn = document.getElementById("attachPdfBtn");
    const pdfFileInput = document.getElementById("pdfFileInput");
    const uploadDropzone = document.getElementById("uploadDropzone");
    const browseFileBtn = document.getElementById("browseFileBtn");
    const quickUploadTrigger = document.getElementById("quickUploadTrigger");

    const welcomeScreen = document.getElementById("welcomeScreen");
    const messagesStream = document.getElementById("messagesStream");
    const chatViewport = document.getElementById("chatViewport");
    const thinkingIndicator = document.getElementById("thinkingIndicator");

    const processingCard = document.getElementById("processingCard");
    const processingPercent = document.getElementById("processingPercent");
    const progressBarFill = document.getElementById("progressBarFill");
    const processingStatusText = document.getElementById("processingStatusText");
    const processingStep = document.getElementById("processingStep");

    const documentsList = document.getElementById("documentsList");
    const historyList = document.getElementById("historyList");
    const newChatBtn = document.getElementById("newChatBtn");
    const clearHistoryBtn = document.getElementById("clearHistoryBtn");

    const activeDocBadge = document.getElementById("activeDocBadge");
    const activeDocName = document.getElementById("activeDocName");
    const activeDocStats = document.getElementById("activeDocStats");
    const deleteActiveDocBtn = document.getElementById("deleteActiveDocBtn");

    const sidebar = document.getElementById("sidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const closeSidebarBtn = document.getElementById("closeSidebarBtn");
    const toastContainer = document.getElementById("toastContainer");

    // Initialize Markdown Parser
    if (window.marked) {
        marked.setOptions({
            breaks: true,
            gfm: true,
            highlight: function (code, lang) {
                if (window.hljs && lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return window.hljs ? hljs.highlightAuto(code).value : code;
            }
        });
    }

    // ==========================================
    // UI Helpers: Toast Notifications
    // ==========================================
    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${message}</span>`;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(100%)";
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // ==========================================
    // Mobile Sidebar Handling
    // ==========================================
    function toggleSidebar(open) {
        if (open) {
            sidebar.classList.add("open");
            sidebarOverlay.classList.add("active");
        } else {
            sidebar.classList.remove("open");
            sidebarOverlay.classList.remove("active");
        }
    }

    mobileMenuBtn?.addEventListener("click", () => toggleSidebar(true));
    closeSidebarBtn?.addEventListener("click", () => toggleSidebar(false));
    sidebarOverlay?.addEventListener("click", () => toggleSidebar(false));

    // ==========================================
    // Auto-Resize Textarea
    // ==========================================
    function adjustTextareaHeight() {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + "px";
        sendBtn.disabled = chatInput.value.trim().length === 0 || isGenerating;
    }

    chatInput.addEventListener("input", adjustTextareaHeight);

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) {
                chatForm.requestSubmit();
            }
        }
    });

    // ==========================================
    // Document Upload & Processing
    // ==========================================
    function triggerFileSelect() {
        pdfFileInput.value = "";
        pdfFileInput.click();
    }

    browseFileBtn?.addEventListener("click", (e) => {
        e.stopPropagation();
        triggerFileSelect();
    });

    uploadDropzone?.addEventListener("click", () => triggerFileSelect());
    attachPdfBtn?.addEventListener("click", () => triggerFileSelect());
    quickUploadTrigger?.addEventListener("click", () => triggerFileSelect());

    // Drag and drop handlers
    ["dragenter", "dragover"].forEach(event => {
        uploadDropzone?.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadDropzone.classList.add("drag-over");
        });
    });

    ["dragleave", "drop"].forEach(event => {
        uploadDropzone?.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadDropzone.classList.remove("drag-over");
        });
    });

    uploadDropzone?.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    pdfFileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            showToast("Please upload a valid PDF document.", "error");
            return;
        }

        if (file.size > 32 * 1024 * 1024) {
            showToast("PDF file exceeds the maximum 32MB limit.", "error");
            return;
        }

        // Show processing card
        uploadDropzone.style.display = "none";
        processingCard.style.display = "flex";
        processingStatusText.textContent = `Uploading ${file.name}...`;
        progressBarFill.style.width = "20%";
        processingPercent.textContent = "20%";
        processingStep.textContent = "Sending document to server...";

        const formData = new FormData();
        formData.append("file", file);

        // Progress animation simulator
        let simulatedProgress = 20;
        const progressInterval = setInterval(() => {
            if (simulatedProgress < 85) {
                simulatedProgress += 8;
                progressBarFill.style.width = simulatedProgress + "%";
                processingPercent.textContent = simulatedProgress + "%";
                if (simulatedProgress > 40) {
                    processingStep.textContent = "Chunking into 1,000-char windows (200 overlap)...";
                }
                if (simulatedProgress > 65) {
                    processingStep.textContent = "Computing HuggingFace embeddings & building ChromaDB MMR index...";
                }
            }
        }, 500);

        try {
            const res = await fetch("/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            clearInterval(progressInterval);

            if (data.success) {
                progressBarFill.style.width = "100%";
                processingPercent.textContent = "100%";
                processingStatusText.textContent = "Processing Complete!";
                processingStep.textContent = `Indexed ${data.document.pages} pages into ${data.document.chunks} vector chunks.`;

                activeDocId = data.document.id;
                showToast(`'${data.document.filename}' processed successfully!`, "success");

                setTimeout(() => {
                    processingCard.style.display = "none";
                    uploadDropzone.style.display = "flex";
                }, 2000);

                await fetchDocuments();
            } else {
                throw new Error(data.error || "Failed to process PDF.");
            }
        } catch (err) {
            clearInterval(progressInterval);
            processingCard.style.display = "none";
            uploadDropzone.style.display = "flex";
            showToast(err.message || "Error uploading document.", "error");
        }
    }

    // ==========================================
    // Documents Management
    // ==========================================
    async function fetchDocuments() {
        try {
            const res = await fetch("/documents");
            const data = await res.json();

            if (data.success) {
                renderDocumentsList(data.documents, data.active_doc_id);
            }
        } catch (err) {
            console.error("Error loading documents:", err);
        }
    }

    function renderDocumentsList(docs, activeId) {
        activeDocId = activeId;
        if (!docs || docs.length === 0) {
            documentsList.innerHTML = `<div class="empty-state-hint">No document uploaded yet</div>`;
            activeDocBadge.style.display = "none";
            deleteActiveDocBtn.style.display = "none";
            return;
        }

        documentsList.innerHTML = "";
        let currentActive = null;

        docs.forEach(doc => {
            const isActive = doc.id === activeDocId;
            if (isActive) currentActive = doc;

            const item = document.createElement("div");
            item.className = `doc-item ${isActive ? "active" : ""}`;
            item.innerHTML = `
                <div class="doc-item-info">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <span class="doc-item-name" title="${doc.filename}">${doc.filename}</span>
                    <span class="doc-item-meta">${doc.pages_count}p</span>
                </div>
                <button class="doc-delete-btn" title="Delete document" data-id="${doc.id}">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            `;

            item.addEventListener("click", (e) => {
                if (e.target.closest(".doc-delete-btn")) return;
                selectDocument(doc.id);
            });

            const deleteBtn = item.querySelector(".doc-delete-btn");
            deleteBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                deleteDocument(doc.id, doc.filename);
            });

            documentsList.appendChild(item);
        });

        if (currentActive) {
            activeDocBadge.style.display = "flex";
            activeDocName.textContent = currentActive.filename;
            activeDocStats.textContent = `• ${currentActive.pages_count} pages (${currentActive.chunks_count} chunks)`;
            deleteActiveDocBtn.style.display = "flex";
        } else {
            activeDocBadge.style.display = "none";
            deleteActiveDocBtn.style.display = "none";
        }
    }

    async function selectDocument(docId) {
        try {
            const res = await fetch("/select-document", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ document_id: docId })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Switched active document to '${data.filename}'`, "info");
                await fetchDocuments();
            }
        } catch (err) {
            showToast("Failed to switch document", "error");
        }
    }

    async function deleteDocument(docId, filename) {
        if (!confirm(`Are you sure you want to remove '${filename}' and its vector store?`)) {
            return;
        }

        try {
            const res = await fetch("/delete-document", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ document_id: docId })
            });
            const data = await res.json();
            if (data.success) {
                showToast(data.message, "success");
                await fetchDocuments();
            } else {
                showToast(data.error || "Failed to delete document", "error");
            }
        } catch (err) {
            showToast("Error deleting document", "error");
        }
    }

    deleteActiveDocBtn?.addEventListener("click", () => {
        if (activeDocId) {
            deleteDocument(activeDocId, activeDocName.textContent);
        }
    });

    // ==========================================
    // Chat Message Handling & RAG Pipeline
    // ==========================================
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message || isGenerating) return;

        // Reset composer
        chatInput.value = "";
        adjustTextareaHeight();

        await sendMessage(message);
    });

    async function sendMessage(userQuery) {
        // Transition from welcome screen to chat messages
        welcomeScreen.style.display = "none";
        messagesStream.style.display = "flex";

        // Append user message
        appendMessage({
            role: "user",
            content: userQuery
        });

        // Set generating state & show 21st.dev Thinking Orb Indicator
        setGeneratingState(true);
        scrollChatToBottom();

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userQuery,
                    conversation_id: currentConversationId,
                    document_id: activeDocId
                })
            });

            const data = await res.json();

            if (data.success) {
                currentConversationId = data.conversation_id;
                appendMessage({
                    role: "assistant",
                    content: data.response,
                    sources: data.sources
                });
                await fetchConversations();
            } else {
                appendMessage({
                    role: "assistant",
                    content: `⚠️ **Error:** ${data.error || "Could not retrieve an answer."}`
                });
                showToast(data.error || "An error occurred", "error");
            }
        } catch (err) {
            appendMessage({
                role: "assistant",
                content: `⚠️ **Connection Error:** Failed to communicate with DocuMind backend.`
            });
            showToast("Server connection error", "error");
        } finally {
            setGeneratingState(false);
            scrollChatToBottom();
        }
    }

    function setGeneratingState(generating) {
        isGenerating = generating;
        thinkingIndicator.style.display = generating ? "flex" : "none";
        sendBtn.disabled = generating || chatInput.value.trim().length === 0;
        chatInput.disabled = generating;
        if (!generating) {
            chatInput.focus();
        }
    }

    function appendMessage({ role, content, sources }) {
        const row = document.createElement("div");
        row.className = `message-row ${role}`;

        let renderedContent = content;
        if (role === "assistant" && window.marked && window.DOMPurify) {
            renderedContent = DOMPurify.sanitize(marked.parse(content));
        } else {
            // Basic escape for user text
            const div = document.createElement("div");
            div.textContent = content;
            renderedContent = div.innerHTML.replace(/\n/g, "<br>");
        }

        let sourcesHtml = "";
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="sources-container">
                    <span class="sources-label">Sources:</span>
                    ${sources.map(s => `
                        <span class="source-badge" title="${s.snippet.replace(/"/g, '&quot;')}">
                            📄 Page ${s.page}
                        </span>
                    `).join("")}
                </div>
            `;
        }

        if (role === "assistant") {
            row.innerHTML = `
                <div class="message-avatar assistant">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                </div>
                <div class="message-body">
                    <div class="message-content">${renderedContent}</div>
                    ${sourcesHtml}
                </div>
            `;
        } else {
            row.innerHTML = `
                <div class="message-body">
                    <div class="message-content">${renderedContent}</div>
                </div>
            `;
        }

        messagesStream.appendChild(row);
        scrollChatToBottom();
    }

    function scrollChatToBottom() {
        setTimeout(() => {
            chatViewport.scrollTop = chatViewport.scrollHeight;
        }, 50);
    }

    // ==========================================
    // Suggested Prompt Cards
    // ==========================================
    document.querySelectorAll(".prompt-card").forEach(card => {
        card.addEventListener("click", () => {
            const prompt = card.getAttribute("data-prompt");
            if (prompt) {
                sendMessage(prompt);
            }
        });
    });

    // ==========================================
    // Conversation History Management
    // ==========================================
    async function fetchConversations() {
        try {
            const res = await fetch("/conversations");
            const data = await res.json();
            if (data.success) {
                renderConversationsList(data.conversations);
            }
        } catch (err) {
            console.error("Error loading conversations:", err);
        }
    }

    function renderConversationsList(conversations) {
        if (!conversations || conversations.length === 0) {
            historyList.innerHTML = `<div class="empty-state-hint">No previous conversations</div>`;
            return;
        }

        historyList.innerHTML = "";
        conversations.forEach(c => {
            const item = document.createElement("div");
            item.className = `history-item ${c.id === currentConversationId ? "active" : ""}`;
            item.innerHTML = `
                <span class="doc-item-name" title="${c.title}">${c.title}</span>
                <span class="doc-item-meta">${c.message_count || ''}</span>
            `;

            item.addEventListener("click", () => loadConversation(c.id));
            historyList.appendChild(item);
        });
    }

    async function loadConversation(convId) {
        try {
            const res = await fetch(`/history?conversation_id=${convId}`);
            const data = await res.json();
            if (data.success) {
                currentConversationId = data.conversation_id;
                welcomeScreen.style.display = "none";
                messagesStream.style.display = "flex";
                messagesStream.innerHTML = "";

                data.messages.forEach(msg => {
                    appendMessage({
                        role: msg.role,
                        content: msg.content,
                        sources: msg.sources
                    });
                });

                await fetchConversations();
                toggleSidebar(false);
            }
        } catch (err) {
            showToast("Failed to load conversation", "error");
        }
    }

    newChatBtn?.addEventListener("click", () => {
        currentConversationId = null;
        messagesStream.innerHTML = "";
        messagesStream.style.display = "none";
        welcomeScreen.style.display = "flex";
        chatInput.value = "";
        adjustTextareaHeight();
        fetchConversations();
        toggleSidebar(false);
    });

    clearHistoryBtn?.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to clear all conversation history?")) return;

        try {
            const res = await fetch("/clear", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                showToast(data.message, "success");
                newChatBtn.click();
                await fetchConversations();
            }
        } catch (err) {
            showToast("Error clearing chat history", "error");
        }
    });

    // Initial Load
    fetchDocuments();
    fetchConversations();
});
