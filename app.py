import streamlit as st
import cv2
import os
import pygame
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Shoulder Surfing Detector",
    page_icon="🛡️",
    layout="wide"
)

# =========================================================
# FACE DETECTOR (Haar Cascade) - loaded once
# =========================================================
if "face_cascade" not in st.session_state:
    st.session_state.face_cascade = cv2.CascadeClassifier(
        "haarcascade_frontalface_default.xml"
    )

face_cascade = st.session_state.face_cascade

# =========================================================
# PYGAME ALARM SETUP - initialized ONCE per session
# =========================================================
ALARM_FILE = "alert.wav"

if "pygame_ready" not in st.session_state:
    pygame.mixer.init()
    st.session_state.pygame_ready = True

if "alarm_sound" not in st.session_state:
    if os.path.exists(ALARM_FILE):
        st.session_state.alarm_sound = pygame.mixer.Sound(ALARM_FILE)
    else:
        st.session_state.alarm_sound = None

if "alarm_channel" not in st.session_state:
    st.session_state.alarm_channel = None

if "alarm_playing" not in st.session_state:
    st.session_state.alarm_playing = False


def start_alarm():
    """Play alarm continuously. Prevents overlapping / repeated play() calls."""
    if st.session_state.alarm_sound is not None and not st.session_state.alarm_playing:
        st.session_state.alarm_channel = st.session_state.alarm_sound.play(loops=-1)
        st.session_state.alarm_playing = True


def stop_alarm():
    """Stop alarm immediately if it is playing."""
    if st.session_state.alarm_playing:
        if st.session_state.alarm_channel is not None:
            st.session_state.alarm_channel.stop()
        st.session_state.alarm_channel = None
        st.session_state.alarm_playing = False


# =========================================================
# ACTIVITY LOG STATE
# =========================================================
if "activity_log" not in st.session_state:
    st.session_state.activity_log = []


def add_log(message):
    """Newest entry on top, capped at 15 entries."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.activity_log.insert(0, (timestamp, message))
    st.session_state.activity_log = st.session_state.activity_log[:15]


# =========================================================
# GLOBAL CSS - Premium Cybersecurity Dashboard Theme
# =========================================================
BASE_CSS = """
<style>

@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #050816 0%, #0F172A 45%, #111827 100%);
    background-attachment: fixed;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ---------- Animated Gradient Title ---------- */
.main-title {
    text-align: center;
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 44px;
    letter-spacing: 2px;
    background: linear-gradient(90deg, #00E5FF, #8B5CF6, #00FFD1, #00E5FF);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientMove 6s ease infinite, titleGlow 2.5s ease-in-out infinite;
    margin-bottom: 0px;
    padding-top: 10px;
}

@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes titleGlow {
    0%, 100% { filter: drop-shadow(0 0 8px rgba(0,229,255,0.5)); }
    50% { filter: drop-shadow(0 0 22px rgba(139,92,246,0.85)); }
}

.sub-title {
    text-align: center;
    color: #94A3B8;
    font-size: 16px;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
    margin-bottom: 28px;
}

/* ---------- Section Headers ---------- */
.section-header {
    font-family: 'Orbitron', sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: #00E5FF;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
    text-shadow: 0 0 12px rgba(0,229,255,0.4);
}

/* ---------- Camera Card (single persistent container, targeted by key) ---------- */
/* Streamlit exposes a stable class "st-key-camera_container" for st.container(key="camera_container") */
div.st-key-camera_container {
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 18px;
    margin-bottom: 20px;
    border: 2px solid rgba(0, 229, 255, 0.45);
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.2);
    transition: border-color 0.6s ease, box-shadow 0.6s ease;
}

div[data-testid="stImage"] img {
    border-radius: 14px;
}

@keyframes redPulse {
    0%, 100% {
        border-color: #FF3B5C;
        box-shadow: 0 0 22px rgba(255,59,92,0.55), inset 0 0 25px rgba(255,59,92,0.08);
    }
    50% {
        border-color: #FF7A90;
        box-shadow: 0 0 48px rgba(255,59,92,0.95), inset 0 0 35px rgba(255,59,92,0.18);
    }
}

