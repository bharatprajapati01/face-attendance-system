/* ===== WEBCAM / FACE RECOGNITION CAMERA MODULE ===== */

const CameraModule = (() => {
  let stream = null;
  let isCapturing = false;
  let captureInterval = null;
  let detectionCount = 0;
  const DETECTION_THRESHOLD = 3; // frames before confirming

  const elements = {
    video: null,
    canvas: null,
    overlay: null,
    statusText: null,
    statusDot: null,
    resultCard: null,
  };

  function init(config = {}) {
    elements.video = document.getElementById(config.videoId || 'cameraFeed');
    elements.canvas = document.getElementById(config.canvasId || 'snapshotCanvas');
    elements.overlay = document.getElementById(config.overlayId || 'faceOverlay');
    elements.statusText = document.getElementById(config.statusId || 'statusText');
    elements.statusDot = document.getElementById(config.statusDotId || 'statusDot');
    elements.resultCard = document.getElementById(config.resultId || 'resultCard');
  }

  async function startCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
      });
      elements.video.srcObject = stream;
      elements.video.play();
      updateStatus('Camera ready. Position your face in the frame.', 'idle');
      return true;
    } catch (err) {
      console.error('Camera error:', err);
      updateStatus('❌ Camera access denied. Please allow camera permissions.', 'error');
      return false;
    }
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    stopCapturing();
  }

  function captureFrame() {
    if (!elements.video || !elements.canvas) return null;
    const ctx = elements.canvas.getContext('2d');
    elements.canvas.width = elements.video.videoWidth || 640;
    elements.canvas.height = elements.video.videoHeight || 480;
    ctx.drawImage(elements.video, 0, 0);
    return elements.canvas.toDataURL('image/jpeg', 0.8);
  }

  function updateStatus(message, state = 'idle') {
    if (elements.statusText) elements.statusText.textContent = message;
    if (elements.statusDot) {
      elements.statusDot.className = 'status-dot';
      elements.statusDot.classList.add(`dot-${state}`);
    }
  }

  function startCapturing(endpoint, onSuccess, onError) {
    if (isCapturing) return;
    isCapturing = true;
    detectionCount = 0;
    updateStatus('🔍 Scanning for face...', 'scanning');

    captureInterval = setInterval(async () => {
      const imageData = captureFrame();
      if (!imageData) return;

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: imageData })
        });

        const result = await response.json();

        if (result.success) {
          detectionCount++;
          if (detectionCount >= DETECTION_THRESHOLD) {
            stopCapturing();
            showSuccessAnimation(result);
            if (onSuccess) onSuccess(result);
          } else {
            updateStatus(`✅ Face detected (${detectionCount}/${DETECTION_THRESHOLD})...`, 'detected');
          }
        } else {
          detectionCount = 0;
          const statusMap = {
            'no_face': '👤 No face detected. Please look at the camera.',
            'no_match': '❓ Face not recognized. Please try again.',
            'mismatch': '🚫 Face does not match your profile.',
            'no_encoding': '⚠️ No face profile found. Contact admin.',
          };
          updateStatus(statusMap[result.status] || result.message, 'warning');
        }
      } catch (err) {
        console.error('Recognition error:', err);
        updateStatus('⚠️ Connection error. Retrying...', 'error');
      }
    }, 1200);
  }

  function stopCapturing() {
    if (captureInterval) {
      clearInterval(captureInterval);
      captureInterval = null;
    }
    isCapturing = false;
  }

  function showSuccessAnimation(result) {
    const card = elements.resultCard;
    if (!card) return;

    const actionEmoji = result.action === 'entry' ? '🟢' : result.action === 'exit' ? '🟡' : '✅';
    const actionText = result.action === 'entry' ? 'Entry Recorded' : result.action === 'exit' ? 'Exit Recorded' : 'Already Recorded';
    const cardColor = result.action === 'entry' ? '#10b981' : result.action === 'exit' ? '#f59e0b' : '#7c3aed';

    card.style.display = 'block';
    card.style.borderColor = cardColor;
    card.innerHTML = `
      <div class="result-icon" style="color:${cardColor}">${actionEmoji}</div>
      <div class="result-name">${result.student_name}</div>
      <div class="result-action">${actionText}</div>
      <div class="result-time">🕐 ${result.time || ''}</div>
      ${result.confidence ? `<div class="result-confidence">Confidence: ${result.confidence}%</div>` : ''}
      ${result.duration ? `<div class="result-duration">Duration: ${result.duration} min</div>` : ''}
    `;

    card.classList.add('result-animate');
    updateStatus(`✅ ${actionText} for ${result.student_name}`, 'success');

    // Vibrate on success
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
  }

  /* For admin: capture single photo */
  function capturePhoto(callback) {
    const imageData = captureFrame();
    if (imageData && callback) callback(imageData);
    return imageData;
  }

  return { init, startCamera, stopCamera, startCapturing, stopCapturing, capturePhoto, captureFrame, updateStatus };
})();

/* ===== ADMIN FACE CAPTURE (Add Student) ===== */
let adminStream = null;
let capturedPhotoData = null;

async function startAdminCamera() {
  const video = document.getElementById('adminVideo');
  const startBtn = document.getElementById('startCamBtn');
  const captureBtn = document.getElementById('captureBtn');
  if (!video) return;

  try {
    adminStream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = adminStream;
    video.play();
    if (startBtn) startBtn.style.display = 'none';
    if (captureBtn) captureBtn.style.display = 'inline-flex';
    document.getElementById('cameraStatus').textContent = '📷 Camera active. Click "Capture" when ready.';
  } catch {
    document.getElementById('cameraStatus').textContent = '❌ Camera unavailable. Please upload a photo instead.';
  }
}

function captureAdminPhoto() {
  const video = document.getElementById('adminVideo');
  const canvas = document.getElementById('adminCanvas');
  const preview = document.getElementById('photoPreview');
  const input = document.getElementById('faceImageInput');

  if (!video || !canvas) return;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  capturedPhotoData = canvas.toDataURL('image/jpeg', 0.9);

  if (preview) {
    preview.src = capturedPhotoData;
    preview.style.display = 'block';
  }

  if (input) input.value = capturedPhotoData;

  document.getElementById('cameraStatus').textContent = '✅ Photo captured! You can capture again to replace.';
  showToast('Photo captured successfully!', 'success');

  // Stop camera
  if (adminStream) {
    adminStream.getTracks().forEach(t => t.stop());
    adminStream = null;
  }
  const startBtn = document.getElementById('startCamBtn');
  const captureBtn = document.getElementById('captureBtn');
  if (startBtn) startBtn.style.display = 'inline-flex';
  if (startBtn) startBtn.textContent = '🔄 Retake Photo';
  if (captureBtn) captureBtn.style.display = 'none';
}

/* Handle file upload as alternative */
function handleFileUpload(input) {
  const file = input.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    capturedPhotoData = e.target.result;
    const preview = document.getElementById('photoPreview');
    if (preview) {
      preview.src = capturedPhotoData;
      preview.style.display = 'block';
    }
    const faceInput = document.getElementById('faceImageInput');
    if (faceInput) faceInput.value = capturedPhotoData;
    document.getElementById('cameraStatus').textContent = '✅ Photo uploaded!';
    showToast('Photo uploaded successfully!', 'success');
  };
  reader.readAsDataURL(file);
}
