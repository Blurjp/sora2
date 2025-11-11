// DOM Elements
const videoForm = document.getElementById('videoForm');
const imageInput = document.getElementById('imageInput');
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

numStepsInput.addEventListener('input', () => {
    numStepsValue.textContent = numStepsInput.value;
});

guidanceInput.addEventListener('input', () => {
    guidanceValue.textContent = parseFloat(guidanceInput.value).toFixed(1);
});

guidanceImgInput.addEventListener('input', () => {
    guidanceImgValue.textContent = parseFloat(guidanceImgInput.value).toFixed(1);
});

// Form submission
videoForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Reset UI
    hideAllCards();

    // Prepare form data
    const formData = new FormData();
    formData.append('image', imageInput.files[0]);
    formData.append('prompt', promptInput.value);
    formData.append('duration', document.getElementById('durationInput').value);
    formData.append('aspect_ratio', document.getElementById('aspectRatioInput').value);
    formData.append('motion_score', motionScoreInput.value);

    // Advanced quality settings
    formData.append('num_steps', numStepsInput.value);
    formData.append('guidance', guidanceInput.value);
    formData.append('guidance_img', guidanceImgInput.value);

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
