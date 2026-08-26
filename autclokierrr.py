import pyautogui
import keyboard
import threading
import time
import json
import os
import tkinter as tk

# Moving the mouse to any screen corner raises FailSafeException, which
# clicker() below treats as an automatic stop signal.
pyautogui.FAILSAFE = True

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autoclicker_settings.json")

DEFAULT_SETTINGS = {
    "interval": "0.1",
    "click_type": "left",
    "always_on_top": False,
    "stop_on_leave": False,
    "dark_mode": False,
    "click_limit_enabled": False,
    "click_limit": "100",
    "time_limit_enabled": False,
    "time_limit": "60",
}

DOT_RED = "#e74c3c"
DOT_GREEN = "#2ecc71"

LIGHT_COLORS = {
    "idle": ("#f8d7da", DOT_RED, "red"),
    "active": ("#d4edda", DOT_GREEN, "green"),
}
DARK_COLORS = {
    "idle": ("#3b1f22", DOT_RED, "#ff9b9b"),
    "active": ("#1f3b28", DOT_GREEN, "#8effc1"),
}
LIGHT_EXTRA = {"entry_bg": "white", "entry_fg": "black", "log_bg": "white", "log_fg": "black", "muted_fg": "gray"}
DARK_EXTRA = {"entry_bg": "#2b2b2b", "entry_fg": "white", "log_bg": "#1e1e1e", "log_fg": "#d4d4d4", "muted_fg": "#aaaaaa"}

# Global state
clicking = False
click_thread = None
click_count = 0
click_interval = 0.1
click_start_time = None
pending_max_clicks = None
pending_max_seconds = None
current_state = "idle"
current_status_text = "Idle"
themed_widgets = []  # filled in after the widgets below are created


def load_settings():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings():
    data = {
        "interval": interval_entry.get(),
        "click_type": click_button.get(),
        "always_on_top": always_on_top.get(),
        "stop_on_leave": stop_on_leave.get(),
        "dark_mode": dark_mode.get(),
        "click_limit_enabled": click_limit_enabled.get(),
        "click_limit": click_limit_entry.get(),
        "time_limit_enabled": time_limit_enabled.get(),
        "time_limit": time_limit_entry.get(),
    }
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


settings = load_settings()


def clicker(interval, button, max_clicks, max_seconds):
    global click_count, clicking
    start = time.time()
    try:
        while clicking:
            pyautogui.click(button=button)
            click_count += 1
            if max_clicks and click_count >= max_clicks:
                clicking = False
                root.after(0, lambda: stop_clicking("Stopped (click limit reached)"))
                break
            if max_seconds and (time.time() - start) >= max_seconds:
                clicking = False
                root.after(0, lambda: stop_clicking("Stopped (time limit reached)"))
                break
            time.sleep(interval)
    except pyautogui.FailSafeException:
        clicking = False
        root.after(0, lambda: stop_clicking("Stopped (mouse hit a screen corner)"))


def start_clicking(event=None):
    global click_interval, pending_max_clicks, pending_max_seconds
    if clicking:
        return
    try:
        click_interval = float(interval_entry.get())
        if click_interval <= 0:
            raise ValueError
    except ValueError:
        set_state("idle", "Enter a valid interval (e.g. 0.1)")
        return

    pending_max_clicks = None
    pending_max_seconds = None
    if click_limit_enabled.get():
        try:
            pending_max_clicks = int(click_limit_entry.get())
            if pending_max_clicks <= 0:
                raise ValueError
        except ValueError:
            set_state("idle", "Enter a valid click limit")
            return
    if time_limit_enabled.get():
        try:
            pending_max_seconds = float(time_limit_entry.get())
            if pending_max_seconds <= 0:
                raise ValueError
        except ValueError:
            set_state("idle", "Enter a valid time limit")
            return

    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    set_controls_state(tk.DISABLED)
    begin_clicking()


def begin_clicking():
    global clicking, click_thread, click_start_time
    clicking = True
    click_start_time = time.time()
    click_thread = threading.Thread(
        target=clicker,
        args=(click_interval, click_button.get(), pending_max_clicks, pending_max_seconds),
        daemon=True,
    )
    click_thread.start()
    set_state("active", "Clicking...")
    log_event("Started")
    update_counter()


def stop_clicking(reason="Stopped"):
    global clicking
    was_active = clicking
    clicking = False
    set_state("idle", reason)
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    set_controls_state(tk.NORMAL)
    if was_active:
        log_event(reason)


