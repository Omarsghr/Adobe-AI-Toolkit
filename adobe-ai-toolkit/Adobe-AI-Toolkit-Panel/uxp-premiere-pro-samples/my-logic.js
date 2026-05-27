const { app } = require("premierepro");

const ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska", "video/webm", "video/ogg"];
const MAX_FILE_SIZE = 5000 * 1024 * 1024; // 5GB

document.addEventListener("DOMContentLoaded", () => {
    const uploadBtn = document.getElementById("upload-btn");
    const fileInput = document.getElementById("video-file-input");
    const statusValue = document.getElementById("status");
    const statusDetails = document.getElementById("status-details");
    const uploadArea = document.getElementById("uploadArea");
    const fileConfirmation = document.getElementById("file-confirmation");
    const fileError = document.getElementById("file-error");
    const changeFileBtn = document.getElementById("change-file-btn");

    // 🧠 عناصر الـ Few-Shot Analogy Engine الجديدة
    const styleNameInput = document.getElementById("style-name");
    const styleTypeInput = document.getElementById("style-type");
    const referenceJsonInput = document.getElementById("reference-json");

    // Handle click on upload area to trigger file input 
    uploadArea.addEventListener("click", () => {
        fileInput.click();
    });

    // Optional: open local folder/files for this panel via hidden link.
    const openLocalBtn = document.getElementById("open-local-btn");
    if (openLocalBtn) {
        openLocalBtn.style.display = "inline-block";
        openLocalBtn.addEventListener("click", () => {
            fileInput.click();
        });
    }

    // Handle drag and drop
    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = "#00b4e6";
        uploadArea.style.backgroundColor = "#303030";
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.style.borderColor = "#555555";
        uploadArea.style.backgroundColor = "#252525";
    });

    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = "#555555";
        uploadArea.style.backgroundColor = "#252525";

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    // Update display when file is selected
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Change file button
    changeFileBtn.addEventListener("click", () => {
        fileInput.value = "";
        fileConfirmation.style.display = "none";
        fileError.style.display = "none";
        uploadBtn.disabled = true;
        uploadArea.style.display = "flex";
    });

    function isValidVideoFile(file) {
        const fileType = file.type || "";
        const fileName = file.name || "";
        const isVideoExtension = /\.(mp4|mov|avi|mkv|webm|ogg)$/i.test(fileName);

        if (!fileType.startsWith("video/") && !isVideoExtension) {
            return { valid: false, error: "Invalid file type. Please upload a video file (MP4, MOV, MKV, etc.)" };
        }

        if (file.size > MAX_FILE_SIZE) {
            const sizeMB = (MAX_FILE_SIZE / (1024 * 1024)).toFixed(0);
            return { valid: false, error: `File too large. Maximum size is ${sizeMB}MB.` };
        }

        return { valid: true };
    }

    function handleFileSelection(file) {
        const validation = isValidVideoFile(file);

        if (!validation.valid) {
            showError(validation.error);
            fileInput.value = "";
            return;
        }

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;

        showFileConfirmation(file);
        fileError.style.display = "none";
        uploadBtn.disabled = false;
    }

    function showFileConfirmation(file) {
        const fileName = file.name;
        const fileSize = (file.size / (1024 * 1024)).toFixed(2);
        const rawType = file.type ? file.type.split("/")[1] : fileName.split('.').pop();
        const fileType = rawType.toUpperCase();

        const confirmationDetails = document.getElementById("confirmation-details");
        confirmationDetails.innerHTML = `<strong>${fileName}</strong> • ${fileSize} MB • ${fileType}`;

        uploadArea.style.display = "none";
        fileConfirmation.style.display = "block";
    }

    function showError(message) {
        const errorMessage = document.getElementById("error-message");
        errorMessage.textContent = message;
        fileError.style.display = "block";
        fileConfirmation.style.display = "none";
        uploadArea.style.display = "flex";
    }

    function updateStatus(message, type = "default", details = "") {
        statusValue.textContent = message;
        statusValue.className = "status-value";

        if (type === "loading") {
            statusValue.classList.add("status-loading");
        } else if (type === "error") {
            statusValue.classList.add("status-error");
        } else if (type === "success") {
            statusValue.classList.add("status-success");
        }

        if (details) {
            statusDetails.textContent = details;
        } else {
            statusDetails.textContent = "";
        }
    }

    async function probeBackendConnectivity() {
        const probes = [
            { url: "http://localhost:8005/health", label: "/health" },
            { url: "http://localhost:8005/", label: "/" }
        ];

        updateStatus("Connecting", "loading", "Checking backend connectivity (localhost:8005)...");

        for (const probe of probes) {
            try {
                const res = await fetch(probe.url, { method: "GET" });
                if (res.ok) {
                    updateStatus("Connected", "success", `Backend reachable (${probe.label}).`);
                    return true;
                }
            } catch (e) {
                // تتبع صامت لـ الجولة الموالية
            }
        }

        updateStatus("Disconnected", "error", "Could not reach backend on port 8005. Running in offline sandbox mode.");
        return false;
    }

    // 🚀 ربط وإطلاق عمليّة الـ Processing مع الـ Analogy Data
    uploadBtn.addEventListener("click", async () => {
        const file = fileInput.files[0];
        if (!file) return;

        // 1. تجميع بيانات التعلّم بالتناظر (Analogy Engine Extraction)
        const styleName = styleNameInput.value.trim() || "Default_Style";
        const styleType = styleTypeInput.value;
        const referenceJsonRaw = referenceJsonInput.value.trim();

        let parsedJson = null;

        // 2. التحقق من صحة الـ JSON إذا قام المستخدم بإدخاله
        if (referenceJsonRaw) {
            try {
                parsedJson = JSON.parse(referenceJsonRaw);
            } catch (err) {
                showError("DNA Template Error: Invalid JSON format. Please check your syntax.");
                updateStatus("Processing Aborted", "error", "Invalid template syntax.");
                return;
            }
        } else {
            // Fallback template آمن إيلا المدوّنة خاوية
            parsedJson = {
                "style_metadata": {"pacing": "standard"},
                "timeline_data": {"video_track_2_b_roll_images": []}
            };
        }

        // 3. 🌟 [Fix]: بناء الـ Multipart Payload بالتسميات الدقيقة لِكيبغيها الـ FastAPI
        const formData = new FormData();
        formData.append("file", file); // المفتح الرئيسي الموحد
        formData.append("style_name", styleName);
        formData.append("style_type", styleType);
        formData.append("reference_json_str", JSON.stringify(parsedJson));

        try {
            updateStatus("Processing", "loading", `Uploading sequence to AI Pipeline via [${styleName}] analogical blueprint...`);
            uploadBtn.disabled = true;

            // 🌟 [Fix]: التوجيه لـ الـ Endpoint الصحيحة لِّي كتستقبل الـ Analogy
            const response = await fetch("http://localhost:8005/process-with-analogy", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Server returned status code: ${response.status}`);
            }

            const result = await response.json();
            
            // نجاح العملية وتحديث الواجهة بالـ Payload النهائي
            updateStatus("Completed", "success", "Sequence mapped successfully! Screenplay payload generated.");
            console.log("🎉 Response JSON Payload:", result);

            // 4. هنا تقدر تعيط لـ ExtendScript باش تحط الـ Cuts ف الـ Timeline ديريكت
            // if (result.status === "success" && result.data) { applyToTimeline(result.data); }
            
        } catch (error) {
            console.error("Pipeline failure:", error);
            updateStatus("Pipeline Failed", "error", error.message || "An unexpected error occurred during the AI orchestration.");
        } finally {
            uploadBtn.disabled = false;
        }
    });

    // Trigger connection probe automatically on load
    probeBackendConnectivity();
});