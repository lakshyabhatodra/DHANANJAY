import threading
from datetime import datetime
from pathlib import Path

import av
import cv2
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="DHANANJAY | Security Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
CASCADE_PATH = BASE_DIR / "haarcascade_frontalface_default.xml"
LOG_PATH = BASE_DIR / "log.txt"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root { color-scheme: dark; }
html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp { background: #0b1120; color: #e5eaf2; }
[data-testid="stSidebar"] { background: #0e1728; border-right: 1px solid #263449; }
[data-testid="stHeader"] { background: rgba(11,17,32,.92); }
#MainMenu, footer { visibility: hidden; }
h1,h2,h3 { letter-spacing: -.025em; }
.brand { font-size: 29px; font-weight: 700; letter-spacing: .08em; color: #e8eef8; }
.brand span { color: #43b8c8; }
.eyebrow { color:#8293aa; font: 11px 'JetBrains Mono',monospace; letter-spacing:.16em; text-transform:uppercase; }
.page-title { font-size: 25px; font-weight: 650; color:#edf3fb; margin: 4px 0 2px; }
.page-subtitle { color:#91a0b5; font-size:13px; margin-bottom:20px; }
.card { background:#111d30; border:1px solid #26364c; border-radius:12px; padding:17px 18px; min-height:105px; }
.metric-label { color:#91a0b5; font-size:11px; letter-spacing:.1em; text-transform:uppercase; }
.metric-value { color:#edf3fb; font:600 25px 'JetBrains Mono',monospace; margin-top:9px; }
.metric-note { color:#7f91a9; font-size:11px; margin-top:5px; }
.status-pill { display:inline-block; border-radius:20px; padding:5px 10px; font:11px 'JetBrains Mono',monospace; letter-spacing:.05em; }
.good { color:#5dd6a0; background:#123328; border:1px solid #245b48; }
.bad { color:#ff7b85; background:#3b1d29; border:1px solid #71313f; }
.neutral { color:#a8b8ca; background:#1c2a3d; border:1px solid #34465d; }
.workspace { background:#111d30; border:1px solid #30435a; border-radius:12px; padding:20px; }
.workspace-label { color:#8fa1b8; font:11px 'JetBrains Mono',monospace; letter-spacing:.12em; }
.log-entry { padding:10px 0; border-bottom:1px solid #24334a; color:#c6d2e1; font:12px 'JetBrains Mono',monospace; }
div[data-testid="stButton"] button { border-radius:8px; font-weight:600; min-height:40px; }
div[data-testid="stTabs"] button { font-weight:600; }
small, .stCaption { color:#8fa1b8 !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Session state
defaults = {
    "shared": {
        "lock": threading.Lock(), "faces": 0, "authorized": 0,
        "unauthorized": 0, "threat": False, "last_event": "Waiting for camera",
    },
    "samples": [],
    "recognizer": None,
    "logs": [],
    "alarm_enabled": True,
    "threshold": 75.0,
    "last_logged_state": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

cascade = cv2.CascadeClassifier(str(CASCADE_PATH))
if cascade.empty():
    st.error("Face detector file missing. Keep haarcascade_frontalface_default.xml in the same folder as app.py.")
    st.stop()


def add_log(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{stamp} | {message}"
    if not st.session_state.logs or st.session_state.logs[0] != entry:
        st.session_state.logs.insert(0, entry)
        st.session_state.logs = st.session_state.logs[:100]
    try:
        with LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(entry + "\n")
    except OSError:
        pass


def read_logs():
    try:
        if LOG_PATH.exists():
            return LOG_PATH.read_text(encoding="utf-8").splitlines()[-100:][::-1]
    except OSError:
        pass
    return st.session_state.logs


def create_recognizer():
    if not hasattr(cv2, "face"):
        return None
    return cv2.face.LBPHFaceRecognizer_create()


# Sidebar
with st.sidebar:
    st.markdown('<div class="brand">DHANA<span>NJAY</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">PRIVACY SECURITY CONSOLE</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("**SYSTEM STATUS**")
    with st.session_state.shared["lock"]:
        current_threat = st.session_state.shared["threat"]
    st.markdown(
        '<span class="status-pill bad">● POTENTIAL THREAT</span>' if current_threat
        else '<span class="status-pill good">● SYSTEM STANDBY / SECURE</span>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("**PROJECT MODULES**")
    st.caption("Overview · Registration · Live test · Logs")
    st.divider()
    st.caption("DHANANJAY / PROTOTYPE BUILD")
    st.caption("Computer vision-based privacy protection")

st.markdown(
    '<div class="eyebrow">CYBERSECURITY / COMPUTER VISION</div>'
    '<div class="page-title">Shoulder Surfing Detection System</div>'
    '<div class="page-subtitle">Monitor nearby faces and protect confidential on-screen information.</div>',
    unsafe_allow_html=True,
)

overview_tab, registration_tab, test_tab, logs_tab, settings_tab = st.tabs(
    ["Overview", "Face Registration", "Live Security Test", "Activity Logs", "Settings"]
)

# Overview
with overview_tab:
    st.markdown("### Security overview")
    shared = st.session_state.shared
    with shared["lock"]:
        faces_now = shared["faces"]
        auth_now = shared["authorized"]
        unauth_now = shared["unauthorized"]
        threat_now = shared["threat"]
    monitoring = st.session_state.get("monitoring_active", False)
    profile_ready = st.session_state.recognizer is not None

    cols = st.columns(4)
    metrics = [
        ("FACES DETECTED", faces_now, "Current camera frame"),
        ("AUTHORIZED", auth_now, "Matched registered profile"),
        ("UNRECOGNIZED", unauth_now, "No profile match"),
        ("THREAT STATUS", "HIGH" if threat_now else ("LOW" if monitoring else "IDLE"),
         "Privacy response state"),
    ]
    for col, (label, value, note) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="card"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
                unsafe_allow_html=True,
            )
    st.write("")
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### System readiness")
        st.markdown(
            f'<span class="status-pill {"good" if profile_ready else "neutral"}">'
            f'● FACE PROFILE {"READY" if profile_ready else "NOT REGISTERED"}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<span class="status-pill {"good" if monitoring else "neutral"}">'
            f'● CAMERA {"ACTIVE" if monitoring else "NOT STARTED"}</span>',
            unsafe_allow_html=True,
        )
        st.write("")
        st.info("Register your face first, then open Live Security Test and start the camera.")
    with right:
        st.markdown("#### Detection policy")
        st.write("- Any unrecognized face triggers a potential threat.")
        st.write("- More than one visible face triggers protection.")
        st.write("- Confidential demo content is blurred during a threat.")
    st.markdown("#### Confidential workspace preview")
    if threat_now:
        st.markdown(
            '<div class="workspace"><div class="workspace-label">DEMO BANKING PORTAL / LOCKED</div>'
            '<div style="filter:blur(8px);user-select:none"><h3>Demo User</h3><h2>₹2,45,800</h2>'
            '<p>Account: XXXX XXXX 4821 · Recent transaction: ₹12,500</p></div>'
            '<span class="status-pill bad">CONTENT PROTECTED</span></div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="workspace"><div class="workspace-label">DEMO BANKING PORTAL / PREVIEW</div>'
            '<h3>Demo User</h3><h2>₹2,45,800</h2>'
            '<p>Account: XXXX XXXX 4821 · Recent transaction: ₹12,500</p>'
            '<span class="status-pill good">CONTENT VISIBLE IN DEMO</span></div>', unsafe_allow_html=True
        )

# Registration
with registration_tab:
    st.markdown("### Register authorized user")
    st.write("Capture multiple samples of the same person. Use consistent lighting and vary the angle slightly.")
    st.info("For this prototype, samples are held in the current Streamlit session. They are not persistent biometric enrollment.")
    shot = st.camera_input("Capture face sample", key="registration_camera")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Add sample", use_container_width=True, disabled=shot is None):
            image = cv2.imdecode(np.frombuffer(shot.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            detected = cascade.detectMultiScale(
                gray, scaleFactor=1.08, minNeighbors=5, minSize=(70, 70)
            )
            if len(detected) != 1:
                st.warning("Exactly one face should be visible. Adjust lighting and try again.")
            else:
                x, y, w, h = detected[0]
                face = cv2.resize(gray[y:y+h, x:x+w], (200, 200), interpolation=cv2.INTER_AREA)
                st.session_state.samples.append(face)
                st.success(f"Sample added. Total: {len(st.session_state.samples)}")
                add_log(f"Authorized face sample captured ({len(st.session_state.samples)} total)")
    with c2:
        if st.button(
            "Train face profile", use_container_width=True,
            disabled=len(st.session_state.samples) < 3,
        ):
            recognizer = create_recognizer()
            if recognizer is None:
                st.error("LBPH is unavailable. Install opencv-contrib-python-headless and remove opencv-python.")
            else:
                recognizer.train(
                    st.session_state.samples,
                    np.array([1] * len(st.session_state.samples), dtype=np.int32),
                )
                st.session_state.recognizer = recognizer
                st.success("Authorized profile trained.")
                add_log("Authorized face profile trained")
    with c3:
        if st.button("Clear registration", use_container_width=True):
            st.session_state.samples = []
            st.session_state.recognizer = None
            add_log("Authorized face profile cleared")
            st.rerun()
    st.markdown(f"**Samples collected:** {len(st.session_state.samples)} / recommended 5–8")
    if st.session_state.recognizer is not None:
        st.success("Profile status: READY")
    else:
        st.warning("Profile status: NOT REGISTERED")
    st.caption("Tip: capture 5–8 samples with small changes in head angle and lighting. Avoid extreme pose changes.")

# Live test
with test_tab:
    st.markdown("### Live security test")
    if st.session_state.recognizer is None:
        st.warning("Register and train an authorized face profile before starting the live test.")
    st.write("Allow browser camera permission when prompted. For best results, use good front lighting and keep the face clearly visible.")
    shared = st.session_state.shared
    recognizer_model = st.session_state.recognizer
    threshold = float(st.session_state.threshold)

    class PrivacyProcessor:
        def __init__(self):
            self.face_cascade = cv2.CascadeClassifier(str(CASCADE_PATH))
            self.recognizer = recognizer_model
            self.shared = shared

        def recv(self, frame):
            image = frame.to_ndarray(format="bgr24")
            # Detect on the full-resolution frame; return the original-size frame
            # to avoid making the displayed camera preview look soft.
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.08, minNeighbors=5, minSize=(65, 65)
            )
            authorized_count = 0
            unauthorized_count = 0
            for (x, y, w, h) in faces:
                crop = cv2.resize(
                    gray[y:y+h, x:x+w], (200, 200), interpolation=cv2.INTER_AREA
                )
                matched = False
                if self.recognizer is not None:
                    label, confidence = self.recognizer.predict(crop)
                    matched = label == 1 and confidence < threshold
                if matched:
                    authorized_count += 1
                    color, tag = (55, 205, 145), "AUTHORIZED"
                else:
                    unauthorized_count += 1
                    color, tag = (70, 85, 245), "UNRECOGNIZED"
                cv2.rectangle(image, (x, y), (x+w, y+h), color, 2)
                cv2.putText(
                    image, tag, (x, max(24, y-9)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, color, 2, cv2.LINE_AA
                )

            threat = unauthorized_count > 0 or len(faces) > 1
            with self.shared["lock"]:
                self.shared["faces"] = len(faces)
                self.shared["authorized"] = authorized_count
                self.shared["unauthorized"] = unauthorized_count
                self.shared["threat"] = threat
                self.shared["last_event"] = "Potential privacy threat" if threat else "System secure"
            if threat:
                cv2.rectangle(image, (0, 0), (image.shape[1], 42), (35, 35, 90), -1)
                cv2.putText(
                    image, "PRIVACY THREAT - CONTENT PROTECTED", (14, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (90, 100, 255), 2, cv2.LINE_AA
                )
            return av.VideoFrame.from_ndarray(image, format="bgr24")

    rtc_config = RTCConfiguration({
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    })
    webrtc_ctx = webrtc_streamer(
        key="dhananjay-security-camera-v2",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=rtc_config,
        video_processor_factory=PrivacyProcessor,
        # Ask the browser for HD video; actual resolution depends on camera/browser.
        media_stream_constraints={
            "video": {
                "width": {"ideal": 1280},
                "height": {"ideal": 720},
                "frameRate": {"ideal": 24, "max": 30},
            },
            "audio": False,
        },
        async_processing=True,
    )
    st.session_state.monitoring_active = bool(webrtc_ctx.state.playing)
    if not st.session_state.monitoring_active:
        st.caption("Camera is stopped. Press START to begin the test.")
    else:
        st.caption("HD is requested from the browser camera. Camera hardware and browser negotiation determine the actual resolution.")

    st_autorefresh(interval=1200, key="security_dashboard_refresh")
    with shared["lock"]:
        threat_now = shared["threat"]
        faces_now = shared["faces"]
        auth_now = shared["authorized"]
        unauth_now = shared["unauthorized"]

    a, b, c, d = st.columns(4)
    for col, label, value in [
        (a, "FACES", faces_now), (b, "AUTHORIZED", auth_now),
        (c, "UNRECOGNIZED", unauth_now),
        (d, "THREAT", "HIGH" if threat_now else ("LOW" if webrtc_ctx.state.playing else "IDLE")),
    ]:
        with col:
            st.metric(label, value)

    if threat_now:
        st.error("Potential shoulder surfing detected. Confidential content is protected.")
        if st.session_state.alarm_enabled:
            components.html(
                """
                <script>
                (() => {
                  try {
                    const C = window.AudioContext || window.webkitAudioContext;
                    const ctx = new C();
                    if (ctx.state === 'suspended') ctx.resume();
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'square'; osc.frequency.value = 880;
                    gain.gain.value = 0.045;
                    osc.connect(gain); gain.connect(ctx.destination);
                    osc.start(); osc.stop(ctx.currentTime + 0.35);
                  } catch (e) {}
                })();
                </script>
                """,
                height=0,
            )
    elif webrtc_ctx.state.playing:
        st.success("No potential threat detected. Confidential demo content is visible.")
    else:
        st.info("Start the camera to begin monitoring.")

    st.markdown("#### Confidential workspace")
    if threat_now:
        st.markdown(
            '<div class="workspace"><div class="workspace-label">DEMO BANKING PORTAL</div>'
            '<div style="filter:blur(9px);user-select:none;pointer-events:none">'
            '<h3>Account holder: Demo User</h3><h2>₹2,45,800</h2>'
            '<p>Account number: XXXX XXXX 4821</p><p>Recent transaction: ₹12,500</p></div>'
            '<span class="status-pill bad">UNAUTHORIZED VIEW RISK — CONTENT BLURRED</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="workspace"><div class="workspace-label">DEMO BANKING PORTAL</div>'
            '<h3>Account holder: Demo User</h3><h2>₹2,45,800</h2>'
            '<p>Account number: XXXX XXXX 4821</p><p>Recent transaction: ₹12,500</p>'
            '<span class="status-pill good">AUTHORIZED VIEW — CONTENT VISIBLE</span></div>',
            unsafe_allow_html=True,
        )

# Logs
with logs_tab:
    st.markdown("### Detection and system activity")
    entries = read_logs()
    if entries:
        for entry in entries[:50]:
            st.markdown(f'<div class="log-entry">{entry}</div>', unsafe_allow_html=True)
    else:
        st.info("No activity has been recorded yet.")
    if st.button("Refresh logs"):
        st.rerun()

# Settings
with settings_tab:
    st.markdown("### Detection settings")
    st.session_state.alarm_enabled = st.toggle("Enable browser alert tone", value=st.session_state.alarm_enabled)
    st.session_state.threshold = st.slider(
        "LBPH match threshold (lower is stricter)",
        min_value=40.0, max_value=100.0, value=float(st.session_state.threshold), step=1.0,
        help="This is a prototype tuning value. Lower values require a closer image match.",
    )
    st.caption("Recommended starting point: 75. A lower threshold may reject the registered user; a higher threshold may accept an unknown face.")
    st.warning("LBPH is a basic demonstration recognizer, not secure biometric authentication. Do not use this prototype to protect real banking or sensitive data.")
    st.caption("Camera resolution is requested as 1280×720. The browser and webcam may negotiate a different resolution.")
