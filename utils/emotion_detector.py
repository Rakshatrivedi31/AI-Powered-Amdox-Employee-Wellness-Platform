import cv2
import numpy as np
import logging
import os
import threading
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
#  DEEPFACE — OPTIONAL, AUTO-WARMUP IN BACKGROUND
# ══════════════════════════════════════════════════════════

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    logger.warning("⚠️ DeepFace not available — camera emotion detection disabled")

_model_warmed  = False
_model_lock    = threading.Lock()
_warmup_thread = None


def _auto_warmup_model():
    global _model_warmed
    if not DEEPFACE_AVAILABLE or _model_warmed:
        return
    with _model_lock:
        if _model_warmed:
            return
        try:
            dummy = np.zeros((224, 224, 3), dtype=np.uint8)
            dummy[50:174, 50:174] = 128
            DeepFace.analyze(
                dummy, actions=['emotion'],
                enforce_detection=False,
                detector_backend='opencv', silent=True,
            )
            _model_warmed = True
        except Exception as e:
            logger.warning(f"Warmup issue (non-fatal): {e}")


if DEEPFACE_AVAILABLE and not _model_warmed:
    _warmup_thread = threading.Thread(target=_auto_warmup_model, daemon=True)
    _warmup_thread.start()

# ══════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════

DEEPFACE_MAP = {
    'happy': 'Happy', 'sad': 'Sad', 'angry': 'Angry',
    'fear': 'Stressed', 'disgust': 'Angry',
    'surprise': 'Happy', 'neutral': 'Neutral',
}

EMOTION_COLORS = {
    'Happy': (0, 255, 0), 'Sad': (255, 0, 0), 'Angry': (0, 0, 255),
    'Stressed': (0, 165, 255), 'Calm': (255, 255, 0),
    'Tired': (128, 0, 128), 'Neutral': (255, 255, 255), 'Energetic': (255, 165, 0),
}

EMOJI = {
    'happy': '😊', 'sad': '😢', 'angry': '😠', 'stressed': '😰',
    'tired': '😴', 'calm': '😌', 'neutral': '😐', 'energetic': '⚡',
}

KEYWORDS = {
    'happy':    ['happy', 'great', 'wonderful', 'amazing', 'joy', 'love', 'excited',
                 'good', 'fantastic', 'awesome', 'delighted', 'pleased', 'cheerful'],
    'sad':      ['sad', 'unhappy', 'depressed', 'down', 'miserable', 'terrible',
                 'crying', 'heartbroken', 'gloomy', 'upset', 'low'],
    'angry':    ['angry', 'mad', 'furious', 'irritated', 'annoyed', 'frustrated',
                 'hate', 'rage', 'outraged', 'livid'],
    'stressed': ['stress', 'stressed', 'overwhelmed', 'pressure', 'anxious',
                 'anxiety', 'nervous', 'worried', 'panic', 'tense', 'burnt out'],
    'tired':    ['tired', 'exhausted', 'sleepy', 'fatigue', 'drained',
                 'weary', 'burnout', 'drowsy', 'no energy'],
    'calm':     ['calm', 'peaceful', 'relaxed', 'tranquil', 'serene',
                 'chill', 'composed', 'stable', 'content'],
    'neutral':  ['okay', 'fine', 'alright', 'normal', 'average', 'decent', 'so-so'],
    'energetic':['energetic', 'pumped', 'motivated', 'charged', 'active',
                 'fired up', 'enthusiastic', 'ready'],
}

# ══════════════════════════════════════════════════════════
#  TEXT DETECTION
# ══════════════════════════════════════════════════════════

def detect_emotion_from_text(text: str):
    """Returns (emotion_str, polarity_float, emoji_str)"""
    if not text or not text.strip():
        return "Neutral", 0.0, "😐"

    try:
        from textblob import TextBlob
        polarity = TextBlob(text).sentiment.polarity
    except Exception:
        polarity = 0.0

    text_lower = text.lower()
    scores = {e: sum(1 for kw in kws if kw in text_lower) for e, kws in KEYWORDS.items()}
    scores = {e: s for e, s in scores.items() if s > 0}

    if scores:
        best = max(scores, key=scores.get)
        return best.capitalize(), polarity, EMOJI.get(best, '😐')

    if polarity > 0.3:  return "Happy",   polarity, "😊"
    if polarity > 0.0:  return "Calm",    polarity, "😌"
    if polarity > -0.3: return "Neutral", polarity, "😐"
    if polarity > -0.6: return "Sad",     polarity, "😢"
    return "Angry", polarity, "😠"

# ══════════════════════════════════════════════════════════
#  STREAMLIT CAMERA DETECTION
# ══════════════════════════════════════════════════════════

class StreamlitEmotionDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def detect_realtime_streamlit(self):
        import streamlit as st

        if not DEEPFACE_AVAILABLE:
            st.error("❌ DeepFace not installed. Run: `pip install deepface tf-keras`")
            return None, None

        if _warmup_thread and _warmup_thread.is_alive():
            with st.spinner("🔥 Loading AI model — first time ~15 seconds..."):
                _warmup_thread.join(timeout=20)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("❌ Camera not accessible! Check permissions.")
            return None, None

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        frame_ph   = st.empty()
        info_ph    = st.empty()
        capture_ph = st.empty()

        # ── Manual capture: user clicks button when ready ──────────
        if 'cam_stop_flag' not in st.session_state:
            st.session_state['cam_stop_flag'] = False

        with capture_ph.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📸 Capture Now", type="primary", key="cam_stop", use_container_width=True):
                    st.session_state['cam_stop_flag'] = True

        st.caption("👆 Position your face clearly, then click **Capture Now**")

        current_emotion = 'Neutral'
        current_conf    = 0
        frame_count     = 0
        best_emotion    = 'Neutral'
        best_conf       = 0
        # No MAX_FRAMES limit — run until user clicks Capture

        try:
            while True:
                # Stop only when user clicks Capture
                if st.session_state.get('cam_stop_flag', False):
                    st.session_state['cam_stop_flag'] = False
                    break

                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.05)
                    continue

                frame_count += 1
                gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

                # DeepFace analysis every 10 frames
                if len(faces) > 0 and frame_count % 10 == 0:
                    try:
                        fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                        pad = 20
                        roi = frame[
                            max(0, fy-pad): min(frame.shape[0], fy+fh+pad),
                            max(0, fx-pad): min(frame.shape[1], fx+fw+pad),
                        ]
                        result = DeepFace.analyze(
                            roi, actions=['emotion'],
                            enforce_detection=False,
                            detector_backend='opencv', silent=True,
                        )
                        if isinstance(result, list): result = result[0]
                        raw             = result['dominant_emotion']
                        current_emotion = DEEPFACE_MAP.get(raw, 'Neutral')
                        current_conf    = int(result['emotion'][raw])
                        if current_conf > best_conf:
                            best_conf    = current_conf
                            best_emotion = current_emotion
                    except Exception:
                        pass

                # Draw face box + label
                for (fx, fy, fw, fh) in faces:
                    color = EMOTION_COLORS.get(current_emotion, (255, 255, 255))
                    cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), color, 3)
                    label = f"{EMOJI.get(current_emotion.lower(), '😐')} {current_emotion} ({current_conf}%)"
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                    cv2.rectangle(frame, (fx, fy-th-12), (fx+tw+10, fy-4), color, -1)
                    cv2.putText(frame, label, (fx+5, fy-8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

                if len(faces) == 0:
                    cv2.putText(frame, "No face — look directly at camera",
                                (10, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 120, 255), 2)

                # Instruction overlay — no countdown
                cv2.putText(frame, "Click 'Capture Now' when ready",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                frame_ph.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB")

                if current_conf > 0:
                    info_ph.info(
                        f"🎭 **Live:** {EMOJI.get(current_emotion.lower(), '😐')} "
                        f"**{current_emotion}** — Confidence: **{current_conf}%** — click Capture when satisfied!"
                    )

                time.sleep(0.033)

        finally:
            cap.release()
            cv2.destroyAllWindows()

        # Return best confidence result
        final_emotion = best_emotion if best_conf > 0 else current_emotion
        final_conf    = best_conf    if best_conf > 0 else current_conf
        return (final_emotion, float(final_conf)) if final_conf > 0 else ('Neutral', 0.0)


def detect_emotion_from_camera_streamlit():
    return StreamlitEmotionDetector().detect_realtime_streamlit()

# ══════════════════════════════════════════════════════════
#  SPEECH RECOGNITION
# ══════════════════════════════════════════════════════════

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False


def detect_emotion_from_speech():
    """Returns (emotion, polarity, emoji, text_or_error)"""
    if not SPEECH_AVAILABLE:
        return (None, 0, "😐",
                "SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return None, 0, "😐", "Timeout — no speech detected."

        try:
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return None, 0, "😐", "Could not understand. Please speak clearly."
        except sr.RequestError as e:
            return None, 0, "😐", f"Speech service error: {e}"

        emotion, polarity, emoji = detect_emotion_from_text(text)
        return emotion, polarity, emoji, text

    except Exception as e:
        return None, 0, "😐", f"Microphone error: {e}"


# ══════════════════════════════════════════════════════════
#  MANUAL MOOD ENTRY (STREAMLIT)
# ══════════════════════════════════════════════════════════

def manual_mood_entry_streamlit():
    import streamlit as st
    moods = [
        ('😊', 'Happy'), ('😌', 'Calm'), ('😐', 'Neutral'), ('😢', 'Sad'),
        ('😰', 'Stressed'), ('😠', 'Angry'), ('😴', 'Tired'), ('⚡', 'Energetic'),
    ]
    cols = st.columns(4)
    selected = None
    for i, (emoji, mood) in enumerate(moods):
        with cols[i % 4]:
            if st.button(f"{emoji}\n{mood}", key=f"mood_btn_{mood}"):
                selected = mood
    return selected


# ══════════════════════════════════════════════════════════
#  STRESS CALCULATOR
# ══════════════════════════════════════════════════════════

def calculate_stress_level(emotion: str, workload: int, recent: list) -> float:
    base = {
        'Happy': 2, 'Energetic': 3, 'Calm': 3, 'Neutral': 4,
        'Tired': 6, 'Sad': 7, 'Stressed': 8, 'Angry': 8,
    }.get(emotion, 5)

    neg_count = sum(1 for m in recent[-3:] if m in {'Stressed', 'Sad', 'Angry', 'Tired'})
    raw = base + (workload * 0.3) + (neg_count * 0.8)
    return round(min(raw, 10.0), 1)