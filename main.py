import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import pyautogui
import time
import os
import subprocess
from collections import deque
import pygetwindow as gw
import win32gui 
import win32con

pyautogui.FAILSAFE = False 

# ── Model ──────────────────────────────────────────────────────────────────────
model_path = os.path.join(os.path.dirname(__file__), "models/gesture_recognizer.task")
if not os.path.exists(model_path):
    print("❌ Model not found. Run: python setup_models.py")
    exit(1)

# ── GestureRecognizer ──────────────────────────────────────────────────────────
base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
options = vision.GestureRecognizerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.65,
    min_hand_presence_confidence=0.65,
    min_tracking_confidence=0.55,
)
recognizer = vision.GestureRecognizer.create_from_options(options)

# ══════════════════════════════════════════════════════════════════════════════
#  APP LAUNCHER CONFIG — Updated (Replaces the old APP_PATHS & launch_app)
# ══════════════════════════════════════════════════════════════════════════════
import getpass
import os 
WIN_USER = getpass.getuser()

APP_PATHS = {
    # Plain paths. No extra inner quotes needed for os.startfile!
    "chrome":     r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Google Chrome.lnk",
    "whatsapp":   "whatsapp:", # Deep-link protocol for MS Store WhatsApp
    "vscode":     rf"C:\Users\{WIN_USER}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "notepad":    "notepad.exe",
    "explorer":   "explorer.exe",
    "calculator": "calc.exe",
}

def launch_app(key):
    path = APP_PATHS.get(key, "")
    if not path:
        return
    try:
     
        os.startfile(path)
        print(f"✓ Successfully launched {key}")
    except Exception as e:
        print(f"✗ Could not launch {key}. Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  MODES
#  PRESENTATION MODE  → controls Google Slides
#  LAUNCHER MODE      → opens apps
#
#  Switch modes with ILoveYou gesture (🤟)
# ══════════════════════════════════════════════════════════════════════════════
MODE_PRESENTATION = "PRESENTATION"
MODE_LAUNCHER     = "LAUNCHER"
current_mode      = MODE_PRESENTATION

# ── Gesture maps per mode ─────────────────────────────────────────────────────
#
#  PRESENTATION MODE gestures:
#    Open_Palm   → Next Slide      (→ arrow)
#    Victory     → Previous Slide  (← arrow)
#    Thumb_Up    → Start Slideshow (Ctrl+Shift+F5 on Windows)
#    Closed_Fist → Exit Slideshow  (Escape)
#    Pointing_Up → Blank Screen    (B key — blacks out slide)
#    ILoveYou    → Switch to LAUNCHER mode
#
#  LAUNCHER MODE gestures:
#    Open_Palm   → Open Chrome
#    Victory     → Open WhatsApp
#    Thumb_Up    → Open VS Code
#    Closed_Fist → Open File Explorer
#    Pointing_Up → Open Notepad
#    ILoveYou    → Switch back to PRESENTATION mode

def switch_mode():
    global current_mode
    current_mode = MODE_LAUNCHER if current_mode == MODE_PRESENTATION else MODE_PRESENTATION
    print(f"Switched to {current_mode} mode")

def start_slideshow():
    """
    Finds either a PowerPoint window or a Google Slides/Chrome window,
    brings it to the foreground, and triggers the correct slideshow shortcut.
    """
    def window_enum_callback(hwnd, wildcard):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            
            # ── Check for Microsoft PowerPoint ────────────────────────────────
            if "PowerPoint" in window_title:
                try:
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    
                    time.sleep(0.5) 
                    
                    pyautogui.press("f5")
                    time.sleep(0.1)
                    pyautogui.press("f5") 
                    
                    print("✓ Switched to PowerPoint and successfully forced slideshow.")
                    return True 
                except Exception as e:
                    print(f"✗ Found PowerPoint but couldn't focus: {e}")

            # ── Check for Google Slides / Chrome ──────────────────────────────
            elif "Google Slides" in window_title or "Chrome" in window_title:
                try:
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.4)
                    
                    pyautogui.hotkey("ctrl", "shift", "F5")
                    print("✓ Switched to Chrome and started Google Slides.")
                    return True
                except Exception as e:
                    print(f"✗ Found Chrome but couldn't focus: {e}")

    win32gui.EnumWindows(window_enum_callback, None)
    
GESTURE_ACTIONS = {
    MODE_PRESENTATION: {
        "Open_Palm":   ("⏭  Next Slide",       lambda: pyautogui.press("right")),
        "Victory":     ("⏮  Prev Slide",        lambda: pyautogui.press("left")),
        "Thumb_Up":    ("▶  Start Slideshow",   start_slideshow),
        "Closed_Fist": ("⏹  Exit Slideshow",    lambda: pyautogui.press("escape")),
        "Pointing_Up": ("⬛ Blank Screen",       lambda: pyautogui.press("b")),
        "ILoveYou":    ("🔀 Switch → LAUNCHER",  switch_mode),
    },
    MODE_LAUNCHER: {
        "Open_Palm":   ("🌐 Open Chrome",        lambda: launch_app("chrome")),
        "Victory":     ("💬 Open WhatsApp",      lambda: launch_app("whatsapp")),
        "Thumb_Up":    ("💻 Open VS Code",       lambda: launch_app("vscode")),
        "Closed_Fist": ("📁 Open Explorer",      lambda: launch_app("explorer")),
        "Pointing_Up": ("📝 Open Notepad",       lambda: launch_app("notepad")),
        "ILoveYou":    ("🔀 Switch → SLIDES",    switch_mode),
    },
}