def update_counter():
    counter_label.config(text=f"Clicks: {click_count}")
    if click_start_time is not None:
        elapsed = time.time() - click_start_time
        rate = click_count / elapsed if elapsed > 0 else 0.0
        rate_label.config(text=f"{rate:.1f} clicks/sec")
    if clicking:
        root.after(100, update_counter)


def reset_counter():
    global click_count, click_start_time
    click_count = 0
    click_start_time = time.time() if clicking else None
    counter_label.config(text="Clicks: 0")
    rate_label.config(text="0.0 clicks/sec")


def set_controls_state(state):
    left_radio.config(state=state)
    right_radio.config(state=state)
    click_limit_check.config(state=state)
    click_limit_entry.config(state=state)
    time_limit_check.config(state=state)
    time_limit_entry.config(state=state)


def log_event(text):
    timestamp = time.strftime("%H:%M:%S")
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, f"{timestamp}  {text}\n")
    log_text.see(tk.END)
    log_text.config(state=tk.DISABLED)


def set_state(mode, text):
    """Update the status text, the small indicator dot, and the whole app's background together."""
    global current_state, current_status_text
    current_state = mode
    current_status_text = text
    palette = DARK_COLORS if dark_mode.get() else LIGHT_COLORS
    bg, dot_color, text_color = palette[mode]

    root.config(bg=bg)
    for widget in themed_widgets:
        widget.config(bg=bg)
    indicator.config(bg=bg)
    indicator.itemconfig(indicator_dot, fill=dot_color)
    status_label.config(text=text, fg=text_color, bg=bg)


def apply_extra_theme():
    extra = DARK_EXTRA if dark_mode.get() else LIGHT_EXTRA
    for entry in (interval_entry, click_limit_entry, time_limit_entry):
        entry.config(bg=extra["entry_bg"], fg=extra["entry_fg"], insertbackground=extra["entry_fg"])
    log_text.config(bg=extra["log_bg"], fg=extra["log_fg"])
    rate_label.config(fg=extra["muted_fg"])
    esc_note_label.config(fg=extra["muted_fg"])
    set_state(current_state, current_status_text)


def toggle_always_on_top():
    root.attributes("-topmost", always_on_top.get())


def on_window_leave(event):
    if stop_on_leave.get() and clicking:
        stop_clicking("Stopped (mouse left the window)")


def on_close():
    stop_clicking()
    save_settings()
    try:
        keyboard.unhook_all()
    except Exception:
        pass
    root.destroy()


# Build the GUI
root = tk.Tk()
root.title("Autoclicker")
root.geometry("300x580")
root.resizable(True, True)
root.minsize(300, 480)
root.protocol("WM_DELETE_WINDOW", on_close)
root.bind("<Leave>", on_window_leave)

interval_label = tk.Label(root, text="Click interval (seconds):")
interval_label.pack(pady=(10, 0))
interval_entry = tk.Entry(root, justify="center")
interval_entry.insert(0, settings["interval"])
interval_entry.bind("<Return>", start_clicking)
interval_entry.pack(pady=5)

click_button = tk.StringVar(value=settings["click_type"])
click_type_frame = tk.Frame(root)
click_type_frame.pack(pady=(0, 8))
left_radio = tk.Radiobutton(click_type_frame, text="Left click", variable=click_button, value="left")
left_radio.pack(side=tk.LEFT, padx=5)
right_radio = tk.Radiobutton(click_type_frame, text="Right click", variable=click_button, value="right")
right_radio.pack(side=tk.LEFT, padx=5)

click_limit_enabled = tk.BooleanVar(value=settings["click_limit_enabled"])
click_limit_frame = tk.Frame(root)
click_limit_frame.pack(pady=2)
click_limit_check = tk.Checkbutton(click_limit_frame, text="Stop after", variable=click_limit_enabled)
click_limit_check.pack(side=tk.LEFT)
click_limit_entry = tk.Entry(click_limit_frame, width=6, justify="center")
click_limit_entry.insert(0, settings["click_limit"])
click_limit_entry.pack(side=tk.LEFT, padx=4)
click_limit_unit_label = tk.Label(click_limit_frame, text="clicks")
click_limit_unit_label.pack(side=tk.LEFT)