/* Alert state: appended dynamically, animates the SAME container (no new card created) */
div.st-key-camera_container.camera-alert {
    border-color: #FF3B5C;
    animation: redPulse 1.2s ease-in-out infinite;
}

/* Safe state: smooth transition back to cyan, animation cleared */
div.st-key-camera_container.camera-safe {
    border-color: rgba(0, 229, 255, 0.45);
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.2);
    animation: none;
}

/* ---------- Metric Cards ---------- */
.metric-card {
    background: rgba(17, 24, 39, 0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.35), 0 0 15px rgba(139, 92, 246, 0.08);
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.metric-card:hover {
    transform: scale(1.035);
    border-color: rgba(0, 229, 255, 0.55);
    box-shadow: 0 6px 28px rgba(0,0,0,0.45), 0 0 25px rgba(0, 229, 255, 0.25);
}

.metric-icon {
    font-size: 20px;
    margin-bottom: 4px;
}

.metric-title {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #94A3B8;
    margin-bottom: 6px;
}

.metric-value {
    font-family: 'Orbitron', sans-serif;
    font-size: 21px;
    font-weight: 700;
    color: #E2E8F0;
    letter-spacing: 0.5px;
}

/* ---------- Badges ---------- */
.badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 30px;
    font-family: 'Orbitron', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
}

.badge-green {
    background: rgba(0, 255, 136, 0.12);
    color: #00FF88;
    border: 1px solid #00FF88;
    box-shadow: 0 0 14px rgba(0, 255, 136, 0.55);
}

.badge-red {
    background: rgba(255, 59, 92, 0.12);
    color: #FF3B5C;
    border: 1px solid #FF3B5C;
    box-shadow: 0 0 14px rgba(255, 59, 92, 0.55);
}

.badge-red-flash {
    background: rgba(255, 59, 92, 0.18);
    color: #FF3B5C;
    border: 1px solid #FF3B5C;
    box-shadow: 0 0 18px rgba(255, 59, 92, 0.75);
    animation: flashAlarm 1s ease-in-out infinite;
}

@keyframes flashAlarm {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.status-dot {
    height: 11px;
    width: 11px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
    vertical-align: middle;
}

.dot-green {
    background-color: #00FF88;
    box-shadow: 0 0 10px #00FF88, 0 0 20px #00FF88;
}

.dot-red {
    background-color: #FF3B5C;
    box-shadow: 0 0 10px #FF3B5C, 0 0 20px #FF3B5C;
}

/* ---------- Status Banner ---------- */
.status-banner {
    border-radius: 16px;
    padding: 14px 20px;
    font-family: 'Orbitron', sans-serif;
    font-weight: 700;
    font-size: 16px;
    letter-spacing: 1px;
    text-align: center;
    margin-bottom: 18px;
    backdrop-filter: blur(14px);
}

.banner-secure {
    background: rgba(0, 255, 136, 0.08);
    border: 1.5px solid #00FF88;
    color: #00FF88;
    box-shadow: 0 0 22px rgba(0, 255, 136, 0.35);
}

.banner-alert {
    background: rgba(255, 59, 92, 0.1);
    border: 1.5px solid #FF3B5C;
    color: #FF3B5C;
    box-shadow: 0 0 28px rgba(255, 59, 92, 0.5);
    animation: flashAlarm 1s ease-in-out infinite;
}

.banner-idle {
    background: rgba(148, 163, 184, 0.06);
    border: 1.5px solid #334155;
    color: #94A3B8;
}

/* ---------- Activity Log ---------- */
.log-card {
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 20px;
    padding: 16px 20px;
    margin-top: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.35);
    max-height: 260px;
    overflow-y: auto;
}

.log-entry {
    font-size: 14px;
    color: #CBD5E1;
    padding: 6px 0;
    border-bottom: 1px solid rgba(148,163,184,0.12);
}

.log-entry:last-child {
    border-bottom: none;
}

