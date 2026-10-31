(() => {
    "use strict";

    const root = document.documentElement;
    const themeButtons = document.querySelectorAll("[data-theme-toggle]");
    const applyTheme = (theme) => {
        const isLight = theme === "light";
        root.dataset.theme = isLight ? "light" : "dark";
        themeButtons.forEach((button) => {
            button.setAttribute("aria-pressed", String(isLight));
            button.setAttribute("aria-label", `Switch to ${isLight ? "dark" : "light"} theme`);
            const label = button.querySelector("[data-theme-label]");
            if (label) label.textContent = isLight ? "Dark mode" : "Light mode";
        });
    };
    try { applyTheme(localStorage.getItem("samir-theme")); } catch (_) { applyTheme("dark"); }
    themeButtons.forEach((button) => button.addEventListener("click", () => {
        const theme = root.dataset.theme === "light" ? "dark" : "light";
        applyTheme(theme);
        try { localStorage.setItem("samir-theme", theme); } catch (_) { /* Storage is optional. */ }
    }));

    const progress = document.querySelector("[data-reading-progress] span");
    if (progress) {
        let scheduled = false;
        const updateProgress = () => {
            const available = document.documentElement.scrollHeight - window.innerHeight;
            const ratio = available > 0 ? Math.min(1, Math.max(0, window.scrollY / available)) : 1;
            progress.style.transform = `scaleX(${ratio})`;
            scheduled = false;
        };
        window.addEventListener("scroll", () => {
            if (!scheduled) { scheduled = true; requestAnimationFrame(updateProgress); }
        }, { passive: true });
        window.addEventListener("resize", updateProgress);
        updateProgress();
    }

    document.querySelectorAll("[data-copy-link]").forEach((button) => {
        button.addEventListener("click", async () => {
            const status = document.querySelector("[data-copy-status]");
            try {
                await navigator.clipboard.writeText(window.location.href);
                if (status) status.textContent = "Article link copied.";
                button.textContent = "Copied ✓";
            } catch (_) {
                if (status) status.textContent = "Copy the article URL from your address bar.";
            }
        });
    });

    const editor = document.querySelector("[data-editor]");
    if (!editor) return;
    const title = editor.querySelector("#id_title");
    const body = editor.querySelector("#id_body");
    if (!title || !body) return;

    const original = { title: title.value, body: body.value };
    const saveState = editor.querySelector("[data-save-state]");
    let submitting = false;
    const initiallyUnsaved = editor.dataset.unsaved === "true";
    const hasChanges = () => initiallyUnsaved || title.value !== original.title || body.value !== original.body;
    const updateEditor = () => {
        const words = body.value.trim() ? body.value.trim().split(/\s+/u).length : 0;
        const readingTime = Math.max(1, Math.ceil(words / 200));
        editor.querySelector("[data-title-count]").textContent = String(title.value.length);
        editor.querySelector("[data-word-count]").textContent = String(words);
        editor.querySelector("[data-reading-time]").textContent = String(readingTime);
        editor.querySelector("[data-preview-reading-time]").textContent = String(readingTime);
        editor.querySelector("[data-preview-title]").textContent = title.value.trim() || "Untitled article";
        editor.querySelector("[data-preview-body]").textContent = body.value || "Your preview will appear here.";
        if (saveState) saveState.textContent = hasChanges() ? "Unsaved changes" : "Ready to write";
    };
    title.addEventListener("input", updateEditor);
    body.addEventListener("input", updateEditor);
    updateEditor();

    const setEditorMode = (mode) => {
        editor.querySelectorAll("[data-editor-mode]").forEach((control) => {
            const active = control.dataset.editorMode === mode;
            control.classList.toggle("is-active", active);
            control.setAttribute("aria-pressed", String(active));
        });
        editor.querySelectorAll("[data-editor-pane]").forEach((pane) => {
            pane.hidden = pane.dataset.editorPane !== mode;
        });
        updateEditor();
    };
    editor.querySelectorAll("[data-editor-mode]").forEach((button) => {
        button.addEventListener("click", () => setEditorMode(button.dataset.editorMode));
    });

    // Reveal required inputs before the browser focuses an invalid field.
    editor.addEventListener("invalid", () => setEditorMode("write"), true);

    const focusButton = editor.querySelector("[data-editor-focus]");
    if (focusButton) focusButton.addEventListener("click", () => {
        const focused = document.body.classList.toggle("editor-focus");
        focusButton.setAttribute("aria-pressed", String(focused));
        focusButton.textContent = focused ? "Exit focus" : "Focus mode";
    });

    editor.addEventListener("submit", () => { submitting = true; });
    window.addEventListener("beforeunload", (event) => {
        if (!submitting && hasChanges()) {
            event.preventDefault();
            event.returnValue = "";
        }
    });
})();
