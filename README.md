========================================================================
INTELLIGENT GESTURE CONTROL SYSTEM (PRESENTATION & APP LAUNCHER)
========================================================================

1. WHAT THIS PROJECT DOES
-------------------------
This is a Python application that lets you control your computer entirely hands-free 
using a webcam. It uses machine learning to look at your hand signs and translates 
them into actual keyboard shortcuts and actions on your system.

It features two main modes that you can toggle between using the "YO" sign (🤟):
*   Presentation Mode: Run slide decks on both Microsoft PowerPoint and Google Chrome 
    without touching your mouse or keyboard.
*   Launcher Mode: Instantly open your everyday apps (Chrome, VS Code, WhatsApp, Notepad, 
    and File Explorer) with quick hand gestures.


2. GESTURE MAPPING BREAKDOWN
----------------------------
To prevent random background movements from accidentally skipping slides or opening apps, 
the script uses a built-in confirmation filter. You have to hold the gesture clearly 
for a split second for it to trigger.

[PRESENTATION MODE]
*   Open Palm (✋)   --> Next Slide (Right Arrow)
*   Victory (✌)     --> Previous Slide (Left Arrow)
*   Thumb Up (👍)    --> Start Slideshow (Brings the app to the front and runs it)
*   Closed Fist (✊)  --> Exit Slideshow (Escape)
*   Pointing Up (☝)  --> Blackout Screen (B Key)
*   Yo (🤟)    --> Switch to LAUNCHER Mode

[LAUNCHER MODE]
*   Open Palm (✋)   --> Open Google Chrome
*   Victory (✌)     --> Open WhatsApp
*   Thumb Up (👍)    --> Open Visual Studio Code
*   Closed Fist (✊)  --> Open File Explorer
*   Pointing Up (☝)  --> Open Notepad
*   Yo (🤟)    --> Switch back to PRESENTATION Mode


3. THE TECH STACK
-----------------
*   Python 3 (Core language)
*   OpenCV: Handles the live webcam feed, flips the image so it acts like a mirror, 
    and draws the custom UI overlay.
*   MediaPipe: Google's vision framework used to detect the hand and read the gesture.
*   PyAutoGUI: Controls the keyboard strokes and hotkeys behind the scenes.
*   pywin32 (Win32gui/Win32con): Directly talks to Windows to find running apps and 
    bring them to the front.


4. REAL CHALLENGES FIXED IN THE CODE
------------------------------------
*   Flickering & Ghost Inputs: Raw machine learning data can be shaky. I added a rolling 
    buffer that requires a gesture to be visible in 7 out of the last 10 frames before 
    it registers. This completely stops accidental misfires.
*   Accidental Spamming: To stop a single gesture from skipping 5 slides at once, I built 
    in a 1.8-second cooldown. You have to lower your hand or change the shape before the 
    same command can trigger again.
*   Window Focus Issues: PyAutoGUI shortcuts only work if the app is active on your screen. 
    I updated the code to automatically scan your desktop for PowerPoint or Chrome, pull 
    it out of the taskbar if it's minimized, force it into the foreground, and then send 
    the keys.
*   PowerPoint Startup Lag: PowerPoint occasionally missed the startup key while rendering 
    the full-screen window switch. I fixed this by adding a tiny 0.5-second buffer delay 
    and a double-tap shortcut command to ensure it launches perfectly on the first try.


5. FUTURE IMPROVEMENTS
------------------------------------
* Swipe gesture recognition
* Gesture-based laser pointer
* Volume control
* Zoom gestures
* Multi-hand support


6. ⚠️ Note
------------------------------------
* Ensure good lighting conditions
* Keep hand visible to webcam
* Avoid cluttered backgrounds for better detection
* Works best at moderate camera distance

========================================================================
