import tkinter as tk
import threading
import time
import psutil
import win32gui
import win32process
import keyboard

# =========================
# CONFIG
# =========================
running = True
auto_snap = False
# 默认初始值
width_val = 400
height_val = 600

# =========================
# OVERLAY WINDOW
# =========================
overlay = tk.Tk()
overlay.overrideredirect(True)
overlay.attributes("-topmost", True)
overlay.configure(bg="black")
overlay.attributes("-alpha", 0.85)
overlay.geometry(f"{width_val}x{height_val}+1200+0")

tk.Frame(overlay, bg="red", height=3).pack(fill="x")

# =========================
# CORE LOGIC
# =========================
def get_tv_pids():
    pids = set()
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if p.info['name'] and "TradingView" in p.info['name']:
                pids.add(p.info['pid'])
        except: pass
    return pids

def safe_snap():
    tv_pids = get_tv_pids()
    candidates = []
    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd): return
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid not in tv_pids: return
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w, h = right - left, bottom - top
        if w > 500 and h > 400:
            candidates.append((w * h, left, top, right))
    win32gui.EnumWindows(enum_handler, None)
    if not candidates: return
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, left, top, right = candidates[0]
    
    x = right - width_val
    overlay.geometry(f"{width_val}x{height_val}+{x}+{top}")
    overlay.lift()

# =========================
# UI & EVENTS
# =========================
def close_all():
    global running
    running = False
    overlay.destroy()
    panel.destroy()

def start_move(e):
    overlay._x = e.x
    overlay._y = e.y

def move(e):
    global auto_snap
    if auto_snap:
        auto_snap = False
        snap_btn.config(text="Auto Snap: OFF")
    x = overlay.winfo_x() + e.x - overlay._x
    y = overlay.winfo_y() + e.y - overlay._y
    overlay.geometry(f"+{x}+{y}")

overlay.bind("<Button-1>", start_move)
overlay.bind("<B1-Motion>", move)

panel = tk.Toplevel()
panel.title("TV Overlay Controller")
panel.geometry("380x450")
panel.configure(bg="#121212")
panel.attributes("-topmost", True)
panel.protocol("WM_DELETE_WINDOW", close_all)

# 动态获取显示器分辨率
SCREEN_W = panel.winfo_screenwidth()
SCREEN_H = panel.winfo_screenheight()

def label(text): return tk.Label(panel, text=text, fg="#dddddd", bg="#121212")
def button(text, cmd): 
    return tk.Button(panel, text=text, command=cmd, bg="#1f1f1f", fg="white", 
                     relief="flat", activebackground="#333333", padx=10, pady=6)

def update_size(val=None):
    global width_val, height_val
    width_val = int(w_slider.get())
    height_val = int(h_slider.get())
    overlay.geometry(f"{width_val}x{height_val}")

label("TradingView Overlay Controller").pack(pady=10)

label("Width").pack()
w_slider = tk.Scale(panel, from_=100, to=SCREEN_W, orient="horizontal", bg="#121212", fg="white", 
                    highlightthickness=0, command=update_size)
w_slider.set(width_val)
w_slider.pack(fill="x", padx=15)

label("Height").pack()
h_slider = tk.Scale(panel, from_=100, to=SCREEN_H, orient="horizontal", bg="#121212", fg="white", 
                    highlightthickness=0, command=update_size)
h_slider.set(height_val)
h_slider.pack(fill="x", padx=15)

label("Opacity").pack()
tk.Scale(panel, from_=0.2, to=1.0, resolution=0.01, orient="horizontal", bg="#121212", 
         fg="white", highlightthickness=0, command=lambda v: overlay.attributes("-alpha", float(v))).pack(fill="x", padx=15)

def toggle_snap():
    global auto_snap
    auto_snap = not auto_snap
    snap_btn.config(text=f"Auto Snap: {'ON' if auto_snap else 'OFF'}")

snap_btn = button("Auto Snap: OFF", toggle_snap)
snap_btn.pack(pady=8)
button("Exit", close_all).pack(pady=10)

label("Hotkey: F8 to Toggle Visibility").pack(pady=10)
keyboard.add_hotkey('f8', lambda: overlay.withdraw() if overlay.winfo_viewable() else overlay.deiconify())

def snap_loop():
    while running:
        if auto_snap: safe_snap()
        time.sleep(0.3)

threading.Thread(target=snap_loop, daemon=True).start()
panel.mainloop()