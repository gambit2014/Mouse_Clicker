import pyautogui
import keyboard
import threading
import time

# Set the interval (in seconds) between clicks
click_interval = 0.1

# A flag to control the clicking loop
clicking = False

# Function to perform the clicking
def clicker():
    while clicking:
        pyautogui.click()
        time.sleep(click_interval)

# Function to start the autoclicker
def start_clicking():
    global clicking
    clicking = True
    click_thread = threading.Thread(target=clicker)
    click_thread.start()

# Function to stop the autoclicker
def stop_clicking():
    global clicking
    clicking = False

# Set up key listeners
keyboard.add_hotkey('s', start_clicking)
keyboard.add_hotkey('q', stop_clicking)

# Keep the script running
print("Press 's' to start clicking and 'q' to stop clicking.")
keyboard.wait('esc')
