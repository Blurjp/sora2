// DOM Elements
const videoForm = document.getElementById('videoForm');
const modeI2V = document.getElementById('modeI2V');
const modeT2V = document.getElementById('modeT2V');
const imageUploadSection = document.getElementById('imageUploadSection');
const imageInput = document.getElementById('imageInput');
const imageRequired = document.getElementById('imageRequired');
const uploadArea = document.getElementById('uploadArea');
const previewContainer = document.getElementById('previewContainer');
const imagePreview = document.getElementById('imagePreview');
const removeImage = document.getElementById('removeImage');
const promptInput = document.getElementById('promptInput');
const charCount = document.getElementById('charCount');
const motionScoreInput = document.getElementById('motionScoreInput');
const motionScoreValue = document.getElementById('motionScoreValue');
const generateBtn = document.getElementById('generateBtn');
const btnText = document.querySelector('.btn-text');
const btnLoader = document.querySelector('.btn-loader');

// Cards
const progressCard = document.getElementById('progressCard');
const resultCard = document.getElementById('resultCard');
const errorCard = document.getElementById('errorCard');

// Progress elements
const statusBadge = document.getElementById('statusBadge');
const statusMessage = document.getElementById('statusMessage');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

// Result elements
const resultVideo = document.getElementById('resultVideo');
const downloadBtn = document.getElementById('downloadBtn');
const newVideoBtn = document.getElementById('newVideoBtn');

// Error elements
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');

// State
let currentVideoId = null;
let statusCheckInterval = null;

// Generation Mode Handling
let currentMode = 'i2v'; // Default mode

modeI2V.addEventListener('click', () => {
    currentMode = 'i2v';
    modeI2V.classList.add('mode-active');
    modeT2V.classList.remove('mode-active');
    imageUploadSection.style.display = 'block';
    imageInput.required = true;
    imageRequired.style.display = 'inline';
});

modeT2V.addEventListener('click', () => {
    currentMode = 't2v';
    modeT2V.classList.add('mode-active');
    modeI2V.classList.remove('mode-active');
    imageUploadSection.style.display = 'none';
    imageInput.required = false;
    imageRequired.style.display = 'none';
});

// Image Upload Handling
imageInput.addEventListener('change', handleImageSelect);
removeImage.addEventListener('click', clearImage);

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#667eea';
    uploadArea.style.background = '#f7fafc';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = '#cbd5e0';
    uploadArea.style.background = '';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#cbd5e0';
    uploadArea.style.background = '';

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        imageInput.files = files;
        handleImageSelect();
    }
});

function handleImageSelect() {
    const file = imageInput.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            document.querySelector('.upload-placeholder').style.display = 'none';
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
}

function clearImage() {
    imageInput.value = '';
    imagePreview.src = '';
    document.querySelector('.upload-placeholder').style.display = 'block';
    previewContainer.style.display = 'none';
}

// Character counter
promptInput.addEventListener('input', () => {
    const count = promptInput.value.length;
    charCount.textContent = count;
});

// Motion score slider
motionScoreInput.addEventListener('input', () => {
    motionScoreValue.textContent = motionScoreInput.value;
});

// Advanced settings sliders
const numStepsInput = document.getElementById('numStepsInput');
const numStepsValue = document.getElementById('numStepsValue');
const guidanceInput = document.getElementById('guidanceInput');
const guidanceValue = document.getElementById('guidanceValue');
const guidanceImgInput = document.getElementById('guidanceImgInput');
const guidanceImgValue = document.getElementById('guidanceImgValue');
const qualityPresetInput = document.getElementById('qualityPresetInput');
const advancedSettings = document.getElementById('advancedSettings');

// Quality indicators
const stepsIndicator = document.getElementById('stepsIndicator');
const guidanceIndicator = document.getElementById('guidanceIndicator');
const imgIndicator = document.getElementById('imgIndicator');

