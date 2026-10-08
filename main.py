import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import math
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

scroll_sensitivity = 3
sensitivity = 3
scroll_small_movement = 3
small_movement = 1
ti_tap_threshold = 0.3
tm_tap_threshold = 0.5
hand_detection_confidence=0.5
tracking_confidence=0.01

mode = 0
# 0 - scroll
# 1 - mouse
# 2 - zoom

def distance(a,b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def midpt(a,b):
    return ((a[0]+b[0])//2,(a[1]+b[1])//2)

def zoom(a):
    if a > 15:
        pyautogui.hotkey('ctrl', '+')
    elif a < -15:
        pyautogui.hotkey('ctrl', '-')

prev_state = False
def hold_mouse(state):
    global prev_state
    if state == prev_state:
        pass
    elif state:
        pyautogui.mouseDown()
    else:
        pyautogui.mouseUp()
    prev_state = state

def toggle_mode():
    global mode
    mode += 1
    if mode > 2:
        mode = 0

vid = cv2.VideoCapture(0)
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options,running_mode=vision.RunningMode.VIDEO,num_hands=1,min_hand_detection_confidence=hand_detection_confidence,min_tracking_confidence=tracking_confidence)
detector = vision.HandLandmarker.create_from_options(options)

ti_ratio = 0
im_ratio = 0
tm_ratio = 0
ti_mid = (0,0)

cv2.namedWindow("vid", cv2.WINDOW_NORMAL)

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
            middlel = landmarks[12]
            palm_pinky = landmarks[17]
            palm_bottom = landmarks[0]

            refrencedist = distance(palm_bottom,palm_pinky)

            # ti -> thumb-index
            del_ti_mid = ((midpt(thumbl,indexl)[0] - ti_mid[0]),(midpt(thumbl,indexl)[1] - ti_mid[1]))
            ti_mid = midpt(thumbl,indexl)
            ti_fingerdist = distance(thumbl,indexl)
            del_ti_ratio = (ti_fingerdist/refrencedist) - ti_ratio
            ti_ratio = ti_fingerdist/refrencedist
            ti_contact = ti_ratio < ti_tap_threshold    

            if mode == 0:
                if ti_contact:
                    if abs(del_ti_mid[1]) > scroll_small_movement:
                        pyautogui.scroll(int(del_ti_mid[1]*scroll_sensitivity))
            elif mode == 1:
                # tm -> thumb-middle
                tm_mid = midpt(thumbl,middlel)
                tm_fingerdist = distance(thumbl,middlel)
                del_tm_ratio = ((tm_fingerdist/refrencedist) - tm_ratio)*100
                tm_ratio = tm_fingerdist/refrencedist
                tm_contact = tm_ratio < tm_tap_threshold

                cv2.circle(frame, tm_mid, 7, (255,255*(not tm_contact),255*tm_contact), cv2.FILLED)
                
                cv2.line(frame, (100,200),(100+int(del_ti_mid[0]),200),(0,255,0),10)
                cv2.line(frame, (100,250),(100+int(del_ti_mid[1]),250),(0,255,0),10)
                if abs(del_ti_mid[0]) > small_movement and abs(del_ti_mid[1]) > small_movement:
                    if not tm_contact:
                        pyautogui.moveRel((del_ti_mid[0]*sensitivity,del_ti_mid[1]*sensitivity))
                    hold_mouse(ti_contact)
            elif mode == 2:
                # im -> index-middle
                im_fingerdist = distance(indexl,middlel)
                del_im_ratio = ((im_fingerdist/refrencedist) - im_ratio)*100
                im_ratio = im_fingerdist/refrencedist

                cv2.line(frame, (100,200),(100+int(del_im_ratio),200),(0,255,0),10)
                if ti_contact:
                    zoom(del_im_ratio)

            cv2.circle(frame, ti_mid, 7, (255,255*(not ti_contact),255*ti_contact), cv2.FILLED)
            cv2.putText(frame, f"Ratio: {ti_ratio}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Score: {result.handedness[0][0].score}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if mode == 0:
            cv2.putText(frame, "Mode: Scroll", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if mode == 1:
            cv2.putText(frame, "Mode: Mouse", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if mode == 2:
            cv2.putText(frame, "Mode: Zoom", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press P while keeping window in focus to change mode.", (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("vid",frame)
    except Exception as e:
        print(e)
    if cv2.waitKey(1) & 0xff==ord('q'):
        break
    if cv2.waitKey(1) & 0xFF== ord('p'):
        toggle_mode()
        print(mode)

vid.release()
cv2.destroyAllWindows()