import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import math

def distance(a,b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),      # Index
    (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky & Palm base
]

vid = cv2.VideoCapture(0)
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options,running_mode=vision.RunningMode.VIDEO,num_hands=1,min_hand_detection_confidence=0.9,min_tracking_confidence=0.9)
detector = vision.HandLandmarker.create_from_options(options)

last_contact_time = None
last_release_time = None

while vid.isOpened():
    try:
        res,frame = vid.read()
        h, w, _ = frame.shape
        rgbimg = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        mpimg = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgbimg)

        frame_timestamp_ms = int(time.time() * 1000)
        result = detector.detect_for_video(mpimg, frame_timestamp_ms)
        if result.hand_landmarks:
            landmarks = {}
            for idx,landmark in enumerate(result.hand_landmarks[0]):
                x = int(landmark.x*w)
                y = int(landmark.y*h)
                landmarks[idx] = (x,y)
                cv2.circle(frame, (x, y), 5, (0, 255, 0), cv2.FILLED)

            thumbl = landmarks[4]
            indexl = landmarks[8]
            palm_pinky = landmarks[17]
            palm_bottom = landmarks[0]

            fingerdist = distance(thumbl,indexl)
            refrencedist = distance(palm_bottom,palm_pinky)

            ratio = fingerdist/refrencedist
            if ratio < 0.3:
                ti_contact = True    # thumb-index contact
            else:
                ti_contact = False
            # print(ratio)
        # print(result.handedness[0][0].score)
            cv2.putText(frame, f" Ratio: {ratio}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Score: {result.handedness[0][0].score}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f" Contact: {ti_contact}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("vid",frame)
    except Exception as e:
        print(e)
    if cv2.waitKey(1) & 0xff==ord('q'):
        break
vid.release()
cv2.destroyAllWindows()