// New control elements
const faceDetailInput = document.getElementById('faceDetailInput');
const faceDetailValue = document.getElementById('faceDetailValue');
const faceDetailIndicator = document.getElementById('faceDetailIndicator');
const aestheticScoreInput = document.getElementById('aestheticScoreInput');
const aestheticScoreValue = document.getElementById('aestheticScoreValue');
const sharpnessInput = document.getElementById('sharpnessInput');
const sharpnessValue = document.getElementById('sharpnessValue');
const negativePromptInput = document.getElementById('negativePromptInput');
const faceEnhanceInput = document.getElementById('faceEnhanceInput');
const denoiseInput = document.getElementById('denoiseInput');
const temporalSmoothing = document.getElementById('temporalSmoothing');

// Quality presets
const qualityPresets = {
    fast: { steps: 50, guidance: 7.0, guidanceImg: 2.0, faceDetail: 2.5, aesthetic: 5.0 },
    balanced: { steps: 100, guidance: 10.0, guidanceImg: 3.0, faceDetail: 3.5, aesthetic: 6.0 },
    high: { steps: 120, guidance: 12.0, guidanceImg: 3.5, faceDetail: 4.5, aesthetic: 6.5 },
    maximum: { steps: 150, guidance: 15.0, guidanceImg: 4.5, faceDetail: 6.0, aesthetic: 7.5 },
    ultra: { steps: 200, guidance: 18.0, guidanceImg: 6.0, faceDetail: 8.0, aesthetic: 8.5 },
    extreme: { steps: 250, guidance: 19.5, guidanceImg: 8.0, faceDetail: 9.5, aesthetic: 9.0 },
    insane: { steps: 300, guidance: 20.0, guidanceImg: 10.0, faceDetail: 10.0, aesthetic: 9.5 }
};

// Update quality indicators
function updateQualityIndicators() {
    // Steps indicator
    const steps = parseInt(numStepsInput.value);
    if (steps < 75) {
        stepsIndicator.textContent = 'Fast';
        stepsIndicator.style.color = '#48bb78';
    } else if (steps < 110) {
        stepsIndicator.textContent = 'Balanced';
        stepsIndicator.style.color = '#4299e1';
    } else if (steps < 135) {
        stepsIndicator.textContent = 'High';
        stepsIndicator.style.color = '#9f7aea';
    } else if (steps < 175) {
        stepsIndicator.textContent = 'Maximum';
        stepsIndicator.style.color = '#ed8936';
    } else if (steps < 225) {
        stepsIndicator.textContent = 'Ultra';
        stepsIndicator.style.color = '#f56565';
    } else if (steps < 275) {
        stepsIndicator.textContent = 'Extreme';
        stepsIndicator.style.color = '#d53f8c';
        stepsIndicator.style.fontWeight = '700';
    } else {
        stepsIndicator.textContent = 'INSANE';
        stepsIndicator.style.color = '#c53030';
        stepsIndicator.style.fontWeight = '700';
        stepsIndicator.style.textShadow = '0 0 10px rgba(197, 48, 48, 0.5)';
    }

    // Guidance indicator
    const guidance = parseFloat(guidanceInput.value);
    if (guidance < 8) {
        guidanceIndicator.textContent = 'Weak';
    } else if (guidance < 13) {
        guidanceIndicator.textContent = 'Strong';
    } else {
        guidanceIndicator.textContent = 'Very Strong';
    }

    // Image influence indicator
    const imgGuidance = parseFloat(guidanceImgInput.value);
    if (imgGuidance < 2.5) {
        imgIndicator.textContent = 'Low';
    } else if (imgGuidance < 4.5) {
        imgIndicator.textContent = 'Strong';
    } else {
        imgIndicator.textContent = 'Maximum';
    }

    // Face detail indicator
    const faceDetail = parseFloat(faceDetailInput.value);
    if (faceDetail < 3) {
        faceDetailIndicator.textContent = 'Low';
        faceDetailIndicator.style.color = '#a0aec0';
    } else if (faceDetail < 5.5) {
        faceDetailIndicator.textContent = 'High';
        faceDetailIndicator.style.color = '#9f7aea';
    } else {
        faceDetailIndicator.textContent = 'Maximum';
        faceDetailIndicator.style.color = '#f56565';
    }
}