# ── Stability buffer ───────────────────────────────────────────────────────────
BUFFER_SIZE   = 10
CONFIRM_COUNT = 7  
gesture_buffer = deque(maxlen=BUFFER_SIZE)

# ── Cooldown ───────────────────────────────────────────────────────────────────
COOLDOWN         = 1.8
last_action_time = 0
last_fired_label = ""  

# ── Hand skeleton ──────────────────────────────────────────────────────────────
CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (5,6),(6,7),(7,8),
    (9,10),(10,11),(11,12),
    (13,14),(14,15),(15,16),
    (17,18),(18,19),(19,20),
    (0,5),(5,9),(9,13),(13,17),(0,17),
]

def draw_hand(frame, landmarks, w, h):
    for s, e in CONNECTIONS:
        x1,y1 = int(landmarks[s].x*w), int(landmarks[s].y*h)
        x2,y2 = int(landmarks[e].x*w), int(landmarks[e].y*h)
        cv2.line(frame, (x1,y1),(x2,y2),(0,220,0),2)
    for lm in landmarks:
        cv2.circle(frame,(int(lm.x*w),int(lm.y*h)),4,(0,255,0),-1)

def draw_ui(frame, raw_label, action_label, score, confirmed, mode, buf_count):
    h, w = frame.shape[:2]

    # Top bar
    cv2.rectangle(frame,(0,0),(w,90),(20,20,20),-1)

    # Mode badge
    badge_color = (200,100,0) if mode == MODE_LAUNCHER else (0,130,200)
    cv2.rectangle(frame,(w-180,10),(w-10,40), badge_color,-1)
    cv2.putText(frame, mode, (w-170,32),
                cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),1)

    # Main status
    color  = (0,255,80) if confirmed else (0,180,255)
    text   = action_label if confirmed else (f"Seeing: {raw_label}" if raw_label != "None" else "Waiting for gesture...")
    cv2.putText(frame, text,(20,58),cv2.FONT_HERSHEY_DUPLEX,1.3,color,2)

    # Confidence + stability bar
    if score > 0:
        cv2.putText(frame,f"{score:.0%}",(20,82),
                    cv2.FONT_HERSHEY_SIMPLEX,0.6,(160,160,160),1)
        bar_w = int((buf_count / CONFIRM_COUNT) * 200)
        bar_w = min(bar_w, 200)
        bar_color = (0,255,0) if confirmed else (0,180,255)
        cv2.rectangle(frame,(80,72),(80+bar_w,82),bar_color,-1)
        cv2.rectangle(frame,(80,72),(280,82),(80,80,80),1)

    # Bottom hint bar
    cv2.rectangle(frame,(0,h-35),(w,h),(20,20,20),-1)
    hints = {
        MODE_PRESENTATION: "✋Next  ✌Prev  👍Start  ✊Exit  ☝Blank  🤟SwitchMode",
        MODE_LAUNCHER:     "✋Chrome  ✌WhatsApp  👍VSCode  ✊Explorer  ☝Notepad  🤟SwitchMode",
    }
    cv2.putText(frame, hints[mode],(10,h-12),
                cv2.FONT_HERSHEY_SIMPLEX,0.5,(180,180,180),1)

# ── Webcam ─────────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

print("✅ Gesture Control started. Press Q in the window to quit.")
print(f"   Current mode: {current_mode}")
print("   Show 🤟 (ILoveYou) to switch between PRESENTATION and LAUNCHER mode\n")

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w  = frame.shape[:2]

    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = recognizer.recognize(mp_img)

    raw_label  = "None"
    raw_score  = 0.0
    confirmed  = False
    action_str = "Waiting..."
    buf_count  = 0

    if result.gestures and result.hand_landmarks:
        top = result.gestures[0][0]
        raw_label = top.category_name
        raw_score = top.score

        draw_hand(frame, result.hand_landmarks[0], w, h)
        gesture_buffer.append(raw_label)

        buf_count   = gesture_buffer.count(raw_label)
        action_map  = GESTURE_ACTIONS[current_mode]

        if buf_count >= CONFIRM_COUNT and raw_label in action_map:
            action_str, action_fn = action_map[raw_label]
            confirmed = True
            now = time.time()

            if now - last_action_time > COOLDOWN and raw_label != last_fired_label:
                action_fn()
                last_action_time = now
                last_fired_label = raw_label
        else:
            # Reset so same gesture can re-trigger after hand is lowered
            if gesture_buffer.count("None") >= 3:
                last_fired_label = ""
    else:
        gesture_buffer.append("None")
        if gesture_buffer.count("None") >= 3:
            last_fired_label = ""

    draw_ui(frame, raw_label, action_str, raw_score, confirmed, current_mode, buf_count)
    cv2.imshow("Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()