time_limit_enabled = tk.BooleanVar(value=settings["time_limit_enabled"])
time_limit_frame = tk.Frame(root)
time_limit_frame.pack(pady=2)
time_limit_check = tk.Checkbutton(time_limit_frame, text="Stop after", variable=time_limit_enabled)
time_limit_check.pack(side=tk.LEFT)
time_limit_entry = tk.Entry(time_limit_frame, width=6, justify="center")
time_limit_entry.insert(0, settings["time_limit"])
time_limit_entry.pack(side=tk.LEFT, padx=4)
time_limit_unit_label = tk.Label(time_limit_frame, text="seconds")
time_limit_unit_label.pack(side=tk.LEFT)

always_on_top = tk.BooleanVar(value=settings["always_on_top"])
always_on_top_check = tk.Checkbutton(
    root, text="Keep window on top", variable=always_on_top, command=toggle_always_on_top
)
always_on_top_check.pack(pady=(6, 2))

stop_on_leave = tk.BooleanVar(value=settings["stop_on_leave"])
stop_on_leave_check = tk.Checkbutton(root, text="Stop if mouse leaves window", variable=stop_on_leave)
stop_on_leave_check.pack(pady=2)

dark_mode = tk.BooleanVar(value=settings["dark_mode"])
dark_mode_check = tk.Checkbutton(root, text="Dark mode", variable=dark_mode, command=lambda: apply_extra_theme())
dark_mode_check.pack(pady=(2, 8))

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

start_button = tk.Button(button_frame, text="Start", width=10, command=start_clicking)
start_button.grid(row=0, column=0, padx=5)

stop_button = tk.Button(button_frame, text="Stop", width=10, command=stop_clicking, state=tk.DISABLED)
stop_button.grid(row=0, column=1, padx=5)

counter_label = tk.Label(root, text="Clicks: 0", font=("Segoe UI", 12, "bold"))
counter_label.pack(pady=(10, 0))

rate_label = tk.Label(root, text="0.0 clicks/sec", font=("Segoe UI", 9), fg="gray")
rate_label.pack(pady=(0, 8))

reset_button = tk.Button(root, text="Reset counter", command=reset_counter)
reset_button.pack()

status_frame = tk.Frame(root)
status_frame.pack(pady=(8, 0))

indicator = tk.Canvas(status_frame, width=14, height=14, highlightthickness=0)
indicator_dot = indicator.create_oval(2, 2, 12, 12, fill=DOT_RED, outline="")
indicator.pack(side=tk.LEFT, padx=(0, 6))

status_label = tk.Label(status_frame, text="Idle", fg="red")
status_label.pack(side=tk.LEFT)

esc_note_label = tk.Label(root, text="Press ESC anytime to stop", fg="gray", font=("Segoe UI", 8))
esc_note_label.pack(pady=(6, 8))

log_frame = tk.Frame(root)
log_frame.pack(pady=(0, 10), padx=10, fill="both", expand=True)

log_label = tk.Label(log_frame, text="Session log:")
log_label.pack(anchor="w")

log_text_frame = tk.Frame(log_frame)
log_text_frame.pack(fill="both", expand=True)

log_scrollbar = tk.Scrollbar(log_text_frame)
log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

log_text = tk.Text(
    log_text_frame, height=7, width=32, font=("Consolas", 8),
    yscrollcommand=log_scrollbar.set, state=tk.DISABLED, wrap="word", borderwidth=1
)
log_text.pack(side=tk.LEFT, fill="both", expand=True)
log_scrollbar.config(command=log_text.yview)

themed_widgets = [
    interval_label,
    click_type_frame,
    left_radio,
    right_radio,
    click_limit_frame,
    click_limit_check,
    click_limit_unit_label,
    time_limit_frame,
    time_limit_check,
    time_limit_unit_label,
    always_on_top_check,
    stop_on_leave_check,
    dark_mode_check,
    button_frame,
    counter_label,
    rate_label,
    status_frame,
    esc_note_label,
    log_frame,
    log_label,
    log_text_frame,
]

toggle_always_on_top()
set_state("idle", "Idle")
apply_extra_theme()

# Global ESC hotkey, works even when this window does not have focus.
# On Windows this may require running the terminal as Administrator.
try:
    keyboard.add_hotkey("esc", lambda: root.after(0, lambda: stop_clicking("Stopped (Esc pressed)")))
except Exception:
    pass

root.mainloop()