// Quality preset selection
qualityPresetInput.addEventListener('change', () => {
    const preset = qualityPresetInput.value;

    if (preset === 'custom') {
        // Open advanced settings
        advancedSettings.open = true;
        return;
    }

    const settings = qualityPresets[preset];
    if (settings) {
        numStepsInput.value = settings.steps;
        guidanceInput.value = settings.guidance;
        guidanceImgInput.value = settings.guidanceImg;
        faceDetailInput.value = settings.faceDetail;
        aestheticScoreInput.value = settings.aesthetic;

        // Update displayed values
        numStepsValue.textContent = settings.steps;
        guidanceValue.textContent = settings.guidance.toFixed(1);
        guidanceImgValue.textContent = settings.guidanceImg.toFixed(1);
        faceDetailValue.textContent = settings.faceDetail.toFixed(1);
        aestheticScoreValue.textContent = settings.aesthetic.toFixed(1);

        // Update indicators
        updateQualityIndicators();
    }
});

// New slider event listeners
faceDetailInput.addEventListener('input', () => {
    faceDetailValue.textContent = parseFloat(faceDetailInput.value).toFixed(1);
    updateQualityIndicators();
    if (qualityPresetInput.value !== 'custom') {
        qualityPresetInput.value = 'custom';
    }
});

aestheticScoreInput.addEventListener('input', () => {
    aestheticScoreValue.textContent = parseFloat(aestheticScoreInput.value).toFixed(1);
    if (qualityPresetInput.value !== 'custom') {
        qualityPresetInput.value = 'custom';
    }
});

sharpnessInput.addEventListener('input', () => {
    sharpnessValue.textContent = parseFloat(sharpnessInput.value).toFixed(1);
    if (qualityPresetInput.value !== 'custom') {
        qualityPresetInput.value = 'custom';
    }
});

// Update slider values and indicators
numStepsInput.addEventListener('input', () => {
    numStepsValue.textContent = numStepsInput.value;
    updateQualityIndicators();

    // If user manually adjusts, switch to custom
    if (qualityPresetInput.value !== 'custom') {
        qualityPresetInput.value = 'custom';
    }
});

guidanceInput.addEventListener('input', () => {
    guidanceValue.textContent = parseFloat(guidanceInput.value).toFixed(1);
    updateQualityIndicators();

    // If user manually adjusts, switch to custom
    if (qualityPresetInput.value !== 'custom') {
        qualityPresetInput.value = 'custom';
    }
});

guidanceImgInput.addEventListener('input', () => {
    guidanceImgValue.textContent = parseFloat(guidanceImgInput.value).toFixed(1);
    updateQualityIndicators();

    // If user manually adjusts, switch to custom
    if (qualityPresetInput.value !== 'custom') {
        qualityPresetInput.value = 'custom';
    }
});

// Initialize indicators on page load
updateQualityIndicators();

// Negative Prompt Presets
const negativePromptPresets = {
    default: "blurry, distorted face, deformed, ugly, low quality, pixelated, artifacts, watermark, text, bad anatomy, bad proportions",
    faces: "blurry face, distorted face, deformed face, asymmetric face, bad eyes, closed eyes, weird eyes, bad teeth, deformed hands, extra fingers, missing fingers, bad anatomy, disfigured",
    cinematic: "low quality, pixelated, blurry, overexposed, underexposed, shaky, amateur, grainy, compression artifacts, watermark, logo, text overlay",
    clear: ""
};

document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        const preset = btn.dataset.preset;
        negativePromptInput.value = negativePromptPresets[preset];

        // Visual feedback
        document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

// Set default preset button as active on load
document.querySelector('.preset-btn[data-preset="default"]').classList.add('active');

