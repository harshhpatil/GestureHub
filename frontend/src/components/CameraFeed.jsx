import { useEffect, useRef, useState } from 'react';

const GESTURE_LABELS = {
  THUMBS_UP: '👍 Thumbs Up',
  THUMBS_DOWN: '👎 Thumbs Down',
  PEACE: '✌️ Peace',
  OPEN_PALM: '🖐️ Open Palm',
  FIST: '✊ Fist',
  INDEX: '☝️ Index',
  ROCK: '🤘 Rock',
  TWO_FINGERS: '✌️ Two Fingers',
  NONE: 'No Gesture',
};

/**
 * Detects hand gestures using MediaPipe Hands.
 * Falls back to mock detection if MediaPipe is unavailable.
 */
function classifyHandLandmarks(landmarks) {
  if (!landmarks || landmarks.length === 0) return 'NONE';

  const tips = [4, 8, 12, 16, 20];
  const pips = [3, 6, 10, 14, 18];

  const extended = tips.map((tip, i) => {
    if (i === 0) {
      // Thumb: compare x distance
      return Math.abs(landmarks[tip].x - landmarks[tips[1]].x) > 0.08;
    }
    return landmarks[tip].y < landmarks[pips[i]].y;
  });

  const [thumb, index, middle, ring, pinky] = extended;
  const fingerCount = extended.slice(1).filter(Boolean).length;

  if (thumb && !index && !middle && !ring && !pinky) return 'THUMBS_UP';
  if (!thumb && !index && !middle && !ring && !pinky) return 'FIST';
  if (thumb && index && middle && ring && pinky) return 'OPEN_PALM';
  if (!thumb && index && middle && !ring && !pinky) return 'PEACE';
  if (!thumb && index && !middle && !ring && pinky) return 'ROCK';
  if (!thumb && index && !middle && !ring && !pinky) return 'INDEX';
  if (!thumb && index && middle && !ring && !pinky) return 'TWO_FINGERS';
  if (!thumb && !index && !middle && !ring && !pinky) {
    // Check wrist vs tip direction for thumbs down
    if (landmarks[4].y > landmarks[8].y) return 'THUMBS_DOWN';
  }

  return 'NONE';
}