.log-time {
    color: #00E5FF;
    font-weight: 600;
    margin-right: 8px;
}

/* ---------- Buttons ---------- */
.stButton > button {
    background: linear-gradient(90deg, #00E5FF, #8B5CF6);
    color: #050816;
    font-weight: 700;
    font-family: 'Orbitron', sans-serif;
    letter-spacing: 1px;
    border: none;
    border-radius: 12px;
    padding: 10px 26px;
    box-shadow: 0 0 18px rgba(0, 229, 255, 0.35);
    transition: all 0.25s ease;
}

.stButton > button:hover {
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 0 28px rgba(139, 92, 246, 0.6);
    color: #050816;
}

.stButton > button:active {
    transform: translateY(0px) scale(0.98);
}

</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)


def set_camera_card_state(state):
    """
    Toggle the SAME camera container between 'safe' and 'alert' visual states
    by injecting a tiny state-marker <style> block that appends a class rule.
    This is only called when the state actually CHANGES, so the CSS pulse
    animation runs continuously and smoothly instead of restarting every frame.
    """
    if state == "alert":
        st.markdown(
            """
            <style>
            div.st-key-camera_container {
                border-color: #FF3B5C !important;
                animation: redPulse 1.2s ease-in-out infinite !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <style>
            div.st-key-camera_container {
                border-color: rgba(0, 229, 255, 0.45) !important;
                box-shadow: 0 0 25px rgba(0, 229, 255, 0.2) !important;
                animation: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# HEADER
# =========================================================
st.markdown("<div class='main-title'>🛡️ Shoulder Surfing Detector</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Real-Time Computer Vision Security Dashboard</div>", unsafe_allow_html=True)

if st.session_state.alarm_sound is None:
    st.warning("⚠️ 'alert.wav' not found in the app directory. Alarm sound will be disabled until the file is added.")

# =========================================================
# LAYOUT
# =========================================================
left, right = st.columns([2, 1])

with left:
    st.markdown("<div class='section-header'>📷 LIVE CAMERA FEED</div>", unsafe_allow_html=True)
    start = st.button("▶  Start Camera")

    # ONE persistent, keyed container. Streamlit keeps this same DOM element
    # across reruns — we only ever change its CSS classes/colors, never
    # recreate it, so the border/glow animates smoothly in place.
    camera_container = st.container(key="camera_container")
    with camera_container:
        frame_placeholder = st.empty()

    # Style placeholder used to hold the current state's CSS injection.
    camera_style_placeholder = st.empty()

    if not start:
        with camera_style_placeholder:
            set_camera_card_state("safe")
        frame_placeholder.markdown(
            "<div style='text-align:center; padding:90px 20px; color:#64748B; "
            "font-family:Orbitron,sans-serif; letter-spacing:1px;'>"
            "⏳ Awaiting camera start...</div>",
            unsafe_allow_html=True
        )

with right:
    st.markdown("<div class='section-header'>📊 SYSTEM STATUS</div>", unsafe_allow_html=True)

    status_placeholder = st.empty()

    col_a, col_b = st.columns(2)

    with col_a:
        faces_placeholder = st.empty()
        threat_placeholder = st.empty()
        camera_placeholder = st.empty()

    with col_b:
        alarm_placeholder = st.empty()
        time_placeholder = st.empty()
        st.empty()


# =========================================================
# HELPER RENDERERS (UI ONLY)
# =========================================================
def render_metric_card(placeholder, icon, title, value_html):
    placeholder.markdown(
        f"""<div class='metric-card'>
            <div class='metric-icon'>{icon}</div>
            <div class='metric-title'>{title}</div>
            <div class='metric-value'>{value_html}</div>
        </div>""",
        unsafe_allow_html=True
    )


def render_idle_dashboard():
    render_metric_card(faces_placeholder, "👤", "Faces Detected", "0")
    render_metric_card(threat_placeholder, "⚠️", "Threat Level", "<span class='badge badge-green'>LOW</span>")
    render_metric_card(alarm_placeholder, "🔔", "Alarm Status", "<span class='badge badge-green'>OFF</span>")
    render_metric_card(camera_placeholder, "📷", "Camera Status", "<span class='status-dot dot-red'></span>Offline")
    render_metric_card(time_placeholder, "🕒", "Current Time", datetime.now().strftime("%H:%M:%S"))
    status_placeholder.markdown(
        "<div class='status-banner banner-idle'>🛡️ SYSTEM IDLE — CAMERA NOT STARTED</div>",
        unsafe_allow_html=True
    )


def render_activity_log():
    if not st.session_state.activity_log:
        entries_html = "<div class='log-entry'>No activity recorded yet.</div>"
    else:
        entries_html = "".join(
            f"<div class='log-entry'><span class='log-time'>[{t}]</span>{msg}</div>"
            for t, msg in st.session_state.activity_log
        )
    log_placeholder.markdown(f"<div class='log-card'>{entries_html}</div>", unsafe_allow_html=True)


if not start:
    render_idle_dashboard()

# =========================================================
# ACTIVITY LOG SECTION
# =========================================================
st.markdown("<div class='section-header' style='margin-top:6px;'>🗂️ ACTIVITY LOG</div>", unsafe_allow_html=True)
log_placeholder = st.empty()
render_activity_log()

# =========================================================
# CAMERA LOOP
# =========================================================
if start:

    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        st.error("Camera not found")
        stop_alarm()

    else:
        last_state = None          # tracks "secure" / "alert" for activity log de-duplication
        last_camera_state = None   # tracks camera card visual state to avoid restarting the pulse animation

        try:
            while True:

                success, frame = cap.read()

                if not success:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5
                )

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                frame_placeholder.image(
                    rgb,
                    channels="RGB",
                    use_container_width=False
                )

                render_metric_card(
                    camera_placeholder,
                    "📷", "Camera Status",
                    "<span class='status-dot dot-green'></span>Online"
                )

                render_metric_card(
                    faces_placeholder,
                    "👤", "Faces Detected",
                    str(len(faces))
                )

                if len(faces) > 1:

                    # Only touch the camera card's visual state on a TRANSITION,
                    # so the red pulse animation runs continuously without restarting.
                    if last_camera_state != "alert":
                        with camera_style_placeholder:
                            set_camera_card_state("alert")
                        last_camera_state = "alert"

                    status_placeholder.markdown(
                        "<div class='status-banner banner-alert'>🚨 SHOULDER SURFING DETECTED</div>",
                        unsafe_allow_html=True
                    )

                    render_metric_card(
                        threat_placeholder,
                        "⚠️", "Threat Level",
                        "<span class='badge badge-red'>HIGH</span>"
                    )

                    render_metric_card(
                        alarm_placeholder,
                        "🔔", "Alarm Status",
                        "<span class='badge badge-red-flash'>🔴 ON</span>"
                    )

                    start_alarm()

                    if last_state != "alert":
                        add_log("🚨 Shoulder surfing detected — alarm triggered")
                        last_state = "alert"

                else:

                    if last_camera_state != "safe":
                        with camera_style_placeholder:
                            set_camera_card_state("safe")
                        last_camera_state = "safe"

                    status_placeholder.markdown(
                        "<div class='status-banner banner-secure'>🟢 SYSTEM SECURE</div>",
                        unsafe_allow_html=True
                    )

                    render_metric_card(
                        threat_placeholder,
                        "⚠️", "Threat Level",
                        "<span class='badge badge-green'>LOW</span>"
                    )

                    render_metric_card(
                        alarm_placeholder,
                        "🔔", "Alarm Status",
                        "<span class='badge badge-green'>OFF</span>"
                    )

                    stop_alarm()

                    if last_state != "secure":
                        add_log("🟢 System secure — no threat detected")
                        last_state = "secure"

                render_metric_card(
                    time_placeholder,
                    "🕒", "Current Time",
                    datetime.now().strftime("%H:%M:%S")
                )

                render_activity_log()

        finally:
            cap.release()
            stop_alarm()