// Form submission
videoForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Reset UI
    hideAllCards();

    // Prepare form data
    const formData = new FormData();

    // Add generation mode
    formData.append('mode', currentMode);

    // Add image only for i2v mode
    if (currentMode === 'i2v') {
        if (!imageInput.files || !imageInput.files[0]) {
            throw new Error('Please select an image for Image-to-Video mode');
        }
        formData.append('image', imageInput.files[0]);
    }

    formData.append('prompt', promptInput.value);
    formData.append('duration', document.getElementById('durationInput').value);
    formData.append('aspect_ratio', document.getElementById('aspectRatioInput').value);
    formData.append('motion_score', motionScoreInput.value);

    // Advanced quality settings
    formData.append('num_steps', numStepsInput.value);
    formData.append('guidance', guidanceInput.value);
    formData.append('guidance_img', guidanceImgInput.value);

    // Facial and detail enhancement
    formData.append('face_detail', faceDetailInput.value);
    formData.append('aesthetic_score', aestheticScoreInput.value);
    formData.append('sharpness', sharpnessInput.value);

    // Negative prompt
    if (negativePromptInput.value.trim()) {
        formData.append('negative_prompt', negativePromptInput.value.trim());
    }

    // Advanced toggles
    formData.append('face_enhance', faceEnhanceInput.checked);
    formData.append('denoise', denoiseInput.checked);
    formData.append('temporal_smoothing', temporalSmoothing.checked);

    const seed = document.getElementById('seedInput').value;
    if (seed) {
        formData.append('seed', seed);
    }

    formData.append('refine_prompt', document.getElementById('refinePromptInput').checked);

    // Update button state
    generateBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'flex';

    try {
        // Submit generation request
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start generation');
        }

        const data = await response.json();
        currentVideoId = data.video_id;

        // Show progress card
        progressCard.style.display = 'block';
        updateProgress(0, 'processing', 'Your video is being generated...');

        // Start polling for status
        startStatusPolling();

        // Don't re-enable button here - keep it disabled until generation completes
        // The button will be re-enabled in checkStatus() when status is completed or failed

    } catch (error) {
        showError(error.message);
        // Only re-enable button on error (not on successful submission)
        generateBtn.disabled = false;
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
    }
});

// Status polling
function startStatusPolling() {
    statusCheckInterval = setInterval(checkStatus, 3000);
    checkStatus(); // Check immediately
}

function stopStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

async function checkStatus() {
    if (!currentVideoId) return;

    try {
        const response = await fetch(`/api/status/${currentVideoId}`);

        if (!response.ok) {
            throw new Error('Failed to check status');
        }

        const data = await response.json();

        if (data.status === 'completed') {
            stopStatusPolling();
            showResult(data.video_url);
            // Re-enable the generate button
            generateBtn.disabled = false;
            btnText.style.display = 'block';
            btnLoader.style.display = 'none';
        } else if (data.status === 'failed') {
            stopStatusPolling();
            showError(data.error || 'Video generation failed');
            // Re-enable the generate button
            generateBtn.disabled = false;
            btnText.style.display = 'block';
            btnLoader.style.display = 'none';
        } else {
            // Update progress (simulated since Open-Sora doesn't provide real progress)
            const progress = data.progress || Math.min(90, Date.now() % 90);
            updateProgress(progress, data.status, 'Generating video... This may take 1-5 minutes.');
        }

    } catch (error) {
        console.error('Status check error:', error);
        stopStatusPolling();
        showError('Lost connection while checking progress. Please try again.');
        generateBtn.disabled = false;
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
    }
}

// UI Updates
function updateProgress(percent, status, message) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `${Math.round(percent)}%`;
    statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusMessage.textContent = message;
}

function showResult(videoUrl) {
    hideAllCards();
    resultCard.style.display = 'block';
    resultVideo.src = videoUrl;
    downloadBtn.href = videoUrl;
}

function showError(message) {
    hideAllCards();
    errorCard.style.display = 'block';
    errorMessage.textContent = message;
}

function hideAllCards() {
    progressCard.style.display = 'none';
    resultCard.style.display = 'none';
    errorCard.style.display = 'none';
}

// Button handlers
newVideoBtn.addEventListener('click', () => {
    hideAllCards();
    currentVideoId = null;
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

retryBtn.addEventListener('click', () => {
    hideAllCards();
    currentVideoId = null;
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopStatusPolling();
});