export default function CameraFeed({ onGesture, sensitivity = 0.7 }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const handsRef = useRef(null);
  const cameraRef = useRef(null);
  const animFrameRef = useRef(null);

  const [handDetected, setHandDetected] = useState(false);
  const [currentGesture, setCurrentGesture] = useState('NONE');
  const [fps, setFps] = useState(0);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const fpsCounterRef = useRef({ frames: 0, lastTime: Date.now() });

  useEffect(() => {
    let active = true;

    async function init() {
      setLoading(true);
      setError(null);

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: 'user' },
        });

        if (!active) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        const video = videoRef.current;
        if (!video) return;
        video.srcObject = stream;
        await video.play();

        // Try to load MediaPipe Hands
        const mpLoaded = await loadMediaPipe(video, active);
        if (!mpLoaded && active) {
          // Fallback: manual frame capture
          startFallbackDetection(video, active);
        }
      } catch (err) {
        if (active) setError(err.message || 'Camera access denied');
      } finally {
        if (active) setLoading(false);
      }
    }

    async function loadMediaPipe(video, active) {
      try {
        const { Hands } = await import('@mediapipe/hands');
        const { Camera } = await import('@mediapipe/camera_utils');
        const { drawConnectors, drawLandmarks } = await import('@mediapipe/drawing_utils');

        const hands = new Hands({
          locateFile: (file) =>
            `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
        });

        hands.setOptions({
          maxNumHands: 1,
          modelComplexity: 1,
          minDetectionConfidence: sensitivity,
          minTrackingConfidence: 0.5,
        });

        hands.onResults((results) => {
          if (!active) return;
          const canvas = canvasRef.current;
          if (!canvas) return;

          const ctx = canvas.getContext('2d');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.clearRect(0, 0, canvas.width, canvas.height);

          const detected = results.multiHandLandmarks?.length > 0;
          setHandDetected(detected);

          if (detected) {
            const landmarks = results.multiHandLandmarks[0];

            // Draw skeleton
            drawConnectors(ctx, landmarks, Hands.HAND_CONNECTIONS, {
              color: '#00FFCC',
              lineWidth: 2,
            });
            drawLandmarks(ctx, landmarks, { color: '#FF0066', lineWidth: 1, radius: 4 });

            const gesture = classifyHandLandmarks(landmarks);
            setCurrentGesture(gesture);
            onGesture?.(gesture, 1.0);
          } else {
            setCurrentGesture('NONE');
            onGesture?.('NONE', 0);
          }

          // FPS counter
          const counter = fpsCounterRef.current;
          counter.frames++;
          const now = Date.now();
          if (now - counter.lastTime >= 1000) {
            setFps(counter.frames);
            counter.frames = 0;
            counter.lastTime = now;
          }
        });

        handsRef.current = hands;

        const camera = new Camera(video, {
          onFrame: async () => {
            if (active) await hands.send({ image: video });
          },
          width: 640,
          height: 480,
        });
        camera.start();
        cameraRef.current = camera;

        return true;
      } catch (e) {
        console.warn('[CameraFeed] MediaPipe unavailable, using fallback:', e.message);
        return false;
      }
    }

    function startFallbackDetection(video, active) {
      // Without MediaPipe: just show the video and emit NONE
      const canvas = canvasRef.current;
      let lastFpsUpdate = Date.now();
      let frames = 0;

      function tick() {
        if (!active) return;
        const ctx = canvas?.getContext('2d');
        if (ctx && video.readyState >= 2) {
          canvas.width = video.videoWidth || 640;
          canvas.height = video.videoHeight || 480;
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          frames++;
          const now = Date.now();
          if (now - lastFpsUpdate >= 1000) {
            setFps(frames);
            frames = 0;
            lastFpsUpdate = now;
          }
        }
        animFrameRef.current = requestAnimationFrame(tick);
      }
      tick();
    }

    init();

    return () => {
      active = false;
      cancelAnimationFrame(animFrameRef.current);
      cameraRef.current?.stop?.();
      handsRef.current?.close?.();
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach((t) => t.stop());
      }
    };
  }, [sensitivity]);

  return (
    <div className="relative w-full aspect-video bg-dark-800 rounded-xl overflow-hidden border border-gray-700">
      {/* Hidden video element (MediaPipe reads from it) */}
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover opacity-80 scale-x-[-1]"
        playsInline
        muted
      />

      {/* Canvas for landmarks overlay */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full object-cover scale-x-[-1]"
      />

      {/* Loading state */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-dark-900/80">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-400">Starting camera…</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-dark-900/90">
          <div className="text-center px-4">
            <p className="text-red-400 text-lg mb-2">⚠️ Camera Error</p>
            <p className="text-sm text-gray-400">{error}</p>
          </div>
        </div>
      )}

      {/* HUD Overlay */}
      {!loading && !error && (
        <>
          {/* Top bar */}
          <div className="absolute top-0 left-0 right-0 flex justify-between items-center px-3 py-1.5 bg-black/50 text-xs font-mono">
            <span className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${handDetected ? 'bg-accent pulse-accent' : 'bg-gray-600'}`}
              />
              {handDetected ? 'Hand Detected' : 'No Hand'}
            </span>
            <span className="text-gray-400">{fps} FPS</span>
          </div>

          {/* Bottom gesture label */}
          <div className="absolute bottom-0 left-0 right-0 px-3 py-2 bg-black/60 text-center">
            <span className="text-sm font-semibold" style={{ color: handDetected ? '#00FFCC' : '#6b7280' }}>
              {GESTURE_LABELS[currentGesture] || currentGesture}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
