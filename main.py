import cv2
import pygame
import time
from datetime import datetime

# Initialize sound system
pygame.mixer.init()

# Load alarm sound
sound = pygame.mixer.Sound("alert.wav")

# Load face detection model
faceCascade = cv2.CascadeClassifier(
    'haarcascade_frontalface_default.xml'
)

# Open webcam
cam = cv2.VideoCapture(0)

# Alarm cooldown timer
last_detection_time = 0

# Stable detection counter
detection_counter = 0

while True:

    # Read webcam frame
    success, frame = cam.read()

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5
    )

    # Draw rectangles around faces
    for (x, y, w, h) in faces:

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

    # =========================
    # SECURITY LOGIC
    # =========================

    # Count stable detections 
    
    if len(faces) > 1:
        detection_counter += 1

    else:
        detection_counter = 0

    # Trigger alert only after stable detection
    if detection_counter >= 15:

        with open("log.txt", "a") as file:
            file.write(
                f"Intrusion detected at {datetime.now()}\n"
            )

        # Save logs
        with open("log.txt", "a") as file:
            file.write(
                f"Intrusion detected at {datetime.now()}\n"
        )

        # Blur screen

        cv2.imwrite("intruder.jpg", frame)

        # Blur screen
        frame = cv2.GaussianBlur(frame, (35, 35), 0)

        # Alarm cooldown logic
        current_time = time.time()

        if current_time - last_detection_time > 3:
            sound.play()
            last_detection_time = current_time

        # Warning text
        cv2.putText(
            frame,
            "WARNING: SHOULDER SURFING DETECTED",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        # Threat level
        cv2.putText(
            frame,
            "THREAT LEVEL: HIGH",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        # Red border
        cv2.rectangle(
            frame,
            (0, 0),
            (frame.shape[1], frame.shape[0]),
            (0, 0, 255),
            10
        )

    else:

        # Safe text
        cv2.putText(
            frame,
            "SYSTEM SECURE",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        # Threat level low
        cv2.putText(
            frame,
            "THREAT LEVEL: LOW",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.putText(
        frame,
        f"Faces Detected: {len(faces)}",
        (20, 170),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    # Show webcam
    cv2.imshow(
        "Shoulder Surfing Detector",
        frame
    )

    # Exit on ESC
    if cv2.waitKey(1) == 27:
        break

# Release resources
cam.release()
cv2.destroyAllWindows()